#!/bin/bash
# run_speed_series.sh — серия скоростей для RL и IK (vx = 0.1..0.4).
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CT="walking_robot_sim"
PY="$HOME/isaacsim-venv/bin/python"
SPEEDS="${SPEEDS:-0.1 0.2 0.3 0.4}"
RUN_SEC="${RUN_SEC:-15}"

echo "=== RL: серия скоростей ==="
for v in $SPEEDS; do
  echo "  RL vx=$v"
  echo "$v 0 0" > /tmp/rl_cmd.txt
  cat /tmp/rl_cmd.txt | GO2_TELEMETRY_TAG=rl_v$v timeout 60 "$PY" -u "$REPO/src/isaac/go2_policy.py" --headless --duration "$RUN_SEC" > "/tmp/rl_v$v.log" 2>&1
  echo "    exit=$?"
done

echo "=== IK: серия скоростей ==="
for v in $SPEEDS; do
  echo "  IK vx=$v"
  timeout 20 docker exec "$CT" bash -lc "pkill -f robot_controller_node; sleep 1" >/dev/null 2>&1
  timeout 20 docker exec -d "$CT" bash -lc "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && exec ros2 run quadropted_controller_rust robot_controller_node --ros-args -r __ns:=/robot1 > /tmp/ctrl.log 2>&1"
  sleep 3
  cd "$REPO"
  GO2_TELEMETRY_TAG=ik_v$v nohup setsid bash src/isaac/run_isaaclab.sh --headless > "/tmp/ik_v$v.log" 2>&1 < /dev/null &
  for _ in $(seq 1 60); do sleep 2; grep -aq "\[SIM\] REPORT" "/tmp/ik_v$v.log" 2>/dev/null && break; done
  timeout 20 docker exec "$CT" bash -lc "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 topic pub -1 /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand '{mode: \"TROT\", robot_id: 1}' >/dev/null 2>&1; ros2 topic pub -1 /robot1/robot_velocity quadropted_msgs/msg/RobotVelocity '{robot_id: 1, cmd_vel: {linear: {x: $v, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}}' >/dev/null 2>&1"
  sleep "$RUN_SEC"
  pkill -f "run_sim_telemetr[y].py"
  sleep 3
done
echo "=== серия завершена ==="
ls -t "$REPO"/logs/isaac/telemetry_rl_v*.csv "$REPO"/logs/isaac/telemetry_ik_v*.csv 2>/dev/null
