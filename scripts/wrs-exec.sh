#!/usr/bin/env bash
# Выполнить команду в контейнере с уже подгруженными ROS + workspace.
# В отличие от make-define не страдает от запятых/кавычек в аргументах.
#
#   scripts/wrs-exec.sh [-it|-i|-d] <команда> [аргументы...]
set -euo pipefail

CONTAINER="${WRS_CONTAINER:-walking_robot_sim}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

MODE=()
case "${1:-}" in
    -it|-i|-d) MODE=("$1"); shift ;;
esac

exec docker exec "${MODE[@]}" "$CONTAINER" bash -c \
    'source /opt/ros/'"$ROS_DISTRO"'/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; exec "$@"' \
    wrs "$@"
