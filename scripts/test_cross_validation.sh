#!/bin/bash
# test_cross_validation.sh — все Rust-тесты проекта одной командой.
#
# Golden-данные C++-эталона завендорены в
#   src/quadropted_controller_rust/quadropted-core/tests/golden/mod.rs
# поэтому C++-пакет, его харнесс и сеть для прогона не нужны.
#
# Usage:
#   ./scripts/test_cross_validation.sh          # в контейнере walking_robot_sim
#   ./scripts/test_cross_validation.sh --host   # локально (нужен cargo + ROS)
#
# Код возврата: 0 — все тесты прошли; non-zero — есть провалы, ошибка сборки
# или не выполнилось ни одного теста (ноль тестов — это не «всё зелёное»).

set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-walking_robot_sim}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUST_DIR="$PROJECT_DIR/src/quadropted_controller_rust"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

info()   { echo -e "${BLUE}[INFO]${NC} $1"; }
header() { echo -e "\n${BOLD}═══════════════════════════════════════════════════${NC}"; echo -e "${BOLD} $1${NC}"; echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"; }

USE_HOST=0
for arg in "$@"; do
    case "$arg" in
        --host) USE_HOST=1 ;;
        -h|--help)
            sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Неизвестный аргумент: $arg" >&2
            exit 2
            ;;
    esac
done

if [ ! -f "$RUST_DIR/quadropted-core/tests/golden/mod.rs" ]; then
    echo -e "${RED}[FAIL]${NC} Нет golden-данных: $RUST_DIR/quadropted-core/tests/golden/mod.rs" >&2
    exit 1
fi

header "Rust-тесты: unit + golden cross-validation + интеграционные"

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

STATUS=0
if [ "$USE_HOST" -eq 1 ]; then
    info "Запуск: cargo test --workspace (хост)"
    (cd "$RUST_DIR" && cargo test --workspace) >"$LOG" 2>&1 || STATUS=$?
else
    info "Запуск: cargo test --workspace (контейнер $CONTAINER_NAME)"
    docker exec "$CONTAINER_NAME" bash -lc \
        "source /opt/ros/$ROS_DISTRO/setup.bash; \
         source /root/ws/install/setup.bash 2>/dev/null; \
         cd /root/ws/src/quadropted_controller_rust && cargo test --workspace" \
        >"$LOG" 2>&1 || STATUS=$?
fi

# Полный лог — чтобы при провале был виден виновный тест.
cat "$LOG"

PASSED=$(grep -E "^test result:" "$LOG" | sed -E 's/.* ([0-9]+) passed.*/\1/' | awk '{s+=$1} END {print s+0}')
FAILED=$(grep -E "^test result:" "$LOG" | sed -E 's/.* ([0-9]+) failed.*/\1/' | awk '{s+=$1} END {print s+0}')

header "Сводка по наборам тестов"
printf "%-62s %s\n" "Набор" "Результат"
printf "%-62s %s\n" "─────────────────────────────────────────────────────────────" "─────────────"
awk '
    /^ *Running / {
        suite = $0
        sub(/^ *Running /, "", suite)
        sub(/ \(.*/, "", suite)
    }
    /^test result:/ {
        result = $0
        sub(/^test result: /, "", result)
        sub(/;.*/, "", result)
        if (suite != "") printf "%-62s %s\n", suite, result
        suite = ""
    }
' "$LOG"

echo ""
if [ "$STATUS" -ne 0 ] || [ "$FAILED" -ne 0 ] || [ "$PASSED" -eq 0 ]; then
    echo -e "${RED}${BOLD}[FAIL]${NC} exit=$STATUS, passed=$PASSED, failed=$FAILED — тест-гейт красный"
    exit 1
fi

echo -e "${GREEN}${BOLD}[PASS]${NC} $PASSED passed, $FAILED failed"
echo ""
echo "Golden cross-validation (21 тест): математика < 1e-12, FK/контроллеры"
echo "< 1e-9, IK < 2e-3 (fast_atan2 в C++-эталоне), phase_index/contacts — точно."
echo "Эталон: quadropted-core/tests/golden/mod.rs, допуски: tests/cross_validation.rs."
exit 0
