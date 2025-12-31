#!/usr/bin/env bash
set -e

# ROS
source /opt/ros/jazzy/setup.bash

# Workspace
if [ ! -f /root/ws/install/setup.bash ]; then
  echo "[INFO] Первый запуск — собираем workspace..."
  cd /root/ws
  apt-get update && rosdep update
  rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
  colcon build --symlink-install || true
fi

source /root/ws/install/setup.bash 2>/dev/null || true

# Приветствие
source /entrypoint/welcome.sh

# Передаём управление дальше
exec "$@"
