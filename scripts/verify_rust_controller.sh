#!/bin/bash
# verify_rust_controller.sh — комплексная проверка Rust-контроллера в симуляции
#
# Проверяет:
#   1. Узлы robot_controller_rust / odometry_rust в namespace /robot1
#   2. Соединение контроллер → joint_group_controller (1 pub + 1 sub)
#   3. Публикацию углов суставов (данные реально идут)
#   4. Odometry: /robot1/odom публикуется, EKF подписан
#   5. Переключение режима TROT и проверка, что контроллер реагирует
#
# Usage: bash scripts/verify_rust_controller.sh

set -u

CONTAINER="${1:-walking_robot_sim}"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

run() { docker exec "$CONTAINER" bash -c "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && $1"; }

echo "═══════════════════════════════════════════════════"
echo " Проверка Rust-контроллера в симуляции"
echo "═══════════════════════════════════════════════════"

# ── 1. Узлы ─────────────────────────────────────────────
echo ""
echo "[1] Узлы в namespace /robot1:"
NODES=$(run "ros2 node list 2>&1")
if echo "$NODES" | grep -q "/robot1/robot_controller_rust"; then
    ok "robot_controller_rust найден"
else
    fail "robot_controller_rust НЕ найден (есть: $(echo "$NODES" | grep -i robot | tr '\n' ' '))"
fi
if echo "$NODES" | grep -q "/robot1/odometry_rust"; then
    ok "odometry_rust найден"
else
    if echo "$NODES" | grep -q "/robot1/dog_odometry"; then
        ok "dog_odometry найден (старое имя узла)"
    else
        fail "odometry_rust НЕ найден"
    fi
fi

# ── 2. Соединение команд ────────────────────────────────
echo ""
echo "[2] Соединение контроллер → ros2_control:"
INFO=$(run "ros2 topic info /robot1/joint_group_controller/commands 2>&1")
P=$(echo "$INFO" | grep -oP 'Publisher count: \K\d+')
S=$(echo "$INFO" | grep -oP 'Subscription count: \K\d+')
if [ "${P:-0}" -ge 1 ] && [ "${S:-0}" -ge 1 ]; then
    ok "commands: $P pub + $S sub (контроллер ↔ ros2_control)"
else
    fail "commands: $P pub + $S sub (ожидалось ≥1+≥1)"
fi

# ── 3. Публикация углов ─────────────────────────────────
echo ""
echo "[3] Данные углов идут от контроллера:"
DATA=$(run "timeout 4 ros2 topic echo /robot1/joint_group_controller/commands --once 2>&1")
if echo "$DATA" | grep -q "data:"; then
    ANGLES=$(echo "$DATA" | grep -A13 "data:" | grep -E "^- " | tr '\n' ' ')
    ok "углы публикуются: $ANGLES"
else
    fail "нет данных на /robot1/joint_group_controller/commands"
fi

# ── 4. Odometry ─────────────────────────────────────────
echo ""
echo "[4] Odometry:"
ODOM_INFO=$(run "ros2 topic info /robot1/odom 2>&1")
ODOM_P=$(echo "$ODOM_INFO" | grep -oP 'Publisher count: \K\d+')
if [ "${ODOM_P:-0}" -ge 1 ]; then
    ok "/robot1/odom публикуется ($ODOM_P pub)"
else
    fail "/robot1/odom НЕ публикуется"
fi
EKF=$(run "ros2 node info /robot1/ekf_filter_node 2>&1" | grep -c "odom")
if [ "$EKF" -gt 0 ]; then
    ok "EKF видит odom"
else
    warn "EKF не подписан на odom (проверь ekf.yaml odom0)"
fi

# ── 5. Переключение режима TROT ─────────────────────────
echo ""
echo "[5] Переключение в TROT и реакция контроллера:"
run "ros2 topic pub --once /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand '{mode: TROT, robot_id: 1}'" >/dev/null 2>&1
run "ros2 topic pub --once /robot1/robot_velocity quadropted_msgs/msg/RobotVelocity '{robot_id: 1, cmd_vel: {linear: {x: 0.05, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}}'" >/dev/null 2>&1
sleep 2
DATA2=$(run "timeout 4 ros2 topic echo /robot1/joint_group_controller/commands --once 2>&1")
if echo "$DATA2" | grep -q "data:"; then
    A2=$(echo "$DATA2" | grep -A13 "data:" | grep -E "^- " | tr '\n' ' ')
    ok "команды после TROT: $A2"
    warn "Если углы изменились относительно стойки — контроллер ходит (проверь визуально в Gazebo)"
else
    fail "нет данных после TROT"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo " Готово. Если все ✅ — контроллер работает."
echo " Для ходьбы: ros2 topic pub /robot1/robot_velocity ... (vx>0)"
echo "═══════════════════════════════════════════════════"
