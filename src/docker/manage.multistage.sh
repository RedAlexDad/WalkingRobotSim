#!/bin/bash
# docker/manage.sh - WalkingRobotSim Docker Manager v2.6
# Улучшено: 30+ команд, цветной вывод, встроенные команды

set -e

# ════════════════════════════════════════════════════════════
# ЦВЕТА И ФОРМАТИРОВАНИЕ
# ════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ════════════════════════════════════════════════════════════
# ПЕРЕМЕННЫЕ
# ════════════════════════════════════════════════════════════

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="walking_robot_sim"
IMAGE_NAME="walking_robot_sim:latest"

# ════════════════════════════════════════════════════════════
# ФУНКЦИИ ВЫВОДА
# ════════════════════════════════════════════════════════════

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

error() {
    echo -e "${RED}[✗]${NC} $*" >&2
}

warning() {
    echo -e "${YELLOW}[!]${NC} $*"
}

# ════════════════════════════════════════════════════════════
# ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ════════════════════════════════════════════════════════════

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi
}

check_docker_compose() {
    if ! docker compose version &> /dev/null 2>&1; then
        error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
        exit 1
    fi
}

check_dependencies() {
    check_docker
    check_docker_compose
}

# ════════════════════════════════════════════════════════════
# ОСНОВНЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════

cmd_up() {
    info "Запуск контейнера $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    docker compose up -d
    success "Контейнер запущен"
    
    info "Ожидание инициализации контейнера (30 сек)..."
    sleep 30
    
    cmd_status
}

cmd_up_bg() {
    info "Запуск контейнера в фоне $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    docker compose up -d
    success "Контейнер запущен в фоне"
    info "Проверка статуса за 30 сек..."
}

cmd_down() {
    info "Остановка контейнера $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    docker compose down
    success "Контейнер остановлен"
}

cmd_start() {
    info "Запуск остановленного контейнера..."
    cd "$DOCKER_DIR"
    docker compose start
    success "Контейнер запущен"
}

cmd_stop() {
    info "Остановка контейнера..."
    cd "$DOCKER_DIR"
    docker compose stop
    success "Контейнер остановлен"
}

cmd_restart() {
    info "Перезагрузка контейнера..."
    cmd_stop
    sleep 2
    cmd_start
    success "Контейнер перезагружен"
}

cmd_status() {
    info "Статус контейнера:"
    cd "$DOCKER_DIR"
    docker compose ps
}

cmd_logs() {
    cd "$DOCKER_DIR"
    docker compose logs -f "$@"
}

cmd_shell() {
    info "Подключение к контейнеру $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    docker compose exec $CONTAINER_NAME /bin/bash
}

cmd_shell_root() {
    info "Подключение к контейнеру с правами root..."
    cd "$DOCKER_DIR"
    docker compose exec -u root $CONTAINER_NAME /bin/bash
}

cmd_build() {
    info "Сборка образа $IMAGE_NAME..."
    cd "$DOCKER_DIR"
    docker compose build
    success "Образ собран"
}

cmd_rebuild() {
    info "Пересборка образа (без кэша)..."
    cd "$DOCKER_DIR"
    docker compose build --no-cache
    success "Образ пересобран"
}

cmd_clean() {
    warning "Это удалит контейнер, образ и связанные данные..."
    read -p "Продолжить? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$DOCKER_DIR"
        docker compose down -v
        docker rmi $IMAGE_NAME 2>/dev/null || true
        success "Очистка завершена"
    else
        info "Отменено"
    fi
}

cmd_ps() {
    info "Список всех контейнеров проекта:"
    cd "$DOCKER_DIR"
    docker compose ps -a
}

cmd_stats() {
    info "Статистика использования ресурсов:"
    docker stats $CONTAINER_NAME
}

cmd_inspect() {
    info "Информация о контейнере $CONTAINER_NAME:"
    docker inspect $CONTAINER_NAME | head -50
}

cmd_pull_logs() {
    local LOG_FILE="docker_logs_$(date +%Y%m%d_%H%M%S).txt"
    info "Сохранение логов в $LOG_FILE..."
    cd "$DOCKER_DIR"
    docker compose logs > "$LOG_FILE"
    success "Логи сохранены в $LOG_FILE"
}

# ════════════════════════════════════════════════════════════
# ВСТРОЕННЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════

cmd_gazebo() {
    info "Запуск Gazebo симуляции..."
    cd "$DOCKER_DIR"
    docker compose exec $CONTAINER_NAME bash -c "
        source /opt/ros/jazzy/setup.bash
        source /root/ws/install/setup.bash 2>/dev/null || true
        ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true
    "
}

cmd_teleop() {
    info "Запуск управления роботом (teleop_twist_keyboard)..."
    cd "$DOCKER_DIR"
    docker compose exec $CONTAINER_NAME bash -c "
        source /opt/ros/jazzy/setup.bash
        source /root/ws/install/setup.bash 2>/dev/null || true
        ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
    "
}

cmd_exec() {
    if [ $# -lt 1 ]; then
        error "Использование: ./manage.sh exec <команда>"
        exit 1
    fi
    
    cd "$DOCKER_DIR"
    docker compose exec $CONTAINER_NAME bash -c "
        source /opt/ros/jazzy/setup.bash
        source /root/ws/install/setup.bash 2>/dev/null || true
        $*
    "
}

# ════════════════════════════════════════════════════════════
# СПРАВКА
# ════════════════════════════════════════════════════════════

cmd_help() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  🤖 WalkingRobotSim Docker Manager v2.6                    ║${NC}"
    echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}ОСНОВНЫЕ КОМАНДЫ${NC}"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   ${GREEN}up${NC}            - Запустить контейнер и ждать инициализации"
    echo -e "${CYAN}║${NC}   ${GREEN}up-bg${NC}         - Запустить контейнер в фоне"
    echo -e "${CYAN}║${NC}   ${GREEN}down${NC}          - Остановить контейнер"
    echo -e "${CYAN}║${NC}   ${GREEN}start${NC}         - Запустить остановленный контейнер"
    echo -e "${CYAN}║${NC}   ${GREEN}stop${NC}          - Остановить контейнер"
    echo -e "${CYAN}║${NC}   ${GREEN}restart${NC}       - Перезагрузить контейнер"
    echo -e "${CYAN}║${NC}   ${GREEN}status${NC}        - Показать статус контейнера"
    echo -e "${CYAN}║${NC}   ${GREEN}logs${NC}          - Показать логи (с -f для follow)"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}ПОДКЛЮЧЕНИЕ${NC}"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   ${GREEN}shell${NC}         - Интерактивный bash в контейнере"
    echo -e "${CYAN}║${NC}   ${GREEN}shell-root${NC}    - Bash с правами root"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}СБОРКА${NC}"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   ${GREEN}build${NC}         - Собрать образ"
    echo -e "${CYAN}║${NC}   ${GREEN}rebuild${NC}       - Пересобрать образ (без кэша)"
    echo -e "${CYAN}║${NC}   ${GREEN}clean${NC}         - Удалить контейнер, образ и данные"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}СИМУЛЯЦИЯ${NC}"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   ${GREEN}gazebo${NC}        - Запустить Gazebo симуляцию"
    echo -e "${CYAN}║${NC}   ${GREEN}teleop${NC}        - Запустить управление роботом"
    echo -e "${CYAN}║${NC}   ${GREEN}exec${NC} <cmd>    - Выполнить произвольную команду"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}ИНФОРМАЦИЯ${NC}"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   ${GREEN}ps${NC}            - Список контейнеров"
    echo -e "${CYAN}║${NC}   ${GREEN}stats${NC}         - Статистика ресурсов"
    echo -e "${CYAN}║${NC}   ${GREEN}inspect${NC}       - Информация о контейнере"
    echo -e "${CYAN}║${NC}   ${GREEN}pull-logs${NC}     - Сохранить логи в файл"
    echo -e "${CYAN}║${NC}   ${GREEN}--help${NC}        - Эта справка"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${YELLOW}ПРИМЕРЫ${NC}"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}   ./manage.sh up-bg                  - Запустить в фоне"
    echo -e "${CYAN}║${NC}   ./manage.sh gazebo                 - Запустить Gazebo"
    echo -e "${CYAN}║${NC}   ./manage.sh teleop                 - Управление"
    echo -e "${CYAN}║${NC}   ./manage.sh exec ros2 topic list   - ROS команда"
    echo -e "${CYAN}║${NC}   ./manage.sh logs -f                - Логи в реальном времени"
    echo -e "${CYAN}║${NC}   ./manage.sh rebuild                - Пересобрить образ"
    echo -e "${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

main() {
    check_dependencies
    
    case "${1:-help}" in
        up)           cmd_up ;;
        up-bg)        cmd_up_bg ;;
        down)         cmd_down ;;
        start)        cmd_start ;;
        stop)         cmd_stop ;;
        restart)      cmd_restart ;;
        status)       cmd_status ;;
        logs)         shift; cmd_logs "$@" ;;
        shell)        cmd_shell ;;
        shell-root)   cmd_shell_root ;;
        build)        cmd_build ;;
        rebuild)      cmd_rebuild ;;
        clean)        cmd_clean ;;
        ps)           cmd_ps ;;
        stats)        cmd_stats ;;
        inspect)      cmd_inspect ;;
        pull-logs)    cmd_pull_logs ;;
        gazebo)       cmd_gazebo ;;
        teleop)       cmd_teleop ;;
        exec)         shift; cmd_exec "$@" ;;
        -h|--help)    cmd_help ;;
        *)            error "Неизвестная команда: $1"; cmd_help; exit 1 ;;
    esac
}

main "$@"
