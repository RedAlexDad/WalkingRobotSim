#!/bin/bash

# Walking Robot Simulation Manager - Simple Architecture
# Простой менеджер для запуска симуляции Walking Robot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="walking_robot_sim"
IMAGE_NAME="walking_robot_sim:latest"
DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ════════════════════════════════════════════════════════════
# ОСНОВНЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════

cmd_build() {
    info "Сборка Docker образа..."
    cd "$DOCKER_DIR"
    docker compose build
    success "Образ собран"
}

cmd_up() {
    info "Запуск контейнера $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    docker compose up -d
    
    info "Ожидание инициализации контейнера (30 сек)..."
    sleep 30
    
    info "Статус контейнера:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    
    success "Контейнер запущен"
}

cmd_down() {
    info "Остановка контейнера $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    docker compose down
    success "Контейнер остановлен"
}

cmd_restart() {
    info "Перезапуск контейнера $CONTAINER_NAME..."
    cmd_down
    cmd_up
}

cmd_logs() {
    cd "$DOCKER_DIR"
    docker compose logs -f
}

cmd_shell() {
    info "Подключение к контейнеру $CONTAINER_NAME..."
    docker exec -it $CONTAINER_NAME bash
}

cmd_exec() {
    docker exec -it $CONTAINER_NAME bash -c "$*"
}

# ════════════════════════════════════════════════════════════
# СПЕЦИАЛЬНЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════

cmd_gazebo() {
    info "Запуск Gazebo симуляции..."
    docker exec -it $CONTAINER_NAME bash -c "
        source /opt/ros/jazzy/setup.bash
        source /root/ws/install/setup.bash 2>/dev/null || true
        ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true
    "
}

cmd_teleop() {
    info "Запуск управления роботом (teleop_twist_keyboard)..."
    docker exec -it $CONTAINER_NAME bash -c "
        source /opt/ros/jazzy/setup.bash
        source /root/ws/install/setup.bash 2>/dev/null || true
        ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
    "
}

cmd_status() {
    info "Статус контейнера:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    info "Использование ресурсов:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" $CONTAINER_NAME 2>/dev/null || echo "Контейнер не запущен"
}

cmd_clean() {
    warning "Очистка Docker образов и контейнеров..."
    cd "$DOCKER_DIR"
    docker compose down -v --remove-orphans
    docker system prune -f
    success "Очистка завершена"
}

# ════════════════════════════════════════════════════════════
# ПОМОЩЬ
# ════════════════════════════════════════════════════════════

cmd_help() {
    echo "Walking Robot Simulation Manager - Simple Architecture"
    echo ""
    echo "Основные команды:"
    echo "  build       Сборка Docker образа"
    echo "  up          Запуск контейнера"
    echo "  down        Остановка контейнера"
    echo "  restart     Перезапуск контейнера"
    echo "  logs        Просмотр логов"
    echo "  shell       Доступ к shell контейнера"
    echo "  exec <cmd>  Выполнение команды в контейнере"
    echo "  status      Статус контейнера"
    echo "  clean       Очистка Docker"
    echo ""
    echo "Специализированные команды:"
    echo "  gazebo      Запуск Gazebo симуляции"
    echo "  teleop      Запуск управления роботом"
    echo ""
    echo "Примеры использования:"
    echo "  ./manage.sh build && ./manage.sh up"
    echo "  ./manage.sh gazebo"
    echo "  ./manage.sh exec 'ros2 topic list'"
}

# ════════════════════════════════════════════════════════════
# ОСНОВНОЙ БЛОК
# ════════════════════════════════════════════════════════════

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    error "Docker не запущен. Пожалуйста, запустите Docker."
    exit 1
fi

# Parse command
case "${1:-help}" in
    build)
        cmd_build
        ;;
    up)
        cmd_up
        ;;
    down)
        cmd_down
        ;;
    restart)
        cmd_restart
        ;;
    logs)
        cmd_logs
        ;;
    shell)
        cmd_shell
        ;;
    exec)
        if [ -z "${2:-}" ]; then
            error "Укажите команду для выполнения"
            echo "Пример: ./manage.sh exec 'ros2 topic list'"
            exit 1
        fi
        shift
        cmd_exec "$@"
        ;;
    gazebo)
        cmd_gazebo
        ;;
    teleop)
        cmd_teleop
        ;;
    status)
        cmd_status
        ;;
    clean)
        cmd_clean
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        error "Неизвестная команда: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
