#!/bin/bash
# Smart deploy: определяет нужна ли пересборка Docker по изменениям в git
#
# Правила:
#   src/*.cpp .hpp .h CMakeLists.txt pkg.xml  → rebuild main image (Docker)
#   src/*.py .yaml .launch.py .rviz            → colcon build --symlink-install внутри контейнера
#   elevation_mapping_cupy/*                   → rebuild elevation image
#   compose.yml Dockerfile                     → rebuild main image
#
# Использование:
#   ./scripts/smart-deploy.sh          # check + build if needed + up
#   ./scripts/smart-deploy.sh --build  # force rebuild
#   ./scripts/smart-deploy.sh --check  # only print what's needed, no actions

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

LAST_BUILD_FILE=".last_build_commit"
COMPOSE="docker compose -f ${PROJECT_ROOT}/compose.yml"
CONTAINER_NAME="walking_robot_sim"

# ── helpers ──────────────────────────────────────────────
red()    { printf "\033[0;31m%s\033[0m\n" "$*"; }
green()  { printf "\033[0;32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[1;33m%s\033[0m\n" "$*"; }
cyan()   { printf "\033[0;36m%s\033[0m\n" "$*"; }
bold()   { printf "\033[1m%s\033[0m" "$*"; }

# ── classify changes ─────────────────────────────────────
REBUILD_MAIN=false
REBUILD_ELEVATION=false
REBUILD_WS_PACKAGES=()  # array of packages needing colcon build inside container
CHANGED_FILES=""
UNSTAGED_FILES=""

collect_changes() {
    # Staged + unstaged tracked files
    UNSTAGED=$(git diff --name-only 2>/dev/null || true)
    STAGED=$(git diff --cached --name-only 2>/dev/null || true)

    # Committed changes since last build
    if [ -f "$LAST_BUILD_FILE" ]; then
        LAST_HASH=$(cat "$LAST_BUILD_FILE")
        if git cat-file -e "$LAST_HASH" 2>/dev/null; then
            COMMITTED=$(git diff --name-only "$LAST_HASH" HEAD 2>/dev/null || true)
        else
            COMMITTED=""
        fi
    else
        COMMITTED=""
    fi

    CHANGED_FILES=$(echo -e "${UNSTAGED}\n${STAGED}\n${COMMITTED}" | sort -u | grep -v '^$' || true)

    if [ -z "$CHANGED_FILES" ]; then
        return
    fi

    # New untracked files
    UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)

    for file in $CHANGED_FILES $UNTRACKED; do
        [ -z "$file" ] && continue
        case "$file" in
            src/*.cpp|src/*.hpp|src/*.h|src/*/CMakeLists.txt|src/*/package.xml|src/*/*.cfg)
                REBUILD_MAIN=true
                yellow "  [C++] $file → rebuild needed"
                ;;
            src/*.py|src/*.yaml|src/*.yml|src/*.launch.py|src/*.rviz)
                # Extract package name (src/<pkg>/...)
                pkg=$(echo "$file" | cut -d/ -f2)
                # Validate it's a real package dir
                if [ -d "src/$pkg" ]; then
                    REBUILD_WS_PACKAGES+=("$pkg")
                    cyan "  [py] $file → queue colcon build $pkg"
                fi
                ;;
            src/*.mk|src/*.md|src/*.txt)
                # Infra/docs — no action
                cyan "  [skip] $file — infra/docs, no rebuild"
                ;;
            elevation_mapping_cupy/*)
                REBUILD_ELEVATION=true
                yellow "  [elevation] $file → rebuild elevation image"
                ;;
            compose.yml|docker-compose*)
                REBUILD_MAIN=true
                yellow "  [compose] $file → rebuild needed"
                ;;
            src/docker/Dockerfile|src/docker/*)
                REBUILD_MAIN=true
                yellow "  [docker] $file → rebuild needed"
                ;;
            scripts/*.sh|.gitignore|Makefile|makefiles/*)
                cyan "  [skip] $file — infra, no rebuild"
                ;;
            .last_build_commit|reports/*|summary.md|data/*|logs/*)
                cyan "  [skip] $file — docs/data, no rebuild"
                ;;
            *)
                # Unknown file — conservative: trigger rebuild
                REBUILD_MAIN=true
                yellow "  [?] $file → unknown type, rebuild (conservative)"
                ;;
        esac
    done
}

# Deduplicate array while preserving order
dedupe() {
    local -n arr=$1
    local -A seen=()
    local result=()
    for item in "${arr[@]}"; do
        if [[ -z "${seen[$item]-}" ]]; then
            seen[$item]=1
            result+=("$item")
        fi
    done
    arr=("${result[@]}")
}

do_build_main() {
    if [ "$REBUILD_MAIN" = true ]; then
        green "→ Building main image..."
        $COMPOSE build
        git rev-parse HEAD > "$LAST_BUILD_FILE" 2>/dev/null || true
        # Full Docker build installs everything — no extra ws build needed
        REBUILD_WS_PACKAGES=()
    else
        cyan "→ No changes requiring main rebuild, skipping build"
    fi
}

do_build_elevation() {
    if [ "$REBUILD_ELEVATION" = true ]; then
        green "→ Building elevation_mapping image..."
        $COMPOSE build elevation_mapping
    else
        cyan "→ No elevation changes, skipping elevation build"
    fi
}

do_workspace_build() {
    dedupe REBUILD_WS_PACKAGES
    if [ ${#REBUILD_WS_PACKAGES[@]} -eq 0 ]; then
        return
    fi

    green "→ Rebuilding workspace packages inside container..."
    pkgs_str=$(IFS=' '; echo "${REBUILD_WS_PACKAGES[*]}")

    if docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME" 2>/dev/null; then
        docker exec "$CONTAINER_NAME" bash -c "
            source /opt/ros/jazzy/setup.bash
            cd /root/ws
            colcon build --packages-select $pkgs_str --symlink-install
        " && green "✓ Workspace rebuild complete ($pkgs_str)"
    else
        yellow "! Container not running, skipping workspace build"
    fi
}

do_up() {
    # Remove old container if exists
    if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
        cyan "→ Removing old container..."
        docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
        sleep 1
    fi

    cyan "→ Starting container..."
    $COMPOSE up -d 2>&1

    # Wait for ROS
    cyan "→ Waiting for ROS..."
    attempt=0
    while [ $attempt -lt 30 ]; do
        if docker exec "$CONTAINER_NAME" bash -c "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 node list" >/dev/null 2>&1; then
            green "✓ ROS ready (${attempt}s)"
            break
        fi
        attempt=$((attempt + 1))
        printf "."
        sleep 1
    done
    echo ""

    # Rebuild workspace if needed (only after container is up)
    do_workspace_build

    green "✓ Container running"
}

do_status() {
    echo ""
    dedupe REBUILD_WS_PACKAGES

    if [ "$REBUILD_MAIN" = false ] && [ "$REBUILD_ELEVATION" = false ] && [ ${#REBUILD_WS_PACKAGES[@]} -eq 0 ]; then
        green "→ No rebuild needed, starting container..."
    else
        echo "────────────────────────────────────────────"
        [ "$REBUILD_MAIN" = true ]              && echo " • Main image:           REBUILD"
        [ "$REBUILD_MAIN" = false ]             && echo " • Main image:           skip"
        [ "$REBUILD_ELEVATION" = true ]         && echo " • Elevation:            REBUILD"
        [ "$REBUILD_ELEVATION" = false ]        && echo " • Elevation:            skip"
        if [ ${#REBUILD_WS_PACKAGES[@]} -gt 0 ]; then
            local pkgs_str
            pkgs_str=$(IFS=' '; echo "${REBUILD_WS_PACKAGES[*]}")
            echo " • Workspace packages:   colcon build $pkgs_str"
        fi
        echo "────────────────────────────────────────────"
    fi
}

# ── main ─────────────────────────────────────────────────

MODE="${1:-auto}"

echo ""
bold "Walking Robot Simulator — Smart Deploy"
echo ""

collect_changes

if [ -z "$CHANGED_FILES" ] && [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
    cyan "→ No changes detected since last build"
fi

echo ""

case "$MODE" in
    --check)
        do_status
        exit 0
        ;;
    --build)
        REBUILD_MAIN=true
        REBUILD_ELEVATION=true
        REBUILD_WS_PACKAGES=()
        do_status
        do_build_main
        do_build_elevation
        do_up
        ;;
    --main)
        REBUILD_MAIN=true
        REBUILD_WS_PACKAGES=()
        do_status
        do_build_main
        do_up
        ;;
    auto|*)
        do_status
        do_build_main
        do_build_elevation
        do_up
        ;;
esac
