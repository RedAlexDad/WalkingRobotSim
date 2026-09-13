#!/bin/bash
# run_ik_repeats.sh — N повторов IK/TROT для статистики.
# Перезапускает контроллер (REST), IsaacLab, подаёт TROT+скорость,
# ждёт заданное время, останавливает. Результат — telemetry_ik_r<i>_*.csv.
set -u
N="${1:-3}"
RUN_SEC="${2:-20}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CT="walking_robot_sim"

for i in $(seq 1 "$N"); do
  echo "=== IK повтор $i/$N ==="
  timeout 20 docker exec "$CT" bash -lc "pkill -f robot_controller_node; sleep 1" >/dev/null 2>&1
  timeout 20 docker exec -d "$CT" bash -lc "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && exec ros2 run quadropted_controller_rust robot_controller_node --ros-args -r __ns:=/robot1 > /tmp/ctrl.log 2>&1"
  sleep 3
  cd "$REPO"
  GO2_TELEMETRY_TAG=ik_r$i GO2_VEL_CMD="0.3 0 0" nohup setsid bash src/isaac/run_isaaclab.sh --headless > /tmp/ik_r$i.log 2>&1 < /dev/null &
  # ждём готовности среды (появление REPORT)
  for _ in $(seq 1 60); do
    sleep 2
    grep -aq "\[SIM\] REPORT" /tmp/ik_r$i.log 2>/dev/null && break
  done
  echo "  среда готова, подаю TROT"
  timeout 20 docker exec "$CT" bash -lc "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 topic pub -1 /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand '{mode: \"TROT\", robot_id: 1}' >/dev/null 2>&1; ros2 topic pub -1 /robot1/robot_velocity quadropted_msgs/msg/RobotVelocity '{robot_id: 1, cmd_vel: {linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}}' >/dev/null 2>&1"
  sleep "$RUN_SEC"
  pkill -f "run_sim_telemetr[y].py"
  sleep 3
  echo "  повтор $i завершён"
done
echo "=== все повторы завершены ==="
ls -t "$REPO"/logs/isaac/telemetry_ik_r*_*.csv 2>/dev/null
