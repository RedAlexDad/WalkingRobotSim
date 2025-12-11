#!/bin/bash
# startup.bash
set -e

# Цвета
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

# Префиксы
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; }

# Вывод справки по командам
echo -e "${BLUE}========== ДОСТУПНЫЕ КОМАНДЫ ==========${NC}"

echo -e "\n${YELLOW}Запуск симуляции в Gazebo:${NC}"
echo -e "  ros2 launch ros2_gazebo <NAME_ROBOT>_run.launch.py world_file_name:=train x:=6 y:=4 z:=0.5"

echo -e "\n${GREEN}Робот Go1:${NC}"
echo -e "  ros2 launch ros2_gazebo go1_run.launch.py"
echo -e "\n${GREEN}Робот Go2:${NC}"
echo -e "  ros2 launch ros2_gazebo go2_run.launch.py"

echo -e "\n${YELLOW}Запуск контроля робота (Управление робота по клавиатуре):${NC}"
echo -e "  ros2 run unitree_guide2 junior_ctrl"

echo -e "\n${YELLOW}Построение картографии (SLAM):${NC}"
echo -e "  ros2 launch ros2_cartography cartography.launch.py"
echo -e "  ros2 launch ros2_cartography rtabmap.launch.py"  # RTAB-Map для SLAM

echo -e "\n${YELLOW}Навигация с AMCL (с картой):${NC}"
echo -e "  ros2 launch ros2_navigation navigation.launch.py"
echo -e "  ros2 launch ros2_navigation navigation.launch.py map:=/path/to/your_map.yaml"

echo -e "\n${YELLOW}Навигация с SLAM (без карты и AMCL):${NC}"
echo -e "  ros2 launch ros2_navigation navigation_slam.launch.py"

echo -e "\n${YELLOW}Распознавание объектов с помощью YOLO:${NC}"
echo -e "  ros2 run ros2_yolo_recognition detect_object"

echo -e "\n${BLUE}=======================================${NC}"
