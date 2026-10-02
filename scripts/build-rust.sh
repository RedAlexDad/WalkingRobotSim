#!/usr/bin/env bash
# Пересборка Rust-бинарников контроллера (robot_controller_node, odometry_node).
#
# Обязательна после изменений исходников: в контейнере install/.../robot_controller_node
# — симлинк на хостовый ./src/.../target/release (bind-mount project_src), поэтому
# сборка образа НЕ обновляет реально запускаемый бинарник.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTAINER="${WRS_CONTAINER:-walking_robot_sim}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"

if ! docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER"; then
    echo "[!] контейнер $CONTAINER не запущен — сначала make deploy/up" >&2
    exit 1
fi

docker exec "$CONTAINER" bash -lc \
    "source /opt/ros/${ROS_DISTRO}/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; cd /root/ws/src/quadropted_controller_rust && cargo build --release"
