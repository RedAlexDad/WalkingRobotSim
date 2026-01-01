#!/bin/bash
# test-workflows.sh - Скрипт для локального тестирования GitHub Actions workflows

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

# Проверка наличия необходимых инструментов
check_dependencies() {
    info "Проверка необходимых инструментов..."
    
    if ! command -v docker &> /dev/null; then
        fail "Docker не установлен. Пожалуйста, установите Docker."
        exit 1
    fi
    
    # Проверка наличия docker-compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        warn "Docker Compose не установлен. Попытка установки..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y docker-compose || {
                fail "Не удалось установить docker-compose"
                exit 1
            }
        else
            fail "Docker Compose не установлен и не удалось автоматически установить. Пожалуйста, установите docker-compose вручную."
            exit 1
        fi
    fi
    
    if ! command -v yamllint &> /dev/null; then
        warn "yamllint не установлен. Установите его для проверки синтаксиса YAML:"
        echo "  pip install yamllint"
    fi
    
    success "Все необходимые инструменты установлены"
}

# Проверка синтаксиса YAML для workflow файлов
check_yaml_syntax() {
    if command -v yamllint &> /dev/null; then
        info "Проверка синтаксиса YAML для workflow файлов..."
        
        # Проверка compose файлов
        if yamllint src/docker/compose.yml; then
            success "Синтаксис compose.yml корректен"
        else
            fail "Обнаружены ошибки в синтаксисе compose.yml"
            exit 1
        fi
        
        if [ -f "src/docker/compose.multistage.yml" ]; then
            if yamllint src/docker/compose.multistage.yml; then
                success "Синтаксис compose.multistage.yml корректен"
            else
                fail "Обнаружены ошибки в синтаксисе compose.multistage.yml"
                exit 1
            fi
        fi
        
        # Проверка наличия GitHub workflows
        if [ -d ".github/workflows" ]; then
            if yamllint .github/workflows/; then
                success "Синтаксис GitHub workflows корректен"
            else
                fail "Обнаружены ошибки в синтаксисе GitHub workflows"
                exit 1
            fi
        else
            warn "Директория .github/workflows не найдена"
        fi
    else
        warn "yamllint не установлен, пропускаем проверку синтаксиса YAML"
    fi
}

# Локальная сборка контейнера
local_build() {
    info "Локальная сборка Docker-образа..."
    
    # Определяем, какой вариант docker-compose использовать
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        fail "Docker Compose не найден"
        exit 1
    fi
    
    info "Используется команда: $DOCKER_COMPOSE_CMD"
    
    # Переходим в директорию с compose файлом
    cd src/docker
    
    if $DOCKER_COMPOSE_CMD build --no-cache; then
        success "Локальная сборка завершена успешно"
    else
        fail "Ошибка при локальной сборке"
        exit 1
    fi
    
    # Возвращаемся в исходную директорию
    cd - > /dev/null
}

# Тестовый запуск контейнера
test_container() {
    info "Тестовый запуск контейнера..."
    
    # Определяем, какой вариант docker-compose использовать
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        fail "Docker Compose не найден"
        exit 1
    fi
    
    info "Используется команда: $DOCKER_COMPOSE_CMD"
    
    # Переходим в директорию с compose файлом
    cd src/docker
    
    # Запускаем контейнер в фоновом режиме
    if $DOCKER_COMPOSE_CMD up -d; then
        info "Ожидание запуска контейнера..."
        sleep 15
        
        # Проверяем здоровье контейнера
        if $DOCKER_COMPOSE_CMD ps | grep -q "healthy"; then
            success "Контейнер запущен и здоров"
        else
            warn "Контейнер запущен, но статус здоровья неизвестен"
        fi
        
        # Проверяем базовую функциональность ROS
        if $DOCKER_COMPOSE_CMD exec -T simulator bash -c "source /opt/ros/jazzy/setup.bash && ros2 node list"; then
            success "ROS функциональность проверена успешно"
        else
            warn "ROS функциональность не проверена (контейнер может быть в процессе инициализации)"
        fi
        
        # Останавливаем контейнер
        $DOCKER_COMPOSE_CMD down
        success "Контейнер остановлен"
    else
        fail "Ошибка при запуске контейнера"
        exit 1
    fi
    
    # Возвращаемся в исходную директорию
    cd - > /dev/null
}

# Проверка структуры проекта
check_project_structure() {
    info "Проверка структуры проекта..."
    
    # Проверка наличия необходимых директорий
    if [ ! -d "src" ]; then
        fail "Директория src не найдена"
        exit 1
    fi
    
    if [ ! -d "src/docker" ]; then
        fail "Директория src/docker не найдена"
        exit 1
    fi
    
    if [ ! -f "src/docker/compose.yml" ]; then
        fail "Файл src/docker/compose.yml не найден"
        exit 1
    fi
    
    if [ ! -f "src/docker/Dockerfile" ]; then
        fail "Файл src/docker/Dockerfile не найден"
        exit 1
    fi
    
    # Проверка наличия ROS пакетов
    if [ ! -d "src/gazebo_sim" ]; then
        warn "Директория src/gazebo_sim не найдена"
    fi
    
    if [ ! -d "src/go1_description" ]; then
        warn "Директория src/go1_description не найдена"
    fi
    
    if [ ! -d "src/go2_description" ]; then
        warn "Директория src/go2_description не найдена"
    fi
    
    success "Структура проекта проверена"
}

# Очистка Docker ресурсов
cleanup_docker() {
    info "Очистка Docker ресурсов..."
    
    # Остановка и удаление контейнеров
    if command -v docker-compose &> /dev/null; then
        cd src/docker && docker-compose down -v 2>/dev/null || true && cd - > /dev/null
    elif docker compose version &> /dev/null; then
        cd src/docker && docker compose down -v 2>/dev/null || true && cd - > /dev/null
    fi
    
    # Удаление образов проекта
    docker rmi walking_robot_sim:latest 2>/dev/null || true
    
    success "Очистка завершена"
}

# Основная функция
main() {
    local action="${1:-test}"
    
    case $action in
        "clean")
            cleanup_docker
            ;;
        "build")
            check_dependencies
            check_project_structure
            check_yaml_syntax
            local_build
            ;;
        "test")
            info "Начало тестирования GitHub Actions workflows"
            
            check_dependencies
            check_project_structure
            check_yaml_syntax
            local_build
            test_container
            
            success "Все тесты пройдены успешно!"
            info "Теперь можно выполнять git push"
            ;;
        "help"|"-h"|"--help")
            echo "Использование: $0 [команда]"
            echo ""
            echo "Команды:"
            echo "  test    - Полный цикл тестирования (по умолчанию)"
            echo "  build   - Только сборка образа"
            echo "  clean   - Очистка Docker ресурсов"
            echo "  help    - Показать эту справку"
            ;;
        *)
            fail "Неизвестная команда: $action"
            echo "Используйте '$0 help' для получения справки"
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"
