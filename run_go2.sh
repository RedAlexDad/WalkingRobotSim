#!/bin/bash

# Скрипт для запуска Go2 в Gazebo с правильными переменными окружения
# Все ошибки про загрузку мешей и плагинов должны быть исправлены

# Очистить экран
clear

# Перейти в директорию проекта
cd /home/redalexdad/GitHub/WalkingRobotSim

# Установить ROS2 окружение
source install/setup.bash

# Запустить Go2 с параметрами по умолчанию
# Параметры:
#   world_file_name: название мира (default: test.sdf)
#   x, y, z: начальная позиция робота
ros2 launch ros2_gazebo go2_run.launch.py

