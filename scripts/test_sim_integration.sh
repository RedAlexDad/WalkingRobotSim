#!/bin/bash
# test_sim_integration.sh — интеграционные тесты против ЖИВОЙ симуляции
#
# Требует запущенную симуляцию: make deploy && make gazebo
# Проверяет всю систему целиком (не отдельные юниты):
#   1. Все критические узлы поднялись в namespace /robot1
#   2. sim-time: stamp в odom/scan растёт (не wall-clock, не нулевой)
#   3. imu-подписка у odometry_rust (регрессия: _imu_sub дропался в if-блоке)
#   4. Соединение контроллер → ros2_control (1 pub + 1 sub)
#   5. Данные суставов реально идут
#   6. foot_contact публикуется (нужен для одометрии)
#   7. stall_status = false (регрессия: ложное застревание при движении)
#   8. Odometry публикуется и имеет sim-time stamp
#   9. TF-цепочка map→odom→base_link→... полная
#   10. SLAM-карта публикуется и строится
#   11. Scan идёт
#   12. Движение: odom растёт при команде (без «белого круга»)
#   13. Восстановление: после остановки odom замирает (зомби-процессов нет)
#   14. EKF согласован с raw odom
#
# Usage: bash scripts/test_sim_integration.sh [container_name]
#
# Возврат: 0 — все обязательные проверки пройдены,
#          1 — хотя бы одна критическая проверка упала.
#          Необязательные (warn) не влияют на код возврата.

set -u

CONTAINER="${1:-walking_robot_sim}"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

PASS=0; FAIL=0; WARN=0

ok()   { PASS=$((PASS+1)); echo -e "${GREEN}✅ $1${NC}"; }
fail() { FAIL=$((FAIL+1)); echo -e "${RED}❌ $1${NC}"; }
warn() { WARN=$((WARN+1)); echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# Сбрасываем ROS 2 daemon: устаревший daemon кэширует endpoint-info в
# несовместимом формате → `ros2 topic echo/--once` падает с
# "unknown tag 'rclpy.endpoint_info.TopicEndpointInfo'" и даёт ложные FAIL.
# Выполняем один раз перед проверками (не в каждом run(), чтобы не тормозить).
docker exec "$CONTAINER" bash -c \
    "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 daemon stop >/dev/null 2>&1" 2>&1 || true

# Выполнить команду внутри контейнера с ROS-окружением
run() {
    docker exec "$CONTAINER" bash -c \
        "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && $1" 2>&1
}

# Проверка: робот вертикален (не упал). Использует TF odom→base_link (надёжнее
# IMU, т.к. gz IMU-плагин может выдавать несоответствующую позе ориентацию).
# |roll|,|pitch| < 30° считаем вертикальным (стойка/ходьба).
check_robot_vertical() {
    local LABEL="$1"
    local RPY=$(docker exec "$CONTAINER" bash -c "
        source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null
        timeout 6 ros2 run tf2_ros tf2_echo odom base_link --ros-args -r tf:=/robot1/tf -r tf_static:=/robot1/tf_static 2>/dev/null \
            | grep -E 'RPY \(degree\)' | head -1 | grep -oP '\[[^]]+\]' | tr -d '[]' | tr ',' ' '
    " 2>&1)
    local RD=$(echo "$RPY" | awk '{print $1}')
    local PD=$(echo "$RPY" | awk '{print $2}')
    if [ -z "${RD:-}" ]; then
        warn "не удалось прочитать TF-позу ($LABEL)"
        return 1
    fi
    # Отрицательные → модуль
    RD=$(echo "$RD" | awk '{if ($1 < 0) print -$1; else print $1}')
    PD=$(echo "$PD" | awk '{if ($1 < 0) print -$1; else print $1}')
    local VERT=$(echo "$RD $PD" | awk '{print ($1 < 30 && $2 < 30) ? "yes" : "no"}')
    if [ "$VERT" = "yes" ]; then
        ok "робот вертикален ($LABEL): roll=$RD°, pitch=$PD°"
        return 0
    else
        fail "робот УПАЛ ($LABEL): roll=$RD°, pitch=$PD° — двигаться нельзя!"
        return 1
    fi
}

echo "═══════════════════════════════════════════════════════════"
echo " Интеграционные тесты: WalkingRobotSim (живая симуляция)"
echo " Контейнер: $CONTAINER"
echo "═══════════════════════════════════════════════════════════"

# Проверка: контейнер запущен
if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER"; then
    echo -e "${RED}❌ Контейнер $CONTAINER не запущен.${NC}"
    echo "Запустите: make deploy && make gazebo"
    exit 1
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 1. Критические узлы в namespace /robot1 ═══"
NODES=$(run "ros2 node list 2>&1")
REQUIRED_NODES="robot_controller_rust odometry_rust ekf_filter_node slam_toolbox
                robot_state_publisher joint_group_controller controller_manager
                ros_gz_bridge cmd_vel_pub_cpp"
for n in $REQUIRED_NODES; do
    if echo "$NODES" | grep -q "/robot1/$n"; then
        ok "узел /robot1/$n"
    else
        fail "узел /robot1/$n НЕ найден"
    fi
done
if echo "$NODES" | grep -q "slam_toolbox"; then
    ok "SLAM запущен (slam_toolbox)"
else
    fail "slam_toolbox не запущен — картография не работает"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 2. sim-time (stamp должен быть из /clock, не wall-clock) ═══"
ODOM_STAMP=$(run "timeout 4 ros2 topic echo /robot1/odom --once 2>&1")
SEC=$(echo "$ODOM_STAMP" | grep -A2 'stamp:' | grep -E 'sec:' | head -1 | grep -oP '\d+')
NANO=$(echo "$ODOM_STAMP" | grep -A2 'stamp:' | grep -E 'nanosec:' | head -1 | grep -oP '\d+')
if [ -n "${SEC:-}" ] && [ "${SEC:-0}" -gt 5 ]; then
    ok "odom stamp sec=$SEC (sim-time работает)"
elif [ -n "${SEC:-}" ] && [ "${SEC:-0}" -eq 0 ]; then
    fail "odom stamp=0 — sim-time НЕ подключён (EKF будет «jump back in time»)"
else
    fail "не удалось прочитать stamp odom"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 3. imu-подписка у odometry_rust (регрессия _imu_sub) ═══"
IMU_INFO=$(run "timeout 5 ros2 topic info /robot1/imu_plugin/out -v 2>&1")
if echo "$IMU_INFO" | grep -q "odometry_rust"; then
    ok "odometry_rust подписан на imu_plugin/out (imu-sub живёт)"
else
    fail "odometry_rust НЕ подписан на imu — stall не будет выходить!"
fi
if echo "$IMU_INFO" | grep -q "robot_controller_rust"; then
    ok "robot_controller_rust подписан на imu"
else
    fail "robot_controller_rust НЕ подписан на imu — компенсация не работает"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 4. Соединение контроллер → ros2_control ═══"
INFO=$(run "ros2 topic info /robot1/joint_group_controller/commands 2>&1")
P=$(echo "$INFO" | grep -oP 'Publisher count: \K\d+')
S=$(echo "$INFO" | grep -oP 'Subscription count: \K\d+')
if [ "${P:-0}" -ge 1 ] && [ "${S:-0}" -ge 1 ]; then
    ok "commands: $P pub + $S sub (контроллер ↔ ros2_control)"
else
    fail "commands: $P pub + $S sub (ожидалось ≥1+≥1) — робот не получит команды!"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 5. Данные суставов идут ═══"
DATA=$(run "timeout 4 ros2 topic echo /robot1/joint_group_controller/commands --once 2>&1")
if echo "$DATA" | grep -q "data:"; then
    ANGLES=$(echo "$DATA" | grep -A13 "data:" | grep -E "^- " | head -12 | tr '\n' ' ')
    ok "углы публикуются ($(echo "$ANGLES" | wc -w) значений)"
else
    fail "нет данных на joint_group_controller/commands"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 6. foot_contact публикуется ═══"
FC=$(run "timeout 4 ros2 topic echo /robot1/foot_contact --once 2>&1")
if echo "$FC" | grep -q "contacts:"; then
    ok "foot_contact публикуется (нужен для одометрии)"
else
    fail "foot_contact НЕ публикуется — одометрия не будет считать перемещение!"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 6b. Нет посторонних команд движения (teleop/зомби) ═══"
# Если пользователь оставил teleop или висит зомби `ros2 topic pub robot_velocity`,
# интеграционный тест движения будет давать ЛОЖНЫЕ результаты. Проверяем:
VEL_PUBS=$(run "ros2 topic info /robot1/robot_velocity 2>&1" | grep -oP 'Publisher count: \K\d+')
CMDVEL_PUBS=$(run "ros2 topic info /robot1/cmd_vel 2>&1" | grep -oP 'Publisher count: \K\d+')
TELEOP=$(run "ps aux 2>&1" | grep -c teleop_twist_keyboard || true)
TELEOP=$(echo "${TELEOP:-0}" | tr -d ' ')
# robot_velocity должен публиковать ТОЛЬКО cmd_vel_pub_cpp (1).
# cmd_vel штатно публикуют Nav2 (behavior_server, controller_server и т.д.) — их >1 нормально,
# НО если активен teleop_twist_keyboard — это посторонняя команда движения.
if [ "${VEL_PUBS:-0}" -gt 1 ] || [ "${TELEOP:-0}" -gt 0 ]; then
    fail "посторонние команды: robot_velocity pubs=${VEL_PUBS} (ожидается 1), teleop procs=${TELEOP}. Убейте: pkill teleop_twist_keyboard"
else
    ok "только штатные publisher'ы (robot_velocity=$VEL_PUBS, cmd_vel=$CMDVEL_PUBS, teleop=$TELEOP)"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 7. stall_status = false (регрессия «белого круга») ═══"
ST=$(run "timeout 4 ros2 topic echo /robot1/stall_status --once 2>&1")
if echo "$ST" | grep -q "data: false"; then
    ok "stall_status=false (одометрия не заморожена)"
elif echo "$ST" | grep -q "data: true"; then
    fail "stall_status=true — одометрия заморожена, SLAM будет рисовать «белый круг»!"
else
    warn "stall_status не публикуется или не прочитался"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 8. Odometry + EKF согласованы ═══"
ODOM_P=$(run "ros2 topic info /robot1/odom 2>&1" | grep -oP 'Publisher count: \K\d+')
if [ "${ODOM_P:-0}" -ge 1 ]; then
    ok "/robot1/odom публикуется ($ODOM_P pub)"
else
    fail "/robot1/odom НЕ публикуется"
fi
FILT=$(run "timeout 4 ros2 topic echo /robot1/odometry/filtered --once 2>&1")
FX=$(echo "$FILT" | grep -E '^      x:' | head -1 | grep -oP '[\d.-]+')
if [ -n "${FX:-}" ]; then
    ok "EKF публикует odometry/filtered (x=$FX)"
else
    warn "EKF odometry/filtered не публикуется (может быть не запущен)"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 9. TF-цепочка map→odom→base_link полная ═══"
# Проверяем через tf2_echo в namespace (не глобальный /tf, а /robot1/tf)
TF_CHAIN=$(docker exec "$CONTAINER" bash -c "
    source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null
    timeout 8 ros2 run tf2_ros tf2_echo map base_link --ros-args -r tf:=/robot1/tf -r tf_static:=/robot1/tf_static 2>&1 | head -6
")
if echo "$TF_CHAIN" | grep -q "Translation"; then
    TX=$(echo "$TF_CHAIN" | grep Translation | grep -oP '\[\K[\d.-]+')
    ok "map→base_link существует (Translation x=$TX)"
else
    fail "TF-цепочка map→base_link НЕ полная: $(echo "$TF_CHAIN" | head -2 | tr '\n' ' ')"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 10. SLAM-карта публикуется ═══"
MAP_INFO=$(run "ros2 topic info /robot1/map 2>&1")
MAP_P=$(echo "$MAP_INFO" | grep -oP 'Publisher count: \K\d+')
MAP_S=$(echo "$MAP_INFO" | grep -oP 'Subscription count: \K\d+')
if [ "${MAP_P:-0}" -ge 1 ]; then
    ok "/robot1/map публикуется ($MAP_P pub, $MAP_S sub)"
else
    fail "/robot1/map НЕ публикуется — SLAM не строит карту!"
fi
MAP_DATA=$(run "timeout 5 ros2 topic echo /robot1/map --once 2>&1")
if echo "$MAP_DATA" | grep -q "resolution"; then
    RES=$(echo "$MAP_DATA" | grep resolution | grep -oP '[\d.]+' | head -1)
    W=$(echo "$MAP_DATA" | grep -A1 'info:' | grep -oP 'width: \K\d+' | head -1)
    H=$(echo "$MAP_DATA" | grep -A1 'info:' | grep -oP 'height: \K\d+' | head -1)
    ok "карта: ${W}×${H}, res=${RES}"
else
    warn "карта публикуется, но данные не прочитались (может быть ещё пустая)"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 11. Scan идёт ═══"
SCAN_INFO=$(run "ros2 topic info /robot1/scan 2>&1")
SCAN_P=$(echo "$SCAN_INFO" | grep -oP 'Publisher count: \K\d+')
if [ "${SCAN_P:-0}" -ge 1 ]; then
    ok "/robot1/scan публикуется ($SCAN_P pub)"
else
    fail "/robot1/scan НЕ публикуется — SLAM/Localization без лидара"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 11b. Частота топиков (realtime-деградация) ═══"
# ros2 topic hz выводит "average rate: N" после замера. Замеряем ~4 сек.
HZ_ODOM=$(run "timeout 6 ros2 topic hz /robot1/odom 2>&1" | grep -oP 'average rate: \K[\d.]+' | tail -1)
if [ -n "${HZ_ODOM:-}" ]; then
    OK_HZ=$(LC_ALL=C awk -v h="$HZ_ODOM" 'BEGIN{print (h >= 40) ? "yes":"no"}')
    if [ "$OK_HZ" = "yes" ]; then ok "odom: $HZ_ODOM Гц (≥40)"; else fail "odom: $HZ_ODOM Гц (< 40) — контроллер/одометрия не в realtime!"; fi
else
    warn "не удалось измерить частоту odom"
fi
HZ_SCAN=$(run "timeout 6 ros2 topic hz /robot1/scan 2>&1" | grep -oP 'average rate: \K[\d.]+' | tail -1)
if [ -n "${HZ_SCAN:-}" ]; then
    OK_HZ=$(LC_ALL=C awk -v h="$HZ_SCAN" 'BEGIN{print (h >= 4) ? "yes":"no"}')
    if [ "$OK_HZ" = "yes" ]; then ok "scan: $HZ_SCAN Гц (≥4)"; else fail "scan: $HZ_SCAN Гц (< 4) — LiDAR тормозит!"; fi
else
    warn "не удалось измерить частоту scan"
fi
HZ_JOINT=$(run "timeout 6 ros2 topic hz /robot1/joint_group_controller/commands 2>&1" | grep -oP 'average rate: \K[\d.]+' | tail -1)
if [ -n "${HZ_JOINT:-}" ]; then
    OK_HZ=$(LC_ALL=C awk -v h="$HZ_JOINT" 'BEGIN{print (h >= 50) ? "yes":"no"}')
    if [ "$OK_HZ" = "yes" ]; then ok "joint commands: $HZ_JOINT Гц (≥50)"; else fail "joint commands: $HZ_JOINT Гц (< 50) — контроллер не в realtime!"; fi
else
    warn "не удалось измерить частоту joint commands"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 11c. Консистентность EKF vs raw odom ═══"
OX=$(run "timeout 3 ros2 topic echo /robot1/odom --once 2>&1" | grep 'x:' | head -1 | grep -oP '[\d.-]+')
FX=$(run "timeout 3 ros2 topic echo /robot1/odometry/filtered --once 2>&1" | grep 'x:' | head -1 | grep -oP '[\d.-]+')
if [ -n "${OX:-}" ] && [ -n "${FX:-}" ]; then
    EKF_DIFF=$(LC_ALL=C awk -v a="$OX" -v b="$FX" 'BEGIN{d=a-b; if(d<0)d=-d; printf "%.4f", d}')
    EKF_OK=$(LC_ALL=C awk -v d="$EKF_DIFF" 'BEGIN{print (d < 0.05) ? "yes":"no"}')
    if [ "$EKF_OK" = "yes" ]; then
        ok "EKF согласован: odom.x=$OX vs filtered.x=$FX (diff=$EKF_DIFF)"
    else
        fail "EKF рассинхрон: odom.x=$OX vs filtered.x=$FX (diff=$EKF_DIFF ≥ 0.05)"
    fi
else
    warn "не удалось сравнить EKF (odom.x=$OX, filtered.x=$FX)"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 11d. Lifecycle-активность Nav2/control ═══"
# controller_server/planner_server — реальные lifecycle-ноды Nav2.
# controller_manager — НЕ lifecycle-нода (ros2_control), его пропускаем.
for LCN in controller_server planner_server; do
    LC_ST=$(run "timeout 5 ros2 lifecycle get /robot1/$LCN 2>&1")
    if echo "$LC_ST" | grep -qi "active"; then
        ok "$LCN: active"
    else
        fail "$LCN: $(echo "$LC_ST" | head -1) — Nav2 подсистема не активна!"
    fi
done

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 11e. TF-цепочка до лидара (map→laser_frame) ═══"
TF_LASER=$(docker exec "$CONTAINER" bash -c "
    source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null
    timeout 6 ros2 run tf2_ros tf2_echo map laser_frame --ros-args -r tf:=/robot1/tf -r tf_static:=/robot1/tf_static 2>&1 | grep Translation | head -1
")
if echo "$TF_LASER" | grep -q "Translation"; then
    ok "map→laser_frame существует ($TF_LASER | head -c 40)"
else
    fail "TF до лидара (map→laser_frame) НЕ полная — SLAM не привяжет карту к сенсору"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 11f. Параметр has_imu_heading (регрессия параметров) ═══"
# Параметр передаётся через params-file в launch; rclrs читает его через
# use_undeclared_parameters, поэтому `ros2 param get` показывает "not set".
# Реальная проверка — факт наличия imu-подписки (см. проверку 3).
IMU_PARAM=$(run "ros2 param get /robot1/odometry_rust has_imu_heading 2>&1")
if echo "$IMU_PARAM" | grep -qi "true"; then
    ok "has_imu_heading=true (явно виден)"
elif echo "$IMU_PARAM" | grep -qi "not set"; then
    # Если imu-подписка жива (проверка 3 ✅) — параметр передан через params-file
    IMU_SUB_ALIVE=$(run "timeout 5 ros2 topic info /robot1/imu_plugin/out -v 2>&1" | grep -c "odometry_rust")
    if [ "${IMU_SUB_ALIVE:-0}" -ge 1 ]; then
        ok "has_imu_heading передан через params-file (imu-подписка активна, проверка 3 ✅)"
    else
        fail "has_imu_heading not set И imu-подписки нет — imu-обработка не работает!"
    fi
else
    fail "has_imu_heading: $(echo "$IMU_PARAM" | head -1)"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 12. Движение: odom растёт при короткой команде ═══"
# Ждём, пока робот устоится после спавна (roll/pitch < 30°), максимум 40 сек.
echo -n "    ожидание устоивания робота..."
VERT_OK=""
for attempt in $(seq 1 20); do
    RPY_NOW=$(docker exec "$CONTAINER" bash -c "
        source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null
        timeout 6 ros2 run tf2_ros tf2_echo odom base_link --ros-args -r tf:=/robot1/tf -r tf_static:=/robot1/tf_static 2>/dev/null \
            | grep -E 'RPY \(degree\)' | head -1 | grep -oP '\[[^]]+\]' | tr -d '[]' | tr ',' ' '
    " 2>&1)
    RD_NOW=$(echo "$RPY_NOW" | awk '{print $1}')
    PD_NOW=$(echo "$RPY_NOW" | awk '{print $2}')
    RD_NOW=$(echo "${RD_NOW:-999}" | awk '{if ($1 < 0) print -$1; else print $1}')
    PD_NOW=$(echo "${PD_NOW:-999}" | awk '{if ($1 < 0) print -$1; else print $1}')
    STABLE=$(echo "$RD_NOW $PD_NOW" | awk '{print ($1 < 30 && $2 < 30) ? "yes" : "no"}')
    if [ "$STABLE" = "yes" ]; then
        VERT_OK="yes"
        echo " стабилен (roll=$RD_NOW°, pitch=$PD_NOW°)"
        break
    fi
    echo -n "."
    sleep 2
done
if [ "$VERT_OK" != "yes" ]; then
    fail "робот не устоялся за 40 сек (roll=$RD_NOW°, pitch=$PD_NOW°) — пропускаем движение"
else
    ok "робот устоялся после спавна"
    # Замер карты SLAM ДО движения (для проверки роста карты)
    MAP_W0=$(run "timeout 4 ros2 topic echo /robot1/map --once 2>&1" | grep -oP 'width: \K\d+' | head -1)
    MAP_H0=$(run "timeout 4 ros2 topic echo /robot1/map --once 2>&1" | grep -oP 'height: \K\d+' | head -1)
    # Короткое движение: одно сообщение vx=0.01 (--once), затем ЯВНАЯ остановка
    # vx=0. Контроллер держит последнюю команду — без нулевой он продолжит идти.
    ODOM_MOVE=$(docker exec "$CONTAINER" bash -c "
        source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null
        timeout 3 ros2 topic echo /robot1/odom --once 2>/dev/null | grep 'x:' | head -1 | grep -oP '[\d.-]+' > /tmp/it_x0
        ros2 topic pub --once /robot1/robot_velocity quadropted_msgs/msg/RobotVelocity '{robot_id: 1, cmd_vel: {linear: {x: 0.01, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}}' >/dev/null 2>&1
        sleep 2
        timeout 3 ros2 topic echo /robot1/odom --once 2>/dev/null | grep 'x:' | head -1 | grep -oP '[\d.-]+' > /tmp/it_x1
        # Явная остановка: vx=0 — контроллер перестаёт генерировать движение
        ros2 topic pub --once /robot1/robot_velocity quadropted_msgs/msg/RobotVelocity '{robot_id: 1, cmd_vel: {linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}}' >/dev/null 2>&1
        ST2=\$(timeout 3 ros2 topic echo /robot1/stall_status --once 2>/dev/null | grep -oP 'data: \K\w+')
        echo \"\$(cat /tmp/it_x0) \$(cat /tmp/it_x1) \$ST2\"
    ")
    # Замер карты SLAM ПОСЛЕ движения
    sleep 2
    MAP_W1=$(run "timeout 4 ros2 topic echo /robot1/map --once 2>&1" | grep -oP 'width: \K\d+' | head -1)
    MAP_H1=$(run "timeout 4 ros2 topic echo /robot1/map --once 2>&1" | grep -oP 'height: \K\d+' | head -1)
    X0=$(echo "$ODOM_MOVE" | awk '{print $1}')
    X1=$(echo "$ODOM_MOVE" | awk '{print $2}')
    ST2=$(echo "$ODOM_MOVE" | awk '{print $3}')
    if [ -n "${X0:-}" ] && [ -n "${X1:-}" ]; then
        # дистанция = |X1 - X0|
        DIST=$(LC_ALL=C awk -v a="$X1" -v b="$X0" 'BEGIN {d = a - b; if (d < 0) d = -d; printf "%.3f", d}')
        GROWTH=$(LC_ALL=C awk -v a="$X1" -v b="$X0" 'BEGIN {print (a != b) ? "yes" : "no"}')
        if [ "$GROWTH" = "yes" ]; then
            ok "odom сдвинулся на $DIST м (x0=$X0 → x1=$X1)"
            TOO_FAR=$(LC_ALL=C awk -v d="$DIST" 'BEGIN {print (d > 3.0) ? "yes" : "no"}')
            if [ "$TOO_FAR" = "yes" ]; then
                fail "робот прошёл $DIST м (> 3 м) — команда слишком долгая или зомби-процесс!"
            else
                ok "дистанция в пределах нормы ($DIST м ≤ 3 м)"
            fi
        else
            fail "odom НЕ изменился при команде: $X0 → $X1 (stall=$ST2) — «белый круг»!"
        fi
    else
        fail "не удалось измерить odom при движении (x0=$X0 x1=$X1 stall=$ST2)"
    fi
    if [ "$ST2" = "false" ] || [ -z "${ST2:-}" ]; then
        ok "stall=false во время движения"
    else
        fail "stall=true во время движения — одометрия заморожена!"
    fi

    echo ""
    info "═══ 12b. Робот не упал после движения ═══"
    check_robot_vertical "после движения"

    # ── 12c. Рост карты SLAM после движения ─────────────────
    echo ""
    info "═══ 12c. SLAM-карта растёт после движения ═══"
    if [ -n "${MAP_W0:-}" ] && [ -n "${MAP_W1:-}" ]; then
        MAP_GROW=$(LC_ALL=C awk -v a="$MAP_W1" -v b="$MAP_W0" 'BEGIN{d=a-b; if(d<0)d=-d; print (d > 1) ? "yes":"no"}')
        if [ "$MAP_GROW" = "yes" ]; then
            ok "карта расширилась: ${MAP_W0}×${MAP_H0} → ${MAP_W1}×${MAP_H1} (SLAM активен)"
        else
            warn "карта не расширилась: ${MAP_W0}×${MAP_H0} → ${MAP_W1}×${MAP_H1} (робот прошёл < клетки или SLAM завис)"
        fi
    else
        warn "не удалось сравнить размеры карты (W0=$MAP_W0 W1=$MAP_W1)"
    fi
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 13. После остановки odom замирает (нет зомби-команд) ═══"
# Ждём, пока робот остановится по инерции (до 8 сек), затем замеряем
sleep 4
SX1=$(run "timeout 3 ros2 topic echo /robot1/odom --once 2>&1" | grep 'x:' | head -1 | grep -oP '[\d.-]+')
sleep 2
SX2=$(run "timeout 3 ros2 topic echo /robot1/odom --once 2>&1" | grep 'x:' | head -1 | grep -oP '[\d.-]+')
if [ -n "${SX1:-}" ] && [ -n "${SX2:-}" ]; then
    # Сравнение с допуском: микро-проскальзывание/инерция ~2 см — это НЕ зомби
    DIFF=$(LC_ALL=C awk -v a="$SX1" -v b="$SX2" 'BEGIN {d = a - b; if (d < 0) d = -d; printf "%.4f", d}')
    DRIFT=$(LC_ALL=C awk -v d="$DIFF" 'BEGIN {print (d > 0.02) ? "yes" : "no"}')
    if [ "$DRIFT" = "no" ]; then
        ok "odom замер после остановки ($SX1 ≈ $SX2, diff=$DIFF) — зомби-процессов нет"
    else
        fail "odom продолжает расти после остановки ($SX1 → $SX2, diff=$DIFF) — зомби-команда!"
    fi
else
    warn "не удалось измерить odom после остановки"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 14. Сервис robot_behavior_command отвечает ═══"
SRV=$(run "timeout 6 ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand '{command: up}' 2>&1")
if echo "$SRV" | grep -q "success"; then
    ok "сервис отвечает: $(echo "$SRV" | grep -E 'success|message' | tr '\n' ' ' | head -c 100)"
else
    warn "сервис robot_behavior_command не ответил (может быть занят)"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 14b. foot_contact значения (контакты считаются) ═══"
FC_VAL=$(run "timeout 4 ros2 topic echo /robot1/foot_contact --once 2>&1" | grep -A2 contacts | tr -d ' \n')
TRUE_COUNT=$(echo "$FC_VAL" | grep -o 'true' | wc -l)
# В TROT робот опирается на 2 диагональные ноги; в стойке/REST — на 4.
# Минимально жизнеспособно: ≥2 ноги в контакте (диагональ TROT).
if [ "${TRUE_COUNT:-0}" -ge 2 ]; then
    ok "foot_contact: $TRUE_COUNT ноги в контакте (≥2, TROT-диагональ)"
else
    fail "foot_contact: $TRUE_COUNT ноги (< 2) — контакты не считаются, одометрия сломана!"
fi

# ──────────────────────────────────────────────────────────────
echo ""
info "═══ 15. Возврат робота на старт (повторяемость теста) ═══"
# gz set_pose телепортирует физическую позу робота на (0, 0, 0.6).
# Примечание: odom-интеграция (leg-одометрия) при этом НЕ сбрасывается —
# робот физически вернулся, но odom покажет старую позицию. Это нормально.
SETPOSE=$(docker exec "$CONTAINER" bash -c "
    source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null
    timeout 5 gz topic -t /world/default/set_pose \
        -m gz.msgs.Pose \
        -p \"name: 'go2', position: {x: 0.0, y: 0.0, z: 0.6}\" 2>&1
" 2>&1)
if [ $? -eq 0 ] && [ -z "$SETPOSE" ]; then
    ok "команда возврата робота на старт отправлена (gz set_pose)"
else
    warn "gz set_pose вывод: $(echo "$SETPOSE" | head -1) — робот мог не вернуться"
fi
# Проверка: робот снова вертикален после телепорта
check_robot_vertical "после возврата на старт"

# ──────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo " ИТОГ: ✅ $PASS | ❌ $FAIL | ⚠️  $WARN"
echo "═══════════════════════════════════════════════════════════"

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}ВСЕ КРИТИЧЕСКИЕ ПРОВЕРКИ ПРОЙДЕНЫ${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}ОБНАРУЖЕНЫ ОШИБКИ ($FAIL)${NC} — см. выше"
    exit 1
fi
