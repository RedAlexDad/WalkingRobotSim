#!/bin/bash
# run_bridge.sh — запуск isaac_bridge.py с корректным ROS2-окружением.
#
# Проблема: host-ROS (Lyrical, py3.14) в PYTHONPATH конфликтует со
# встроенным rclpy Isaac Sim (Jazzy, py3.12). Isaac Sim при старте
# сохраняет OLD_PYTHONPATH и восстанавливает пути, совпадающие с
# AMENT_PREFIX_PATH. Поэтому PYTHONPATH и AMENT_PREFIX_PATH должны
# указывать на jazzy/rclpy Isaac Sim.
#
# Использование:
#   source ~/isaacsim-venv/bin/activate
#   bash src/isaac/run_bridge.sh [--headless] [--ns /robot1]

set -euo pipefail

ISAAC_VENV="${HOME}/isaacsim-venv"
ISAAC_JAZZY="${ISAAC_VENV}/lib/python3.12/site-packages/isaacsim/exts/isaacsim.ros2.core/jazzy"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE="${SCRIPT_DIR}/isaac_bridge.py"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ ! -d "${ISAAC_JAZZY}/rclpy" ]; then
    echo "[run_bridge] ERROR: не найден rclpy Isaac Sim: ${ISAAC_JAZZY}/rclpy" >&2
    exit 1
fi

# Собранные типы quadropted_msgs (py3.12) — для foot_contact
QUADROPTED_MSGS_PY="${PROJECT_ROOT}/install/quadropted_msgs/lib/python3.12/site-packages"

export PYTHONPATH="${ISAAC_JAZZY}/rclpy:${QUADROPTED_MSGS_PY}"
export AMENT_PREFIX_PATH="${ISAAC_JAZZY}:${PROJECT_ROOT}/install/quadropted_msgs"
export LD_LIBRARY_PATH="${ISAAC_JAZZY}/lib:${PROJECT_ROOT}/install/quadropted_msgs/lib"
export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"
export ROS_DOMAIN_ID="0"
export CYCLONEDDS_URI="file://${HOME}/.cyclonedds.xml"
export PYTHONUNBUFFERED="1"

echo "[run_bridge] PYTHONPATH=${PYTHONPATH}"
exec "${ISAAC_VENV}/bin/python" -u "${BRIDGE}" "$@"
