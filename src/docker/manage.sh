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
ROS_DISTRO="jazzy"  # Фиксированная версия для Gazebo Harmonic

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
    docker exec -it $CONTAINER_NAME bash -c "
        echo 'alias sim=\"ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true\"' >> ~/.bashrc && 
        echo 'alias teleop=\"ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel\"' >> ~/.bashrc && 
        echo 'alias topics=\"ros2 topic list\"' >> ~/.bashrc && 
        echo 'alias nodes=\"ros2 node list\"' >> ~/.bashrc && 
        echo 'alias help=\"echo \\\"Доступные команды: sim, teleop, topics, nodes\\\"\"' >> ~/.bashrc && 
        source /opt/ros/jazzy/setup.bash && 
        source /root/ws/install/setup.bash && 
        export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\[\033[01;31m\](ROS Jazzy)\[\033[00m\]\$ ' && 
        echo '🤖 ROS Jazzy окружение настроено!' && 
        echo '🚀 Доступные команды:' && 
        echo '   sim          - Запуск Gazebo симуляции' && 
        echo '   teleop       - Управление роботом' && 
        echo '   topics       - Список топиков' && 
        echo '   nodes        - Список узлов' && 
        echo '   help         - Эта справка' && 
        echo '' && 
        echo '💡 Если алиасы не работают, используйте полные команды:' && 
        echo '   ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true' && 
        echo '   ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel' && 
        echo '   ros2 topic list' && 
        echo '   ros2 node list' && 
        source ~/.bashrc && 
        exec bash
    "
}

cmd_exec() {
    docker exec -it $CONTAINER_NAME bash -c "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash && $*"
}

cmd_test() {
    info "Проверка алиасов в контейнере..."
    docker exec -it $CONTAINER_NAME bash -c "
        source /opt/ros/jazzy/setup.bash && 
        source /root/ws/install/setup.bash && 
        source ~/.bashrc && 
        echo '🔍 Проверка алиасов:' && 
        alias topics && 
        echo '📋 Топики (первые 3):' && 
        topics | head -3 && 
        echo '✓ Алиасы работают!'
    "
}

# ════════════════════════════════════════════════════════════
# СПЕЦИАЛЬНЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════

cmd_gazebo() {
    info "Запуск Gazebo симуляции (ROS Jazzy + Gazebo Harmonic)..."
    docker exec -it $CONTAINER_NAME bash -c "
        source /opt/ros/${ROS_DISTRO}/setup.bash
        source /root/ws/install/setup.bash 2>/dev/null || true
        ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true
    "
}

cmd_teleop() {
    info "Запуск управления роботом (ROS Jazzy)..."
    docker exec -it $CONTAINER_NAME bash -c "
        source /opt/ros/${ROS_DISTRO}/setup.bash
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
    docker volume prune -f
    success "Очистка завершена"
}

cmd_backup() {
    local backup_file="walking_robot_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    info "Создание бэкапа: $backup_file"
    cd "$DOCKER_DIR"
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
        -v $(pwd):/backup alpine tar czf /backup/"$backup_file" \
        /var/lib/docker/volumes/gazebo_logs /var/lib/docker/volumes/gazebo_data
    success "Бэкап создан: $backup_file"
}

# ════════════════════════════════════════════════════════════
# ПОМОЩЬ
# ════════════════════════════════════════════════════════════

cmd_help() {
    echo "Walking Robot Simulation Manager - Simple Architecture v3.0"
    echo "Версия ROS: Jazzy (с Gazebo Harmonic)"
    echo ""
    echo "Основные команды:"
    echo "  build       Сборка Docker образа"
    echo "  up          Запуск контейнера"
    echo "  down        Остановка контейнера"
    echo "  restart     Перезапуск контейнера"
    echo "  logs        Просмотр логов"
    echo "  logs-save   Сохранение логов в файл"
    echo "  shell       Доступ к shell контейнера (с настроенным ROS)"
    echo "  exec <cmd>  Выполнение команды в контейнере (с настроенным ROS)"
    echo "  status      Статус контейнера"
    echo "  backup      Создание бэкапа данных"
    echo "  clean       Очистка Docker"
    echo ""
    echo "Специализированные команды:"
    echo "  gazebo      Запуск Gazebo симуляции"
    echo "  teleop      Запуск управления роботом"
    echo ""
    echo "Примеры использования:"
    echo "  ./manage.sh build && ./manage.sh up"
    echo "  ./manage.sh gazebo"
    echo "  ./manage.sh teleop"
    echo "  ./manage.sh exec 'ros2 topic list'"
    echo "  ./manage.sh logs-save"
    echo "  ./manage.sh backup"
    echo ""
    echo "Внутри контейнера (./manage.sh shell):"
    echo "  sim          - Запуск Gazebo симуляции"
    echo "  teleop       - Управление роботом"
    echo "  topics       - Список ROS топиков"
    echo "  nodes        - Список ROS узлов"
    echo "  help         - Справка по командам"
    echo ""
    echo "Технологии:"
    echo "  • ROS 2 Jazzy"
    echo "  • Gazebo Harmonic"
    echo "  • Docker + Docker Compose"
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
    logs-save)
        cmd_logs_save
        ;;
    shell)
        cmd_shell
        ;;
    test)
        cmd_test
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
    backup)
        cmd_backup
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
