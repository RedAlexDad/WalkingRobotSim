#!/bin/bash
# run_rust_bridge.sh — запуск isaac_rust_bridge.py (Rust-контроллер → Isaac,
# ассет NVIDIA) с корректным ROS2-окружением.
#
# Проблема: host-ROS (Lyrical, py3.14) в PYTHONPATH конфликтует со
# встроенным rclpy Isaac Sim (Jazzy, py3.12). Без правильного PYTHONPATH
# geometry_msgs/rosidl_typesupport_c импортируются из Lyrical и падает
# UnsupportedTypeSupport. PYTHONPATH и AMENT_PREFIX_PATH должны указывать
# на jazzy/rclpy Isaac Sim ДО старта python.
#
# Использование:
#   source ~/isaacsim-venv/bin/activate
#   bash src/isaac/run_rust_bridge.sh [--headless] [--ns /robot1] [--min-ram 12]
#
# Защита: проверяет доступную RAM (по умолчанию >= 12 GB) перед запуском.

set -euo pipefail
export LC_ALL=C

ts() {
    local ns
    ns=$(date +%H:%M:%S.%N)
    echo "${ns%??????}"
}
log() {
    echo "[$(ts)] [run_rust_bridge] $*"
}

MIN_RAM_GB=12
for arg in "$@"; do
    case "${arg}" in
        --min-ram=*) MIN_RAM_GB="${arg#*=}" ;;
    esac
done

available_mem_gb() {
    local kb
    if [ -r /proc/meminfo ]; then
        kb=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
        if [ -n "${kb}" ]; then
            awk -v k="${kb}" 'BEGIN { printf "%.1f", k / (1024*1024) }'
            return 0
        fi
    fi
    echo "inf"
    return 0
}

RAM_GB=$(available_mem_gb)
log "доступно RAM: ${RAM_GB} GB (нужно >= ${MIN_RAM_GB} GB)"
if [ "${RAM_GB}" != "inf" ]; then
    if awk -v r="${RAM_GB}" -v m="${MIN_RAM_GB}" 'BEGIN { exit !(r < m) }'; then
        log "ERROR: памяти недостаточно (${RAM_GB} GB < ${MIN_RAM_GB} GB)." >&2
        log "Закройте GUI-приложения и контейнеры (docker stop elevation_mapping walking_robot_sim)." >&2
        exit 1
    fi
fi

ISAAC_VENV="${HOME}/isaacsim-venv"
ISAAC_JAZZY="${ISAAC_VENV}/lib/python3.12/site-packages/isaacsim/exts/isaacsim.ros2.core/jazzy"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE="${SCRIPT_DIR}/isaac_rust_bridge.py"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ ! -d "${ISAAC_JAZZY}/rclpy" ]; then
    log "ERROR: не найден rclpy Isaac Sim: ${ISAAC_JAZZY}/rclpy" >&2
    exit 1
fi
log "rclpy Isaac: OK (${ISAAC_JAZZY}/rclpy)"

QUADROPTED_MSGS_PY="${PROJECT_ROOT}/install/quadropted_msgs/lib/python3.12/site-packages"
if [ -d "${QUADROPTED_MSGS_PY}/quadropted_msgs" ]; then
    log "quadropted_msgs: OK (${QUADROPTED_MSGS_PY})"
else
    log "WARN: quadropted_msgs не найден — foot_contact будет отключён"
fi

# Ассет NVIDIA Go2 (в проекте)
GO2_USD="${PROJECT_ROOT}/src/isaac/assets/Isaac/Samples/Mujoco_Menagerie/unitree_go2/go2/go2.usda"
if [ -f "${GO2_USD}" ]; then
    log "Go2 asset: OK (${GO2_USD})"
else
    log "ERROR: ассет Go2 не найден: ${GO2_USD}" >&2
    exit 1
fi

export PYTHONPATH="${ISAAC_JAZZY}/rclpy:${QUADROPTED_MSGS_PY}"
export AMENT_PREFIX_PATH="${ISAAC_JAZZY}:${PROJECT_ROOT}/install/quadropted_msgs"
export LD_LIBRARY_PATH="${ISAAC_JAZZY}/lib:${PROJECT_ROOT}/install/quadropted_msgs/lib"
export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"
export ROS_DOMAIN_ID="0"
export CYCLONEDDS_URI="file://${HOME}/.cyclonedds.xml"
export PYTHONUNBUFFERED="1"

log "PYTHONPATH=${PYTHONPATH}"
log "RMW=${RMW_IMPLEMENTATION} ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
log "запуск: ${ISAAC_VENV}/bin/python -u ${BRIDGE} $*"
exec "${ISAAC_VENV}/bin/python" -u "${BRIDGE}" "$@"
