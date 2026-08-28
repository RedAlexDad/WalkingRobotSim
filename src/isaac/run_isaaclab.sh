#!/bin/bash
# run_isaaclab.sh — запуск go2_isaac_ros2 (IsaacLab) с нашим окружением.
#
# Использует:
#   - IsaacLab 3.0 (установлен в ~/isaacsim-venv)
#   - Локальные ассеты (ISAACSIM_ASSET_ROOT=~/isaac_assets) вместо S3
#   - rclpy Isaac Sim (Jazzy) для /lowcmd и /lowstate
#   - ручной python-модуль unitree_go (вместо сборки unitree_ros2)
#
# Запуск:
#   source ~/isaacsim-venv/bin/activate
#   bash src/isaac/run_isaaclab.sh [--headless]
#
# Управление роботом: публиковать LowCmd в /lowcmd (q, kp, kd на 12 суставов).
# Чтение: /lowstate (joint_pos, imu), /utlidar/cloud.

set -euo pipefail
export LC_ALL=C

ts() {
    local ns
    ns=$(date +%H:%M:%S.%N)
    echo "${ns%??????}"
}
log() {
    echo "[$(ts)] [run_isaaclab] $*"
}

# Минимальная RAM
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
        log "ERROR: памяти недостаточно." >&2
        exit 1
    fi
fi

ISAAC_VENV="${HOME}/isaacsim-venv"
ISAAC_JAZZY="${ISAAC_VENV}/lib/python3.12/site-packages/isaacsim/exts/isaacsim.ros2.core/jazzy"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
GO2_ISAAC="${HOME}/GitHub/go2_isaac_ros2"

# Локальные ассеты (вместо S3 6.1)
export ISAACSIM_ASSET_ROOT="${HOME}/isaac_assets"

# go2_isaac_ros2 + python-типы unitree_go (собраны через colcon в контейнере,
# .so скопированы на хост). rclpy Isaac (Jazzy) добавляется в sys.path
# в run_sim.py (чтобы не мешать AppLauncher).
export PYTHONPATH="${GO2_ISAAC}"
export LD_LIBRARY_PATH="${HOME}/isaacsim-venv/lib/python3.12/site-packages/unitree_go_lib:${LD_LIBRARY_PATH:-}"
export AMENT_PREFIX_PATH="${ISAAC_JAZZY}/rclpy:${HOME}/isaacsim-venv/ament_install/unitree_go:${AMENT_PREFIX_PATH:-}"
export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"
export ROS_DOMAIN_ID="0"
export CYCLONEDDS_URI="file://${HOME}/.cyclonedds.xml"
export PYTHONUNBUFFERED="1"

log "ISAACSIM_ASSET_ROOT=${ISAACSIM_ASSET_ROOT}"
log "PYTHONPATH=${PYTHONPATH}"
log "запуск go2_isaac_ros2 (main.py) $*"
exec "${ISAAC_VENV}/bin/python" -u "${GO2_ISAAC}/go2_isaac_ros2/main.py" "$@"
