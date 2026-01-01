#!/bin/bash

# Build script for specific Docker stages
# Использование: ./build-stage.sh [stage-name]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="walking_robot_sim"

# Helper functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# Available stages
STAGES=(
    "base-system"
    "ros-core"
    "ros-control"
    "ros-simulation"
    "ros-navigation"
    "ros-vision"
    "ros-tools"
    "python-deps"
    "workspace"
    "final"
)

show_help() {
    echo "Docker Stage Build Script"
    echo ""
    echo "Доступные этапы:"
    for stage in "${STAGES[@]}"; do
        echo "  $stage"
    done
    echo ""
    echo "Использование:"
    echo "  $0 [stage-name]    - Сборка конкретного этапа"
    echo "  $0 all             - Сборка всех этапов"
    echo "  $0 list            - Показать доступные этапы"
    echo ""
    echo "Примеры:"
    echo "  $0 ros-core       - Сборка только ROS core пакетов"
    echo "  $0 ros-simulation - Сборка до этапа simulation"
    echo "  $0 final          - Полная сборка (по умолчанию)"
}

build_stage() {
    local stage=$1
    info "Сборка этапа: $stage"
    
    cd "$DOCKER_DIR"
    docker build \
        --target "$stage" \
        --tag "${IMAGE_NAME}:${stage}" \
        --tag "${IMAGE_NAME}:latest" \
        --cache-from "${IMAGE_NAME}:${stage}" \
        --cache-from "${IMAGE_NAME}:latest" \
        .
    
    success "Этап $stage собран"
}

build_all() {
    info "Сборка всех этапов..."
    
    cd "$DOCKER_DIR"
    docker build \
        --tag "${IMAGE_NAME}:latest" \
        --cache-from "${IMAGE_NAME}:base-system" \
        --cache-from "${IMAGE_NAME}:ros-core" \
        --cache-from "${IMAGE_NAME}:ros-control" \
        --cache-from "${IMAGE_NAME}:ros-simulation" \
        --cache-from "${IMAGE_NAME}:ros-navigation" \
        --cache-from "${IMAGE_NAME}:ros-vision" \
        --cache-from "${IMAGE_NAME}:ros-tools" \
        --cache-from "${IMAGE_NAME}:python-deps" \
        --cache-from "${IMAGE_NAME}:workspace" \
        --cache-from "${IMAGE_NAME}:latest" \
        .
    
    success "Все этапы собраны"
}

# Main logic
case "${1:-final}" in
    "all")
        build_all
        ;;
    "list")
        show_help
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        if [[ " ${STAGES[@]} " =~ " $1 " ]]; then
            build_stage "$1"
        else
            error "Неизвестный этап: $1"
            echo ""
            show_help
            exit 1
        fi
        ;;
esac
