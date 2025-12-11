#!/bin/bash
# docker-compose.sh — улучшенный скрипт управления Docker Compose для проекта Unitree ROS2 Simulation

set -e

# Имя проекта и контейнера
PROJECT_NAME="unitree_sim"
CONTAINER_NAME="unitree_sim"

# Цвета
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
MAGENTA='\033[1;35m'
NC='\033[0m' # No Color

# Префиксы для цветного вывода
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; }
highlight() { echo -e "${CYAN}[•]${NC} $1"; }
action() { echo -e "${MAGENTA}[ACTION]${NC} $1"; }

# Вывод справки
show_help() {
    echo -e "${CYAN}Улучшенный скрипт управления Docker Compose для Unitree ROS2 Simulation${NC}"
    echo
    echo "Использование:"
    echo "  ./docker-compose.sh [опции] <команда>"
    echo
    echo "Команды:"
    echo "  up        Запустить контейнер"
    echo "  down      Остановить и удалить контейнер"
    echo "  start     Запустить существующий контейнер"
    echo "  stop      Остановить контейнер"
    echo "  restart   Перезапустить контейнер"
    echo "  status    Показать статус контейнера"
    echo "  logs      Показать логи контейнера"
    echo "  exec      Выполнить команду в контейнере"
    echo "  build     Пересобрать образ"
    echo "  clean     Очистить неиспользуемые ресурсы Docker"
    echo
    echo "Опции:"
    echo "  --sudo    Использовать sudo для команд docker"
    echo "  --no-cache  Пересобрать без использования кэша (только для build)"
    echo "  --help    Показать эту справку"
    echo
    echo "Примеры:"
    echo "  ./docker-compose.sh up"
    echo "  ./docker-compose.sh --sudo down"
    echo "  ./docker-compose.sh build --no-cache"
    echo "  ./docker-compose.sh status"
}

# Проверка наличия docker-compose.yml
check_compose_file() {
    if [ ! -f "docker-compose.yml" ]; then
        fail "Файл docker-compose.yml не найден в текущей директории"
        exit 1
    fi
    info "Найден файл конфигурации: docker-compose.yml"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        fail "Docker не установлен или недоступен"
        exit 1
    fi
    info "Docker доступен"
}

# Проверка наличия Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        fail "Docker Compose не установлен или недоступен"
        exit 1
    fi
    # Определяем, какой вариант docker-compose использовать
    if command -v docker-compose &> /dev/null; then
        export DOCKER_COMPOSE_CMD="docker-compose"
    else
        export DOCKER_COMPOSE_CMD="docker compose"
    fi
    info "Используется команда: $DOCKER_COMPOSE_CMD"
}

# Очистка неиспользуемых ресурсов Docker
do_clean() {
    action "Очистка неиспользуемых ресурсов Docker..."
    $DOCKER_CMD system prune -f
    $DOCKER_CMD volume prune -f
    success "Неиспользуемые ресурсы Docker очищены"
}

# Обработка аргументов командной строки
ACTION=""
USE_SUDO=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --sudo)
            USE_SUDO=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        up|down|start|stop|restart|status|logs|exec|build|clean)
            ACTION="$1"
            shift
            ;;
        *)
            warn "Неизвестный аргумент: $1"
            show_help
            exit 1
            ;;
    esac
done

# Если команда не указана, показываем справку
if [ -z "$ACTION" ]; then
    show_help
    exit 1
fi

# Установка префикса sudo при необходимости
if [ "$USE_SUDO" = true ]; then
    DOCKER_CMD="sudo docker"
    DOCKER_COMPOSE="sudo $DOCKER_COMPOSE_CMD"
    info "Используется sudo для команд Docker"
else
    DOCKER_CMD="docker"
    DOCKER_COMPOSE="$DOCKER_COMPOSE_CMD"
    info "Запуск без sudo"
fi

# Проверки
check_docker
check_docker_compose
# Установка DOCKER_COMPOSE после проверки docker-compose
if [ "$USE_SUDO" = true ]; then
    DOCKER_COMPOSE="sudo $DOCKER_COMPOSE_CMD"
else
    DOCKER_COMPOSE="$DOCKER_COMPOSE_CMD"
fi
check_compose_file

# Функции управления контейнером
do_up() {
    action "Запуск контейнера $CONTAINER_NAME..."
    # Разрешение доступа к X-серверу
    info "Разрешение доступа к X-серверу (xhost)"
    xhost +local:root >/dev/null 2>&1 || true
    
    $DOCKER_COMPOSE up -d
    success "Контейнер $CONTAINER_NAME запущен в фоновом режиме"
    show_status
}

do_down() {
    action "Остановка и удаление контейнера $CONTAINER_NAME..."
    $DOCKER_COMPOSE down
    success "Контейнер $CONTAINER_NAME остановлен и удален"
}

do_start() {
    action "Запуск существующего контейнера $CONTAINER_NAME..."
    # Разрешение доступа к X-серверу
    info "Разрешение доступа к X-серверу (xhost)"
    xhost +local:root >/dev/null 2>&1 || true
    
    $DOCKER_COMPOSE start
    success "Контейнер $CONTAINER_NAME запущен"
    show_status
}

do_stop() {
    action "Остановка контейнера $CONTAINER_NAME..."
    $DOCKER_COMPOSE stop
    success "Контейнер $CONTAINER_NAME остановлен"
}

do_restart() {
    action "Перезапуск контейнера $CONTAINER_NAME..."
    # Разрешение доступа к X-серверу
    info "Разрешение доступа к X-серверу (xhost)"
    xhost +local:root >/dev/null 2>&1 || true
    
    $DOCKER_COMPOSE restart
    success "Контейнер $CONTAINER_NAME перезапущен"
    show_status
}

do_status() {
    show_status
}

show_status() {
    info "Проверка статуса контейнера $CONTAINER_NAME..."
    if $DOCKER_CMD ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        highlight "Контейнер $CONTAINER_NAME: ${GREEN}ЗАПУЩЕН${NC}"
        CONTAINER_ID=$($DOCKER_CMD ps -q -f name="$CONTAINER_NAME")
        info "ID контейнера: $CONTAINER_ID"
        $DOCKER_CMD ps -f name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    elif $DOCKER_CMD ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
        highlight "Контейнер $CONTAINER_NAME: ${YELLOW}ОСТАНОВЛЕН${NC}"
        $DOCKER_CMD ps -aq -f name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}"
    else
        highlight "Контейнер $CONTAINER_NAME: ${RED}НЕ НАЙДЕН${NC}"
    fi
}

do_logs() {
    action "Показ логов контейнера $CONTAINER_NAME..."
    $DOCKER_COMPOSE logs -f
}

do_exec() {
    action "Подключение к контейнеру $CONTAINER_NAME..."
    if $DOCKER_CMD ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        $DOCKER_CMD exec -it $CONTAINER_NAME bash
    else
        fail "Контейнер $CONTAINER_NAME не запущен"
        exit 1
    fi
}

do_build() {
    action "Пересборка образа..."
    if [ "$NO_CACHE" = true ]; then
        $DOCKER_COMPOSE build --no-cache
        success "Образ пересобран без использования кэша"
    else
        $DOCKER_COMPOSE build
        success "Образ пересобран"
    fi
}

# Выполнение выбранной команды
case $ACTION in
    up)
        do_up
        ;;
    down)
        do_down
        ;;
    start)
        do_start
        ;;
    stop)
        do_stop
        ;;
    restart)
        do_restart
        ;;
    status)
        do_status
        ;;
    logs)
        do_logs
        ;;
    exec)
        do_exec
        ;;
    build)
        do_build
        ;;
    clean)
        do_clean
        ;;
    *)
        fail "Неизвестная команда: $ACTION"
        show_help
        exit 1
        ;;
esac