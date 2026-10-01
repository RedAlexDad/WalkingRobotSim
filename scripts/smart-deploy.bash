#!/bin/bash
# Smart deploy: пересобирает Docker образы при изменениях в исходниках
#
# Правила:
#   src/*                  → rebuild main image
#   elevation_mapping_cupy/* → rebuild elevation image
#   compose.yml Dockerfile → rebuild main image
#
# Использование:
#   ./scripts/smart-deploy.bash          # check + build if needed + up
#   ./scripts/smart-deploy.bash --build  # force rebuild
#   ./scripts/smart-deploy.bash --check  # only print what's needed, no actions

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# DRM-узлы встроенной AMD для проброса через compose.gpu.yml — если не заданы
# Makefile (номера cardN/renderDN меняются при подключении/отключении eGPU).
if [ -z "${WRS_DRI_CARD:-}" ]; then
    WRS_DRI_CARD="$(bash "$PROJECT_ROOT/scripts/detect-gpu.sh" card 2>/dev/null || true)"
    WRS_DRI_RENDER="$(bash "$PROJECT_ROOT/scripts/detect-gpu.sh" render 2>/dev/null || true)"
    export WRS_DRI_CARD WRS_DRI_RENDER
fi

# Режим GPU: nvidia | amd | none. Приоритет — WRS_GPU_EFF (из Makefile),
# иначе WRS_GPU, иначе auto (nvidia если доступна, затем amd, затем none).
GPU_MODE="${WRS_GPU_EFF:-${WRS_GPU:-auto}}"
if [ "$GPU_MODE" = "auto" ]; then
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
        GPU_MODE="nvidia"
    elif [ -n "${WRS_DRI_RENDER:-}" ] && [ -e "${WRS_DRI_RENDER:-}" ]; then
        GPU_MODE="amd"
    else
        GPU_MODE="none"
    fi
fi

LAST_BUILD_FILE=".last_build_commit"
CONTAINER_NAME="walking_robot_sim"

# Защита: docker установлен и демон запущен.
command -v docker >/dev/null 2>&1 || { echo "docker не установлен"; exit 1; }
docker info >/dev/null 2>&1 || { echo "демон docker не запущен"; exit 1; }

# GPU-override: nvidia → compose.nvidia.yml; amd → compose.gpu.yml (если iGPU есть).
COMPOSE=(docker compose -f "$PROJECT_ROOT/compose.yml")
case "$GPU_MODE" in
    nvidia) COMPOSE+=(-f "$PROJECT_ROOT/compose.nvidia.yml") ;;
    amd)    if [ -n "${WRS_DRI_RENDER:-}" ] && [ -e "${WRS_DRI_RENDER:-}" ]; then
                COMPOSE+=(-f "$PROJECT_ROOT/compose.gpu.yml")
            fi ;;
esac

# ── helpers ──────────────────────────────────────────────
red()    { printf "\033[0;31m%s\033[0m\n" "$*"; }
green()  { printf "\033[0;32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[1;33m%s\033[0m\n" "$*"; }
cyan()   { printf "\033[0;36m%s\033[0m\n" "$*"; }
bold()   { printf "\033[1m%s\033[0m" "$*"; }

# ── classify changes ─────────────────────────────────────
REBUILD_MAIN=false
REBUILD_ELEVATION=false
CHANGED_FILES=""

collect_changes() {
    UNSTAGED=$(git diff --name-only 2>/dev/null || true)
    STAGED=$(git diff --cached --name-only 2>/dev/null || true)

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

    UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)

    for file in $CHANGED_FILES $UNTRACKED; do
        [ -z "$file" ] && continue
        case "$file" in
            src/*)
                REBUILD_MAIN=true
                yellow "  [src] $file → rebuild main image"
                ;;
            elevation_mapping_cupy/*)
                REBUILD_ELEVATION=true
                yellow "  [elevation] $file → rebuild elevation image"
                ;;
            compose.yml|docker-compose*)
                REBUILD_MAIN=true
                yellow "  [compose] $file → rebuild needed"
                ;;
            .last_build_commit|reports/*|summary.md|data/*|logs/*)
                cyan "  [skip] $file — docs/data"
                ;;
            scripts/*|.gitignore|Makefile|makefiles/*|README.md)
                cyan "  [skip] $file — infra/docs"
                ;;
            *)
                cyan "  [skip] $file — не влияет на сборку"
                ;;
        esac
    done
}

do_build_main() {
    if [ "$REBUILD_MAIN" = true ]; then
        green "→ Building main image..."
        "${COMPOSE[@]}" build
        git rev-parse HEAD > "$LAST_BUILD_FILE" 2>/dev/null || true
    else
        cyan "→ No changes requiring main rebuild, skipping build"
    fi
}

do_build_elevation() {
    if [ "$REBUILD_ELEVATION" = true ]; then
        green "→ Building elevation_mapping image..."
        "${COMPOSE[@]}" build elevation_mapping
    else
        cyan "→ No elevation changes, skipping elevation build"
    fi
}

do_up() {
    if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
        cyan "→ Removing old container..."
        docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
        sleep 1
    fi

    cyan "→ Starting container..."
    "${COMPOSE[@]}" up -d 2>&1

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
    green "✓ Container running"
}

do_status() {
    echo ""
    if [ "$REBUILD_MAIN" = false ] && [ "$REBUILD_ELEVATION" = false ]; then
        green "→ No rebuild needed, starting container..."
    else
        echo "────────────────────────────────────────────"
        [ "$REBUILD_MAIN" = true ]       && echo " • Main image:     REBUILD"
        [ "$REBUILD_MAIN" = false ]      && echo " • Main image:     skip"
        [ "$REBUILD_ELEVATION" = true ]  && echo " • Elevation:      REBUILD"
        [ "$REBUILD_ELEVATION" = false ] && echo " • Elevation:      skip"
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
        do_status
        do_build_main
        do_build_elevation
        do_up
        ;;
    auto|*)
        do_status
        do_build_main
        do_build_elevation
        do_up
        ;;
esac
