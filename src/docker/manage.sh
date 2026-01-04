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
    info "Сборка Docker образа с кэшированием по этапам..."
    cd "$DOCKER_DIR"
    docker compose build
    success "Образ собран"
}

cmd_build_stage() {
    local stage=${2:-final}
    info "Сборка этапа: $stage"
    cd "$DOCKER_DIR"
    ./build-stage.sh "$stage"
}

cmd_up() {
    info "Запуск контейнера $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    docker compose up -d
    
    info "Ожидание инициализации ROS окружения..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec $CONTAINER_NAME bash -c "source /opt/ros/jazzy/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 node list" >/dev/null 2>&1; then
            success "ROS окружение готово (${attempt} сек)"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
        echo -n "."
    done
    
    if [ $attempt -eq $max_attempts ]; then
        warning "ROS окружение может быть не готово, но продолжаем..."
    fi
    
    echo ""
    info "Статус контейнера:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    
    success "Контейнер запущен"
}

cmd_down() {
    info "Остановка контейнера $CONTAINER_NAME..."
    cd "$DOCKER_DIR"
    
    # Сохраняем логи перед остановкой
    if docker ps --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
        info "Сохранение логов сессии..."
        local timestamp=$(date +%s)
        local hostname=$(hostname)
        local backup_folder="logs/gazebo_backup_${timestamp}_${hostname}"
        local gazebo_folder="logs/gazebo"
        
        # Создаем папку для бэкапа
        mkdir -p "$backup_folder"
        
        # Копируем логи ИЗ контейнера
        info "Копирование ROS логов из контейнера..."
        docker cp $CONTAINER_NAME:/root/ws/logs/. "$backup_folder/" 2>/dev/null || true
        
        # Объединяем дублирующиеся логи по типам
        info "Объединение логов по типам..."
        cd "$backup_folder"
        
        # Создаем папку для объединенных логов
        mkdir -p merged_logs
        
        # Объединяем логи по типам
        for pattern in "amcl" "behavior_server" "bt_navigator" "controller_server" "ekf_node" "gz sim server" "image_bridge" "lifecycle_manager" "map_server" "parameter_bridge" "planner_server" "python3" "robot_state_publisher" "rviz2" "smoother_server"; do
            # Находим все файлы по шаблону
            local files=$(ls ${pattern}_*.log 2>/dev/null || true)
            if [ -n "$files" ]; then
                # Создаем папку для этого типа логов
                mkdir -p "$pattern"
                
                # Объединяем все файлы типа в один с временной меткой
                local merged_file="merged_logs/${pattern}_combined.log"
                echo "=== Объединенные логи ${pattern} ===" > "$merged_file"
                echo "Время создания: $(date)" >> "$merged_file"
                echo "" >> "$merged_file"
                
                # Перемещаем оригинальные файлы в папку типа и добавляем в объединенный файл
                for file in $files; do
                    if [ -f "$file" ]; then
                        # Перемещаем файл в папку типа
                        mv "$file" "$pattern/"
                        
                        # Добавляем содержимое в объединенный файл
                        echo "" >> "$merged_file"
                        echo "=== Файл: $pattern/$(basename $file) ===" >> "$merged_file"
                        cat "$pattern/$(basename $file)" >> "$merged_file"
                        echo "" >> "$merged_file"
                    fi
                done
                
                echo "Объединен: $pattern ($(echo $files | wc -w) файлов, перемещены в папку $pattern/)"
            fi
        done
        
        # Копируем текущие логи gazebo если они есть
        if [ -d "../$gazebo_folder" ]; then
            info "Копирование Docker логов..."
            cp -r ../"$gazebo_folder"/* "./" 2>/dev/null || true
        fi
        
        # Сохраняем логи Docker контейнера
        docker compose logs --no-color > "docker_compose.log" 2>/dev/null || true
        
        # Создаем индексный файл
        echo "=== Логи сессии Walking Robot Simulator ===" > "session_info.log"
        echo "Время сохранения: $(date)" >> "session_info.log"
        echo "Тип: Остановка контейнера" >> "session_info.log"
        echo "Хост: $hostname" >> "session_info.log"
        echo "Контейнер: $CONTAINER_NAME" >> "session_info.log"
        echo "ROS версия: $(docker exec $CONTAINER_NAME ros2 --version 2>/dev/null | head -1 || echo 'N/A')" >> "session_info.log"
        echo "" >> "session_info.log"
        echo "Объединенные логи:" >> "session_info.log"
        ls -la merged_logs/ >> "session_info.log" 2>/dev/null || echo "Нет объединенных логов" >> "session_info.log"
        echo "" >> "session_info.log"
        echo "Все файлы:" >> "session_info.log"
        ls -la >> "session_info.log"
        
        # Возвращаемся в исходную папку
        cd "../.."
        
        # Полностью очищаем папку gazebo для следующей сессии с помощью Docker
        if [ -d "$gazebo_folder" ]; then
            info "Очистка папки gazebo для следующей сессии..."
            # Используем Docker для очистки, чтобы избежать sudo
            docker run --rm -v "$(pwd)/$gazebo_folder":/tmp/clean alpine sh -c "rm -rf /tmp/clean/*" 2>/dev/null || true
        fi
        
        # Создаем пустую папку gazebo для следующей сессии
        mkdir -p "$gazebo_folder"
        
        local file_count=$(find "$backup_folder" -type f 2>/dev/null | wc -l)
        local merged_count=$(find "$backup_folder/merged_logs" -type f 2>/dev/null | wc -l)
        success "Логи сохранены в: $backup_folder"
        echo "📁 Всего файлов: $file_count"
        echo "🔄 Объединенных логов: $merged_count"
        echo "📂 Проверьте объединенные логи в: $backup_folder/merged_logs/"
    fi
    
    docker compose down
    success "Контейнер остановлен"
}

cmd_deploy() {
    info "Сборка и запуск контейнера $CONTAINER_NAME..."
    cmd_build
    cmd_up
    success "Контейнер собран и запущен"
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
        echo 'alias help=\"echo \\\"Доступные команды: sim, teleop, topics, nodes, robot-walk, robot-up, robot-sit\\\"\"' >> ~/.bashrc && 
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
        ros2 launch gazebo_sim launch.launch.py use_sim_time:=true gui:=true
    "
    
    # После завершения симуляции сохраняем логи
    info "Симуляция завершена, сохранение логов..."
    cmd_save_gazebo_logs
}

cmd_gazebo_py() {
    info "Запуск Gazebo симуляции с Python контроллером..."
    docker exec -it $CONTAINER_NAME bash -c "
        source /opt/ros/${ROS_DISTRO}/setup.bash
        source /root/ws/install/setup.bash 2>/dev/null || true
        ros2 launch gazebo_sim launch_python.launch.py use_sim_time:=true gui:=true
    "
    
    # После завершения симуляции сохраняем логи
    info "Симуляция завершена, сохранение логов..."
    cmd_save_gazebo_logs
}

cmd_save_gazebo_logs() {
    cd "$DOCKER_DIR"
    
    # Проверяем что контейнер запущен
    if docker ps --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
        info "Сохранение логов сессии Gazebo..."
        local timestamp=$(date +%s)
        local hostname=$(hostname)
        local backup_folder="logs/gazebo_backup_${timestamp}_${hostname}"
        local gazebo_folder="logs/gazebo"
        
        # Создаем папку для бэкапа
        mkdir -p "$backup_folder"
        
        # Копируем логи ИЗ контейнера
        info "Копирование ROS логов из контейнера..."
        docker cp $CONTAINER_NAME:/root/ws/logs/. "$backup_folder/" 2>/dev/null || true
        
        # Объединяем дублирующиеся логи по типам
        info "Объединение логов по типам..."
        cd "$backup_folder"
        
        # Создаем папку для объединенных логов
        mkdir -p merged_logs
        
        # Объединяем логи по типам
        for pattern in "amcl" "behavior_server" "bt_navigator" "controller_server" "ekf_node" "gz sim server" "image_bridge" "lifecycle_manager" "map_server" "parameter_bridge" "planner_server" "python3" "robot_state_publisher" "rviz2" "smoother_server"; do
            # Находим все файлы по шаблону
            local files=$(ls ${pattern}_*.log 2>/dev/null || true)
            if [ -n "$files" ]; then
                # Создаем папку для этого типа логов
                mkdir -p "$pattern"
                
                # Объединяем все файлы типа в один с временной меткой
                local merged_file="merged_logs/${pattern}_combined.log"
                echo "=== Объединенные логи ${pattern} ===" > "$merged_file"
                echo "Время создания: $(date)" >> "$merged_file"
                echo "" >> "$merged_file"
                
                # Перемещаем оригинальные файлы в папку типа и добавляем в объединенный файл
                for file in $files; do
                    if [ -f "$file" ]; then
                        # Перемещаем файл в папку типа
                        mv "$file" "$pattern/"
                        
                        # Добавляем содержимое в объединенный файл
                        echo "" >> "$merged_file"
                        echo "=== Файл: $pattern/$(basename $file) ===" >> "$merged_file"
                        cat "$pattern/$(basename $file)" >> "$merged_file"
                        echo "" >> "$merged_file"
                    fi
                done
                
                echo "Объединен: $pattern ($(echo $files | wc -w) файлов, перемещены в папку $pattern/)"
            fi
        done
        
        # Копируем текущие логи gazebo если они есть
        if [ -d "../$gazebo_folder" ]; then
            info "Копирование Docker логов..."
            cp -r ../"$gazebo_folder"/* "./" 2>/dev/null || true
        fi
        
        # Сохраняем логи Docker контейнера
        docker compose logs --no-color > "docker_compose.log" 2>/dev/null || true
        
        # Создаем индексный файл
        echo "=== Логи сессии Walking Robot Simulator ===" > "session_info.log"
        echo "Время сохранения: $(date)" >> "session_info.log"
        echo "Тип: Gazebo симуляция" >> "session_info.log"
        echo "Хост: $hostname" >> "session_info.log"
        echo "Контейнер: $CONTAINER_NAME" >> "session_info.log"
        echo "ROS версия: $(docker exec $CONTAINER_NAME ros2 --version 2>/dev/null | head -1 || echo 'N/A')" >> "session_info.log"
        echo "" >> "session_info.log"
        echo "Объединенные логи:" >> "session_info.log"
        ls -la merged_logs/ >> "session_info.log" 2>/dev/null || echo "Нет объединенных логов" >> "session_info.log"
        echo "" >> "session_info.log"
        echo "Все файлы:" >> "session_info.log"
        ls -la >> "session_info.log"
        
        # Возвращаемся в исходную папку
        cd "../.."
        
        # Полностью очищаем папку gazebo для следующей сессии с помощью Docker
        if [ -d "$gazebo_folder" ]; then
            info "Очистка папки gazebo для следующей сессии..."
            # Используем Docker для очистки, чтобы избежать sudo
            docker run --rm -v "$(pwd)/$gazebo_folder":/tmp/clean alpine sh -c "rm -rf /tmp/clean/*" 2>/dev/null || true
        fi
        
        # Создаем пустую папку gazebo для следующей сессии
        mkdir -p "$gazebo_folder"
        
        local file_count=$(find "$backup_folder" -type f 2>/dev/null | wc -l)
        local merged_count=$(find "$backup_folder/merged_logs" -type f 2>/dev/null | wc -l)
        success "Логи Gazebo сохранены в: $backup_folder"
        echo "📁 Всего файлов: $file_count"
        echo "🔄 Объединенных логов: $merged_count"
        echo "📂 Проверьте объединенные логи в: $backup_folder/merged_logs/"
    else
        warning "Контейнер не запущен, логи не сохранены"
    fi
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

cmd_kill_ros() {
    info "Очистка всех ROS/Gazebo процессов..."
    
    # Проверяем что контейнер запущен
    if docker ps --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
        info "Убиваем ROS/Gazebo процессы в контейнере..."
        docker exec -it $CONTAINER_NAME bash -c "
            # Убиваем все процессы связанные с ROS
            pkill -f 'ros2\|gz sim\|rviz2\|gazebo' || true
            pkill -f 'robot_controller\|quadruped\|teleop' || true
            pkill -f 'python.*robot\|python.*controller' || true
            
            # Убиваем все процессы использующие ROS топики
            pkill -f '/robot1/' || true
            pkill -f 'cmd_vel\|joint_states\|imu_plugin' || true
            
            # Очищаем ROS мастер и демоны
            rm -f /tmp/ros* 2>/dev/null || true
            rm -f ~/.ros/* 2>/dev/null || true
            
            # Убиваем все gz процессы
            pkill -f 'gz-' || true
            pkill -f 'ign-' || true
            
            # Ожидаем завершения процессов
            sleep 2
            
            # Проверяем что процессы убиты
            if pgrep -f 'ros2\|gz sim\|rviz2' > /dev/null; then
                warning 'Некоторые ROS процессы все еще запущены'
                pgrep -f 'ros2\|gz sim\|rviz2' || true
            else
                success 'Все ROS/Gazebo процессы успешно остановлены'
            fi
        "
    else
        warning "Контейнер $CONTAINER_NAME не запущен"
    fi
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
    echo ""
    echo "Специализированные команды:"
    echo "  gazebo      Запуск Gazebo симуляции (C++ контроллер)"
    echo "  gazebo-py   Запуск Gazebo симуляции (Python контроллер)"
    echo "  teleop      Запуск управления роботом"
    echo "  kill-ros    Очистка всех ROS/Gazebo процессов"
    echo ""
    echo "Примеры использования:"
    echo "  ./manage.sh deploy                      # Сборка и запуск (рекомендуется)"
    echo "  ./manage.sh build && ./manage.sh up     # Отдельно сборка и запуск"
    echo "  ./manage.sh build-stage ros-core        # Сборка только ROS core"
    echo "  ./manage.sh build-stage ros-simulation  # Сборка до этапа simulation"
    echo "  ./manage.sh gazebo                      # Запуск с C++ контроллером"
    echo "  ./manage.sh gazebo-py                   # Запуск с Python контроллером"
    echo "  ./manage.sh teleop                      # Управление роботом"
    echo "  ./manage.sh kill-ros                    # Очистка процессов перед перезапуском"
    echo "  ./manage.sh exec 'ros2 topic list'      # Выполнение команды в контейнере"
    echo "  ./manage.sh backup                      # Создание бэкапа данных"
    echo ""
    echo "Доступные этапы сборки:"
    echo "  base-system     - Системные зависимости"
    echo "  ros-core        - ROS Core пакеты"
    echo "  ros-control     - ROS Control пакеты"
    echo "  ros-simulation  - Gazebo и simulation"
    echo "  ros-navigation  - Navigation пакеты"
    echo "  ros-vision      - Vision и sensor пакеты"
    echo "  ros-tools       - Tools и утилиты"
    echo "  python-deps     - Python зависимости"
    echo "  workspace       - Сборка workspace"
    echo "  final           - Финальный образ (по умолчанию)"
    echo ""
    echo "Внутри контейнера (./manage.sh shell):"
    echo "  sim             - Запуск Gazebo симуляции"
    echo "  teleop          - Управление роботом"
    echo "  topics          - Список ROS топиков"
    echo "  nodes           - Список ROS узлов"
    echo "  help            - Справка по командам"
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
    build-stage)
        cmd_build_stage "$@"
        ;;
    up)
        cmd_up
        ;;
    deploy)
        cmd_deploy
        ;;
    down)
        cmd_down
        ;;
    restart)
        cmd_restart
        ;;
    kill-ros)
        cmd_kill_ros
        ;;
    logs)
        cmd_logs
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
    gazebo-py)
        cmd_gazebo_py
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