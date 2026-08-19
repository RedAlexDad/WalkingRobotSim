#!/bin/bash
# Smart elevation build: пересобирает образ только при изменениях в elevation_mapping_cupy/
#
# Использование:
#   ./scripts/smart-elevation.bash          # check + build if needed
#   ./scripts/smart-elevation.bash --build  # force rebuild
#   ./scripts/smart-elevation.bash --check  # dry-run

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

LAST_BUILD_FILE=".last_elevation_build_commit"
COMPOSE="docker compose -f ${PROJECT_ROOT}/compose.yml"

red()    { printf "\033[0;31m%s\033[0m\n" "$*"; }
green()  { printf "\033[0;32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[1;33m%s\033[0m\n" "$*"; }
cyan()   { printf "\033[0;36m%s\033[0m\n" "$*"; }
bold()   { printf "\033[1m%s\033[0m" "$*"; }

NEED_REBUILD=false
CHANGED_FILES=""

collect_changes() {
    UNSTAGED=$(git diff --name-only -- elevation_mapping_cupy/ 2>/dev/null || true)
    STAGED=$(git diff --cached --name-only -- elevation_mapping_cupy/ 2>/dev/null || true)

    if [ -f "$LAST_BUILD_FILE" ]; then
        LAST_HASH=$(cat "$LAST_BUILD_FILE")
        if git cat-file -e "$LAST_HASH" 2>/dev/null; then
            COMMITTED=$(git diff --name-only "$LAST_HASH" HEAD -- elevation_mapping_cupy/ 2>/dev/null || true)
        else
            COMMITTED=""
        fi
    else
        COMMITTED=""
    fi

    CHANGED_FILES=$(echo -e "${UNSTAGED}\n${STAGED}\n${COMMITTED}" | sort -u | grep -v '^$' || true)

    if [ -n "$CHANGED_FILES" ]; then
        NEED_REBUILD=true
    fi

    UNTRACKED=$(git ls-files --others --exclude-standard -- elevation_mapping_cupy/ 2>/dev/null || true)
    if [ -n "$UNTRACKED" ]; then
        NEED_REBUILD=true
        CHANGED_FILES="${CHANGED_FILES}${UNTRACKED}"
    fi
}

do_build() {
    green "→ Building elevation_mapping image..."
    $COMPOSE build elevation_mapping
    git rev-parse HEAD > "$LAST_BUILD_FILE" 2>/dev/null || true
    green "✓ Образ elevation_mapping собран"
}

do_check() {
    if [ "$NEED_REBUILD" = true ]; then
        yellow "→ Изменения в elevation_mapping_cupy/ — требуется пересборка"
    else
        green "→ В elevation_mapping_cupy/ нет изменений, сборка не нужна"
    fi
}

# ── main ─────────────────────────────────────────────────

MODE="${1:-auto}"

echo ""
bold "Elevation Mapping — Smart Build"
echo ""

collect_changes

case "$MODE" in
    --check)
        do_check
        exit 0
        ;;
    --build)
        NEED_REBUILD=true
        do_check
        do_build
        ;;
    auto|*)
        if [ "$NEED_REBUILD" = true ]; then
            for f in $CHANGED_FILES; do
                cyan "  $f"
            done
            do_build
        else
            green "→ Нет изменений, сборка не требуется"
        fi
        ;;
esac
