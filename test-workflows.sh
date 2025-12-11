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
        if yamllint .github/workflows/; then
            success "Синтаксис YAML корректен"
        else
            fail "Обнаружены ошибки в синтаксисе YAML"
            exit 1
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
    
    if $DOCKER_COMPOSE_CMD build --no-cache --build-arg ROBOT_TYPE=Go2; then
        success "Локальная сборка завершена успешно"
    else
        fail "Ошибка при локальной сборке"
        exit 1
    fi
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
    
    if $DOCKER_COMPOSE_CMD up -d; then
        sleep 10
        if $DOCKER_COMPOSE_CMD exec -T unitree_sim echo "Container built successfully"; then
            success "Контейнер запущен успешно"
            $DOCKER_COMPOSE_CMD down
        else
            fail "Ошибка при запуске контейнера"
            $DOCKER_COMPOSE_CMD down
            exit 1
        fi
    else
        fail "Ошибка при запуске контейнера"
        exit 1
    fi
}

# Основная функция
main() {
    info "Начало тестирования GitHub Actions workflows"
    
    check_dependencies
    check_yaml_syntax
    local_build
    test_container
    
    success "Все тесты пройдены успешно!"
    info "Теперь можно выполнять git push"
}

# Запуск основной функции
main "$@"