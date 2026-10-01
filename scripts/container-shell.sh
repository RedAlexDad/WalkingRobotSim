#!/usr/bin/env bash
# Настройка интерактивной оболочки в контейнере (цель `make shell`).
#
# Алиасы пишутся идемпотентно: отдельный файл ~/.wrs_aliases перезаписывается,
# а ~/.bashrc подключает его ровно один раз. Старые дубликаты алиасов, которые
# прежняя версия дописывала в ~/.bashrc при каждом запуске, удаляются.
set -e

ROS_DISTRO="${ROS_DISTRO:-jazzy}"

# Удалить ранее накопленные дубликаты алиасов из .bashrc.
if [ -f ~/.bashrc ]; then
    sed -i -E '/^alias (sim|teleop|topics|nodes|services|actions|waypoints|nav-start|nav-stop|nav-clear|detect)=/d' ~/.bashrc
fi

cat > ~/.wrs_aliases <<'EOF'
alias sim='ros2 launch gazebo_sim launch_cpp.launch.py use_sim_time:=true gui:=true'
alias teleop='ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel'
alias topics='ros2 topic list'
alias nodes='ros2 node list'
alias services='ros2 service list'
alias actions='ros2 action list'
alias waypoints='ros2 service call /robot1/get_waypoints quadropted_msgs/srv/GetWaypoints'
alias nav-start='ros2 service call /robot1/start_navigation std_srvs/srv/Trigger'
alias nav-stop='ros2 service call /robot1/stop_navigation std_srvs/srv/Trigger'
alias nav-clear='ros2 service call /robot1/clear_waypoints std_srvs/srv/Trigger'
alias detect='ros2 launch quadropted_perception yolo_detector.launch.py'
EOF

# Подключить ~/.wrs_aliases из .bashrc ровно один раз.
grep -q 'wrs_aliases' ~/.bashrc 2>/dev/null || \
    echo '[ -f ~/.wrs_aliases ] && source ~/.wrs_aliases' >> ~/.bashrc

source "/opt/ros/${ROS_DISTRO}/setup.bash"
source /root/ws/install/setup.bash 2>/dev/null || true

export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\[\033[01;31m\](ROS '"${ROS_DISTRO}"')\[\033[00m\]\$ '

printf '\033[0;32m\033[1mROS %s окружение настроено!\033[0m\n' "${ROS_DISTRO}"
printf '\033[0;36mДоступные команды:\033[0m\n'
printf '   sim          - Запуск Gazebo симуляции (в контейнере)\n'
printf '   teleop       - Управление роботом с клавиатуры\n'
printf '   topics       - ros2 topic list\n'
printf '   nodes        - ros2 node list\n'
printf '   services     - ros2 service list\n'
printf '   actions      - ros2 action list\n'
printf '   waypoints    - Показать текущие путевые точки\n'
printf '   nav-start    - Запустить навигацию по waypoint\n'
printf '   nav-stop     - Остановить навигацию\n'
printf '   nav-clear    - Очистить waypoint\n'
printf '   detect       - Запустить YOLO детектор\n'

exec bash
