# Walking Robot Simulation - Makefile
# Замена для всех .sh скриптов управления

SHELL := /bin/bash

# ════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ════════════════════════════════════════════════════════════

CONTAINER_NAME  := walking_robot_sim
IMAGE_NAME      := walking_robot_sim:latest
DOCKER_DIR      := $(CURDIR)/src/docker
PROJECT_ROOT    := $(CURDIR)
ROS_DISTRO      := jazzy
COMPOSE         := docker compose
COMPOSE_FILE    := $(DOCKER_DIR)/compose.yml

# ════════════════════════════════════════════════════════════
# ЦВЕТА
# ════════════════════════════════════════════════════════════

BLUE    := \033[0;34m
GREEN   := \033[0;32m
YELLOW  := \033[1;33m
RED     := \033[0;31m
CYAN    := \033[0;36m
BOLD    := \033[1m
NC      := \033[0m

# ════════════════════════════════════════════════════════════
# HELPER
# ════════════════════════════════════════════════════════════

# Проверка что контейнер запущен
define require-container
	@if ! docker ps --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Контейнер $(CONTAINER_NAME) не запущен.${NC}\n" >&2; \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Запустите: make deploy${NC}\n" >&2; \
		exit 1; \
	fi
endef

# Проверка и настройка X11 для GUI
define check-x11
	@if [ -z "$$DISPLAY" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}DISPLAY не установлен.${NC}\n" >&2; \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Установите: export DISPLAY=:0${NC}\n" >&2; \
		exit 1; \
	fi
	@xhost +local:root >/dev/null 2>&1 || true
	@xhost +local:$(USER) >/dev/null 2>&1 || true
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}X11 настроен: DISPLAY=$$DISPLAY${NC}\n"
endef

# ════════════════════════════════════════════════════════════
# ОСНОВНЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════

.PHONY: deploy build up up-bg down restart clean status logs shell benchmark

## Сборка и запуск контейнера (рекомендуется)
deploy: build up

## Сборка и запуск контейнера без кэша (решение проблем с cache_from)
deploy-no-cache: build-no-cache up

## Сборка Docker образа
build:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка Docker образа с кэшированием по этапам...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) --progress=auto build
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Образ собран${NC}\n"

## Сборка Docker образа без кэша (решает проблему с cache_from)
build-no-cache:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка Docker образа БЕЗ кэширования (решение проблем с cache_from)...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) --progress=auto build --no-cache
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Образ собран без кэша${NC}\n"

## Запуск контейнера
up:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск контейнера $(CONTAINER_NAME)...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) up -d
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Ожидание инициализации ROS окружения...${NC}\n"
	@attempt=0; \
	while [ $$attempt -lt 30 ]; do \
		if docker exec $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 node list" >/dev/null 2>&1; then \
			printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}ROS окружение готово ($${attempt} сек)${NC}\n"; \
			break; \
		fi; \
		attempt=$$((attempt + 1)); \
		sleep 1; \
		printf "."; \
	done; \
	if [ $$attempt -eq 30 ]; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}ROS окружение может быть не готово, но продолжаем...${NC}\n"; \
	fi
	@echo ""
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Статус контейнера:${NC}\n"
	@docker ps --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Контейнер запущен${NC}\n"

## Запуск контейнера в фоновом режиме (без ожидания ROS)
up-bg:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск контейнера $(CONTAINER_NAME) в фоновом режиме...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) up -d
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Контейнер запущен${NC}\n"

## Остановка контейнера с сохранением логов
down:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Остановка контейнера $(CONTAINER_NAME)...${NC}\n"
	@if docker ps --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сохранение логов сессии...${NC}\n"; \
		timestamp=$$(date +%s); \
		hostname=$$(hostname); \
		backup_folder="logs/gazebo_backup_$${timestamp}_$${hostname}"; \
		gazebo_folder="logs/gazebo"; \
		mkdir -p "$$backup_folder" 2>/dev/null || { \
			printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Не удалось создать $$backup_folder, используем /tmp/${NC}\n"; \
			backup_folder="/tmp/gazebo_backup_$${timestamp}_$${hostname}"; \
			mkdir -p "$$backup_folder"; \
		}; \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Копирование ROS логов из контейнера...${NC}\n"; \
		docker cp $(CONTAINER_NAME):/root/ws/logs/. "$$backup_folder/" 2>/dev/null || true; \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Объединение логов по типам...${NC}\n"; \
		cd "$$backup_folder" && \
		mkdir -p merged_logs && \
		for pattern in "amcl" "behavior_server" "bt_navigator" "controller_server" "ekf_node" "gz sim server" "image_bridge" "lifecycle_manager" "map_server" "parameter_bridge" "planner_server" "python3" "robot_state_publisher" "rviz2" "smoother_server"; do \
			files=$$(ls $${pattern}_*.log 2>/dev/null || true); \
			if [ -n "$$files" ]; then \
				mkdir -p "$$pattern"; \
				merged_file="merged_logs/$${pattern}_combined.log"; \
				echo "=== Объединенные логи $${pattern} ===" > "$$merged_file"; \
				echo "Время создания: $$(date)" >> "$$merged_file"; \
				echo "" >> "$$merged_file"; \
				for file in $$files; do \
					if [ -f "$$file" ]; then \
						mv "$$file" "$$pattern/"; \
						echo "" >> "$$merged_file"; \
						echo "=== Файл: $$pattern/$$(basename $$file) ===" >> "$$merged_file"; \
						cat "$$pattern/$$(basename $$file)" >> "$$merged_file"; \
						echo "" >> "$$merged_file"; \
					fi; \
				done; \
				echo "Объединен: $$pattern ($$(echo $$files | wc -w) файлов)"; \
			fi; \
		done && \
		if [ -d "../$$gazebo_folder" ]; then \
			cp -r ../"$$gazebo_folder"/* "./" 2>/dev/null || true; \
		fi && \
		$(COMPOSE) logs --no-color > "docker_compose.log" 2>/dev/null || true && \
		echo "=== Логи сессии Walking Robot Simulator ===" > "session_info.log" && \
		echo "Время: $$(date)" >> "session_info.log" && \
		echo "Хост: $$hostname" >> "session_info.log" && \
		echo "Контейнер: $(CONTAINER_NAME)" >> "session_info.log" && \
		cd "../.."; \
		if [ -d "$$gazebo_folder" ]; then \
			printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Очистка папки gazebo...${NC}\n"; \
			docker run --rm -v "$$(pwd)/$$gazebo_folder":/tmp/clean alpine sh -c "rm -rf /tmp/clean/*" 2>/dev/null || true; \
		fi; \
		mkdir -p "$$gazebo_folder"; \
		file_count=$$(find "$$backup_folder" -type f 2>/dev/null | wc -l); \
		merged_count=$$(find "$$backup_folder/merged_logs" -type f 2>/dev/null | wc -l); \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Логи сохранены: $$backup_folder${NC}\n"; \
		printf "📁 Всего файлов: $$file_count\n"; \
		printf "🔄 Объединенных логов: $$merged_count\n"; \
	fi
	@cd $(DOCKER_DIR) && $(COMPOSE) down
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Контейнер остановлен${NC}\n"

## Перезапуск контейнера
restart: down up

## Полная очистка Docker образов и контейнеров
clean:
	@printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Очистка Docker образов и контейнеров...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@docker volume prune -f
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Очистка завершена${NC}\n"

## Статус контейнера
status:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Статус контейнера:${NC}\n"
	@docker ps --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Использование ресурсов:${NC}\n"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" $(CONTAINER_NAME) 2>/dev/null || printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Контейнер не запущен${NC}\n"

## Просмотр логов контейнера
logs:
	@cd $(DOCKER_DIR) && $(COMPOSE) logs -f

## Подключение к контейнеру (shell)
shell:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Подключение к контейнеру $(CONTAINER_NAME)...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		echo 'alias sim=\"ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true\"' >> ~/.bashrc && \
		echo 'alias teleop=\"ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel\"' >> ~/.bashrc && \
		echo 'alias topics=\"ros2 topic list\"' >> ~/.bashrc && \
		echo 'alias nodes=\"ros2 node list\"' >> ~/.bashrc && \
		echo 'alias help=\"echo \\\"Доступные команды: sim, teleop, topics, nodes, robot-walk, robot-up, robot-sit\\\"\"' >> ~/.bashrc && \
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\[\033[01;31m\](ROS $(ROS_DISTRO))\[\033[00m\]\$$ ' && \
		printf '${GREEN}${BOLD}🤖${NC} ${GREEN}ROS $(ROS_DISTRO) окружение настроено!${NC}\n' && \
		printf '${CYAN}🚀 Доступные команды:${NC}\n' && \
		echo '   sim          - Запуск Gazebo симуляции' && \
		echo '   teleop       - Управление роботом' && \
		echo '   topics       - Список топиков' && \
		echo '   nodes        - Список узлов' && \
		echo '   help         - Эта справка' && \
		echo '' && \
		printf '${YELLOW}💡 Если алиасы не работают, используйте полные команды:${NC}\n' && \
		echo '   ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true' && \
		echo '   ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel' && \
		echo '   ros2 topic list' && \
		echo '   ros2 node list' && \
		source ~/.bashrc && \
		exec bash"

# ════════════════════════════════════════════════════════════
# СПЕЦИАЛЬНЫЕ КОМАНДЫ
# ════════════════════════════════════════════════════════════

.PHONY: gazebo gazebo-py gazebo-cpp teleop exec kill-ros test-aliases

## Запуск Gazebo симуляции (C++ контроллер)
gazebo:
	$(require-container)
	$(check-x11)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск Gazebo симуляции (ROS $(ROS_DISTRO) + Gazebo Harmonic)...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 launch gazebo_sim launch.launch.py use_sim_time:=true gui:=true"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Симуляция завершена, сохранение логов...${NC}\n"
	@$(MAKE) save-logs

## Запуск Gazebo симуляции с Python контроллером
gazebo-py:
	$(require-container)
	$(check-x11)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск Gazebo симуляции с Python контроллером...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 launch gazebo_sim launch_python.launch.py use_sim_time:=true gui:=true"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Симуляция завершена, сохранение логов...${NC}\n"
	@$(MAKE) save-logs

## Запуск Gazebo симуляции с C++ контроллером
gazebo-cpp:
	$(require-container)
	$(check-x11)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск Gazebo симуляции с C++ контроллером...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 launch gazebo_sim launch_cpp.launch.py use_sim_time:=true gui:=true"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Симуляция завершена, сохранение логов...${NC}\n"
	@$(MAKE) save-logs

## Запуск управления роботом (teleop)
teleop:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск управления роботом (ROS $(ROS_DISTRO))...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel"

## Установка положения робота в Gazebo (пример: make set-pose X=1.0 Y=0.0 Z=0.0 YAW=0.0)
set-pose:
	$(require-container)
	@if [ -z "$(X)" ] || [ -z "$(Y)" ] || [ -z "$(Z)" ] || [ -z "$(YAW)" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Укажите все параметры: X Y Z YAW${NC}\n"; \
		printf "Пример: make set-pose X=1.0 Y=0.0 Z=0.0 YAW=0.0\n"; \
		exit 1; \
	fi
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Установка положения робота: X=$(X) Y=$(Y) Z=$(Z) YAW=$(YAW)${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		gz service -s /world/default/set_pose \
			--reqtype gz.msgs.Pose \
			--reptype gz.msgs.Boolean \
			--timeout 1000 \
			--req \"name: 'go2', position: {x: $(X), y: $(Y), z: $(Z)}, orientation: {z: $(YAW)}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Положение установлено${NC}\n"

## Сброс положения робота в начало (0, 0, 0.5, 0)
reset-pose:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сброс положения робота в начало...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		gz service -s /world/default/set_pose \
			--reqtype gz.msgs.Pose \
			--reptype gz.msgs.Boolean \
			--timeout 1000 \
			--req \"name: 'go2', position: {x: 0, y: 0, z: 0.5}, orientation: {z: 0}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Положение сброшено${NC}\n"

# ════════════════════════════════════════════════════════════
# СОСТОЯНИЯ РОБОТА (behavior states)
# ════════════════════════════════════════════════════════════

.PHONY: rest trot crawl stand

## Перевести робота в режим REST (отдых)
rest:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Перевод робота в режим REST...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 topic pub --once /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand \"{mode: REST, robot_id: 1}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Режим REST установлен${NC}\n"

## Перевести робота в режим TROT (бег рысью)
trot:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Перевод робота в режим TROT...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 topic pub --once /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand \"{mode: TROT, robot_id: 1}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Режим TROT установлен${NC}\n"

## Перевести робота в режим CRAWL (ползание)
crawl:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Перевод робота в режим CRAWL...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 topic pub --once /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand \"{mode: CRAWL, robot_id: 1}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Режим CRAWL установлен${NC}\n"

## Перевести робота в режим STAND (стойка)
stand:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Перевод робота в режим STAND...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 topic pub --once /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand \"{mode: STAND, robot_id: 1}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Режим STAND установлен${NC}\n"

.PHONY: waypoint-start waypoint-clear waypoint-navigate waypoint-stop waypoint-resume waypoint-load

## Запустить навигацию по всем waypoints (сервис /start_navigation)
waypoint-start:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск навигации по waypoints...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 service call /start_navigation std_srvs/Trigger"
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Команда отправлена${NC}\n"

## Очистить все waypoints (сервис /clear_waypoints)
waypoint-clear:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Очистка waypoints...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 service call /clear_waypoints std_srvs/Trigger"
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Команда отправлена${NC}\n"

## Навигация к конкретному waypoint по индексу (пример: make waypoint-navigate INDEX=2)
waypoint-navigate:
	$(require-container)
	@if [ -z "$(INDEX)" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Укажите индекс: make waypoint-navigate INDEX=2${NC}\n"; \
		exit 1; \
	fi
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Навигация к waypoint $(INDEX)...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 service call /navigate_to_waypoint quadropted_msgs/srv/WaypointNavigate \"{index: $(INDEX)}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Команда отправлена${NC}\n"

## Остановить текущую навигацию (сервис /stop_navigation)
waypoint-stop:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Остановка навигации...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 service call /stop_navigation std_srvs/Trigger"
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Команда отправлена${NC}\n"

## Продолжить навигацию с прерванного waypoint (сервис /resume_navigation)
waypoint-resume:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Продолжение навигации...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 service call /resume_navigation std_srvs/Trigger"
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Команда отправлена${NC}\n"

## Загрузить waypoints из JSON-файла (пример: make waypoint-load FILE=test.json)
waypoint-load:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Загрузка waypoints..."
ifneq ($(FILE),)
	@printf " из $(FILE)...${NC}\n"
else
	@printf " (по умолчанию)...${NC}\n"
endif
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 service call /load_waypoints quadropted_msgs/srv/LoadWaypoints \"{file_path: '$(FILE)'}\""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Команда отправлена${NC}\n"

## Выполнение команды в контейнере (пример: make exec CMD="ros2 topic list")
exec:
	$(require-container)
	@if [ -z "$(CMD)" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Укажите команду для выполнения${NC}\n"; \
		printf "Пример: make exec CMD='ros2 topic list'\n"; \
		exit 1; \
	fi
	@docker exec -it $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash && source /root/ws/install/setup.bash && $(CMD)"

## Проверка алиасов в контейнере
test-aliases:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка алиасов в контейнере...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		source ~/.bashrc && \
		echo '🔍 Проверка алиасов:' && \
		alias topics && \
		echo '📋 Топики (первые 3):' && \
		topics | head -3 && \
		echo '✓ Алиасы работают!'"

## Очистка всех ROS/Gazebo процессов в контейнере
kill-ros:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Очистка всех ROS/Gazebo процессов...${NC}\n"
	@if docker ps --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Убиваем ROS/Gazebo процессы в контейнере...${NC}\n"; \
		docker exec -it $(CONTAINER_NAME) bash -c "\
			pkill -f 'ros2\|gz sim\|rviz2\|gazebo' || true; \
			pkill -f 'robot_controller\|quadruped\|teleop' || true; \
			pkill -f 'python.*robot\|python.*controller' || true; \
			pkill -f '/robot1/' || true; \
			pkill -f 'cmd_vel\|joint_states\|imu_plugin' || true; \
			rm -f /tmp/ros* 2>/dev/null || true; \
			rm -f ~/.ros/* 2>/dev/null || true; \
			pkill -f 'gz-' || true; \
			pkill -f 'ign-' || true; \
			sleep 2; \
			if pgrep -f 'ros2\|gz sim\|rviz2' > /dev/null; then \
				printf '${YELLOW}${BOLD}[!]${NC} ${YELLOW}Некоторые ROS процессы все еще запущены${NC}\n'; \
				pgrep -f 'ros2\|gz sim\|rviz2' || true; \
			else \
				printf '${GREEN}${BOLD}[✓]${NC} ${GREEN}Все ROS/Gazebo процессы успешно остановлены${NC}\n'; \
			fi"; \
	else \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Контейнер $(CONTAINER_NAME) не запущен${NC}\n"; \
	fi

# ════════════════════════════════════════════════════════════
# СБОРКА ПО ЭТАПАМ
# ════════════════════════════════════════════════════════════

.PHONY: build-stage build-stage-list

## Сборка конкретного этапа Docker (пример: make build-stage STAGE=ros-core)
build-stage:
	@if [ -z "$(STAGE)" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Укажите этап: make build-stage STAGE=<stage>${NC}\n"; \
		echo "Доступные этапы: base-system ros-core ros-control ros-simulation ros-navigation ros-vision ros-tools python-deps workspace final"; \
		exit 1; \
	fi
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка этапа: $(STAGE)${NC}\n"
	@cd $(DOCKER_DIR) && docker build \
		--target $(STAGE) \
		--tag walking_robot_sim:$(STAGE) \
		--tag walking_robot_sim:latest \
		--cache-from walking_robot_sim:$(STAGE) \
		--cache-from walking_robot_sim:latest \
		.
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Этап $(STAGE) собран${NC}\n"

## Показать доступные этапы сборки
build-stage-list:
	@printf "${CYAN}Доступные этапы сборки:${NC}\n"
	@printf "  ${BOLD}base-system${NC}     - Системные зависимости\n"
	@printf "  ${BOLD}ros-core${NC}        - ROS Core пакеты\n"
	@printf "  ${BOLD}ros-control${NC}     - ROS Control пакеты\n"
	@printf "  ${BOLD}ros-simulation${NC}  - Gazebo и simulation\n"
	@printf "  ${BOLD}ros-navigation${NC}  - Navigation пакеты\n"
	@printf "  ${BOLD}ros-vision${NC}      - Vision и sensor пакеты\n"
	@printf "  ${BOLD}ros-tools${NC}       - Tools и утилиты\n"
	@printf "  ${BOLD}python-deps${NC}     - Python зависимости\n"
	@printf "  ${BOLD}workspace${NC}       - Сборка workspace\n"
	@printf "  ${BOLD}final${NC}           - Финальный образ (по умолчанию)\n"

# ════════════════════════════════════════════════════════════
# СОХРАНЕНИЕ ЛОГОВ
# ════════════════════════════════════════════════════════════

.PHONY: save-logs

## Сохранение логов Gazebo сессии
save-logs:
	@if docker ps --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сохранение логов сессии Gazebo...${NC}\n"; \
		timestamp=$$(date +%s); \
		hostname=$$(hostname); \
		backup_folder="logs/gazebo_backup_$${timestamp}_$${hostname}"; \
		gazebo_folder="logs/gazebo"; \
		mkdir -p "$$backup_folder" 2>/dev/null || { \
			printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Не удалось создать $$backup_folder, используем /tmp/${NC}\n"; \
			backup_folder="/tmp/gazebo_backup_$${timestamp}_$${hostname}"; \
			mkdir -p "$$backup_folder"; \
		}; \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Копирование ROS логов из контейнера...${NC}\n"; \
		docker cp $(CONTAINER_NAME):/root/ws/logs/. "$$backup_folder/" 2>/dev/null || true; \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Объединение логов по типам...${NC}\n"; \
		cd "$$backup_folder" && \
		mkdir -p merged_logs && \
		for pattern in "amcl" "behavior_server" "bt_navigator" "controller_server" "ekf_node" "gz sim server" "image_bridge" "lifecycle_manager" "map_server" "parameter_bridge" "planner_server" "python3" "robot_state_publisher" "rviz2" "smoother_server"; do \
			files=$$(ls $${pattern}_*.log 2>/dev/null || true); \
			if [ -n "$$files" ]; then \
				mkdir -p "$$pattern"; \
				merged_file="merged_logs/$${pattern}_combined.log"; \
				echo "=== Объединенные логи $${pattern} ===" > "$$merged_file"; \
				echo "Время: $$(date)" >> "$$merged_file"; \
				echo "" >> "$$merged_file"; \
				for file in $$files; do \
					if [ -f "$$file" ]; then \
						mv "$$file" "$$pattern/"; \
						echo "" >> "$$merged_file"; \
						echo "=== Файл: $$pattern/$$(basename $$file) ===" >> "$$merged_file"; \
						cat "$$pattern/$$(basename $$file)" >> "$$merged_file"; \
						echo "" >> "$$merged_file"; \
					fi; \
				done; \
				echo "Объединен: $$pattern ($$(echo $$files | wc -w) файлов)"; \
			fi; \
		done && \
		if [ -d "../$$gazebo_folder" ]; then \
			cp -r ../"$$gazebo_folder"/* "./" 2>/dev/null || true; \
		fi && \
		cd $(DOCKER_DIR) && $(COMPOSE) logs --no-color > "$$backup_folder/docker_compose.log" 2>/dev/null || true && \
		echo "=== Логи сессии Walking Robot Simulator ===" > "$$backup_folder/session_info.log" && \
		echo "Время: $$(date)" >> "$$backup_folder/session_info.log" && \
		echo "Тип: Gazebo симуляция" >> "$$backup_folder/session_info.log" && \
		echo "Хост: $$hostname" >> "$$backup_folder/session_info.log" && \
		echo "Контейнер: $(CONTAINER_NAME)" >> "$$backup_folder/session_info.log" && \
		cd "$(PROJECT_ROOT)"; \
		if [ -d "$$gazebo_folder" ]; then \
			printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Очистка папки gazebo...${NC}\n"; \
			docker run --rm -v "$$(pwd)/$$gazebo_folder":/tmp/clean alpine sh -c "rm -rf /tmp/clean/*" 2>/dev/null || true; \
		fi; \
		mkdir -p "$$gazebo_folder"; \
		file_count=$$(find "$$backup_folder" -type f 2>/dev/null | wc -l); \
		merged_count=$$(find "$$backup_folder/merged_logs" -type f 2>/dev/null | wc -l); \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Логи сохранены: $$backup_folder${NC}\n"; \
		printf "📁 Всего файлов: $$file_count\n"; \
		printf "🔄 Объединенных логов: $$merged_count\n"; \
		printf "📂 Проверьте: $$backup_folder/merged_logs/\n"; \
	else \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Контейнер не запущен, логи не сохранены${NC}\n"; \
	fi

# ════════════════════════════════════════════════════════════
# SETUP И ПРОВЕРКИ
# ════════════════════════════════════════════════════════════

.PHONY: setup check-x11 backup

## Начальная настройка проекта
setup: check-x11
	@echo ""
	@printf "${CYAN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}\n"
	@printf "${CYAN}${BOLD}║${NC}  🤖 ${BOLD}WalkingRobotSim - Setup${NC}                               ${CYAN}${BOLD}║${NC}\n"
	@printf "${CYAN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}\n"
	@echo ""
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка Docker...${NC}\n"
	@if ! command -v docker &> /dev/null; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Docker не установлен${NC}\n"; \
		echo "Установите Docker: https://docs.docker.com/get-docker/"; \
		exit 1; \
	fi
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Docker найден: $$(docker --version)${NC}\n"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка Docker Compose...${NC}\n"
	@if ! docker compose version &> /dev/null 2>&1; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Docker Compose не установлен${NC}\n"; \
		echo "Установите Docker Compose: https://docs.docker.com/compose/install/"; \
		exit 1; \
	fi
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Docker Compose найден: $$(docker compose version --short)${NC}\n"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка структуры проекта...${NC}\n"
	@for file in "docker/Dockerfile" "docker/compose.yml" "docker/cyclonedds.xml"; do \
		if [ ! -f "$(PROJECT_ROOT)/src/$$file" ]; then \
			printf "${RED}${BOLD}[✗]${NC} ${RED}Файл не найден: $$file${NC}\n"; \
			exit 1; \
		fi; \
	done
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Структура проекта верна${NC}\n"
	@echo ""
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Информация о системе:${NC}\n"
	@printf "  OS: $$(uname -s)\n"
	@printf "  Kernel: $$(uname -r)\n"
	@printf "  Docker: $$(docker --version)\n"
	@printf "  Compose: $$(docker compose version --short)\n"
	@printf "  User: $$(whoami)\n"
	@printf "  Home: $$HOME\n"
	@echo ""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}✅ Инициализация завершена успешно!${NC}\n"
	@echo ""
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Следующие шаги:${NC}\n"
	@printf "  1. ${BOLD}make deploy${NC}              # Сборка и запуск\n"
	@printf "  2. ${BOLD}make gazebo${NC}              # Запуск Gazebo\n"
	@printf "  3. ${BOLD}make teleop${NC}              # Управление роботом (в другом терминале)\n"
	@echo ""

## Проверка X11 (для GUI)
check-x11:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка X11 (для GUI)...${NC}\n"
	@if [ -z "$$DISPLAY" ]; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}DISPLAY не установлен. X11 GUI может не работать.${NC}\n"; \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Для использования GUI установите DISPLAY:${NC}\n"; \
		echo "  export DISPLAY=:0"; \
		echo "  xhost +local:"; \
	else \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}DISPLAY установлен: $$DISPLAY${NC}\n"; \
	fi

## Создание бэкапа данных
backup:
	@backup_file="walking_robot_backup_$$(date +%Y%m%d_%H%M%S).tar.gz"; \
	printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Создание бэкапа: $$backup_file${NC}\n"; \
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(DOCKER_DIR):/backup alpine tar czf /backup/"$$backup_file" \
		/var/lib/docker/volumes/gazebo_logs /var/lib/docker/volumes/gazebo_data 2>/dev/null || true; \
	printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Бэкап создан: $$backup_file${NC}\n"

# ════════════════════════════════════════════════════════════
# ТЕСТЫ
# ════════════════════════════════════════════════════════════

.PHONY: test test-build test-container test-clean

## Полный цикл тестирования
test: check-deps check-structure test-yaml test-build test-container
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Все тесты пройдены успешно!${NC}\n"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Теперь можно выполнять git push${NC}\n"

## Только сборка образа для теста
test-build: check-deps check-structure test-yaml
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Локальная сборка Docker-образа...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) build --no-cache
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Локальная сборка завершена успешно${NC}\n"

## Тестовый запуск контейнера
test-container:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Тестовый запуск контейнера...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) up -d
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Ожидание запуска контейнера...${NC}\n"
	@sleep 15
	@if $(COMPOSE) ps | grep -q "healthy"; then \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Контейнер запущен и здоров${NC}\n"; \
	else \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Контейнер запущен, но статус здоровья неизвестен${NC}\n"; \
	fi
	@if $(COMPOSE) exec -T simulator bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash && ros2 node list"; then \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}ROS функциональность проверена успешно${NC}\n"; \
	else \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}ROS функциональность не проверена (контейнер может быть в процессе инициализации)${NC}\n"; \
	fi
	@cd $(DOCKER_DIR) && $(COMPOSE) down
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Контейнер остановлен${NC}\n"

## Очистка Docker ресурсов после тестов
test-clean:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Очистка Docker ресурсов...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) down -v 2>/dev/null || true
	@docker rmi walking_robot_sim:latest 2>/dev/null || true
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Очистка завершена${NC}\n"

## Проверка зависимостей
check-deps:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка необходимых инструментов...${NC}\n"
	@if ! command -v docker &> /dev/null; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Docker не установлен. Пожалуйста, установите Docker.${NC}\n"; \
		exit 1; \
	fi
	@if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Docker Compose не установлен.${NC}\n"; \
		exit 1; \
	fi
	@if ! command -v yamllint &> /dev/null; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}yamllint не установлен. Установите: pip install yamllint${NC}\n"; \
	fi
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Все необходимые инструменты установлены${NC}\n"

## Проверка структуры проекта
check-structure:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка структуры проекта...${NC}\n"
	@if [ ! -d "$(PROJECT_ROOT)/src" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Директория src не найдена${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/docker" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Директория src/docker не найдена${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_ROOT)/src/docker/compose.yml" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Файл src/docker/compose.yml не найден${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_ROOT)/src/docker/Dockerfile" ]; then \
		printf "${RED}${BOLD}[✗]${NC} ${RED}Файл src/docker/Dockerfile не найден${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/gazebo_sim" ]; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Директория src/gazebo_sim не найдена${NC}\n"; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/go1_description" ]; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Директория src/go1_description не найдена${NC}\n"; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/go2_description" ]; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Директория src/go2_description не найдена${NC}\n"; \
	fi
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Структура проекта проверена${NC}\n"

## Проверка синтаксиса YAML
test-yaml:
	@if command -v yamllint &> /dev/null; then \
		printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Проверка синтаксиса YAML...${NC}\n"; \
		if yamllint $(DOCKER_DIR)/compose.yml; then \
			printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Синтаксис compose.yml корректен${NC}\n"; \
		else \
			printf "${RED}${BOLD}[✗]${NC} ${RED}Обнаружены ошибки в синтаксисе compose.yml${NC}\n"; \
			exit 1; \
		fi; \
		if [ -f "$(DOCKER_DIR)/compose.multistage.yml" ]; then \
			if yamllint $(DOCKER_DIR)/compose.multistage.yml; then \
				printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Синтаксис compose.multistage.yml корректен${NC}\n"; \
			else \
				printf "${RED}${BOLD}[✗]${NC} ${RED}Обнаружены ошибки в синтаксисе compose.multistage.yml${NC}\n"; \
				exit 1; \
			fi; \
		fi; \
		if [ -d "$(PROJECT_ROOT)/.github/workflows" ]; then \
			if yamllint $(PROJECT_ROOT)/.github/workflows/; then \
				printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Синтаксис GitHub workflows корректен${NC}\n"; \
			else \
				printf "${RED}${BOLD}[✗]${NC} ${RED}Обнаружены ошибки в синтаксисе GitHub workflows${NC}\n"; \
				exit 1; \
			fi; \
		else \
			printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Директория .github/workflows не найдена${NC}\n"; \
		fi; \
	else \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}yamllint не установлен, пропускаем проверку YAML${NC}\n"; \
	fi

# ════════════════════════════════════════════════════════════
# ПОМОЩЬ
# ════════════════════════════════════════════════════════════

.PHONY: help

## Показать справку
help:
	@echo ""
	@printf "${CYAN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}\n"
	@printf "${CYAN}${BOLD}║${NC}  🤖 ${BOLD}Walking Robot Simulation Manager v3.0${NC}                  ${CYAN}${BOLD}║${NC}\n"
	@printf "${CYAN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}\n"
	@echo ""
	@printf "${BOLD}Специализированные команды:${NC}\n"
	@printf "  ${GREEN}${BOLD}make gazebo${NC}         Запуск Gazebo симуляции (C++ контроллер)\n"
	@printf "  ${GREEN}${BOLD}make gazebo-py${NC}      Запуск Gazebo симуляции (Python контроллер)\n"
	@printf "  ${GREEN}${BOLD}make gazebo-cpp${NC}     Запуск Gazebo симуляции (C++ контроллер)\n"
	@printf "  ${GREEN}${BOLD}make teleop${NC}         Запуск управления роботом\n"
	@printf "  ${GREEN}${BOLD}make kill-ros${NC}       Очистка всех ROS/Gazebo процессов\n"
	@echo ""
	@printf "${BOLD}Основные команды:${NC}\n"
	@printf "  ${GREEN}${BOLD}make deploy${NC}         Сборка и запуск (рекомендуется)\n"
	@printf "  ${GREEN}${BOLD}make build${NC}          Сборка Docker образа\n"
	@printf "  ${GREEN}${BOLD}make up${NC}             Запуск контейнера\n"
	@printf "  ${GREEN}${BOLD}make up-bg${NC}          Запуск контейнера в фоне (без ожидания ROS)\n"
	@printf "  ${GREEN}${BOLD}make down${NC}           Остановка контейнера с сохранением логов\n"
	@printf "  ${GREEN}${BOLD}make restart${NC}        Перезапуск контейнера\n"
	@printf "  ${GREEN}${BOLD}make clean${NC}          Полная очистка Docker ресурсов\n"
	@printf "  ${GREEN}${BOLD}make status${NC}         Статус контейнера\n"
	@printf "  ${GREEN}${BOLD}make logs${NC}           Просмотр логов\n"
	@printf "  ${GREEN}${BOLD}make shell${NC}          Подключение к контейнеру\n"
	@echo ""
	@printf "${BOLD}Сборка по этапам:${NC}\n"
	@printf "  ${GREEN}${BOLD}make build-stage STAGE=ros-core${NC}   Сборка конкретного этапа\n"
	@printf "  ${GREEN}${BOLD}make build-stage-list${NC}             Показать доступные этапы\n"
	@echo ""
	@printf "${BOLD}Выполнение команд:${NC}\n"
	@printf "  ${GREEN}${BOLD}make exec CMD='ros2 topic list'${NC}   Выполнение команды в контейнере\n"
	@echo ""
	@printf "${BOLD}Состояния робота:${NC}\n"
	@printf "  ${GREEN}${BOLD}make rest${NC}           Режим отдыха (REST)\n"
	@printf "  ${GREEN}${BOLD}make stand${NC}          Режим стойки (STAND)\n"
	@printf "  ${GREEN}${BOLD}make trot${NC}           Режим бега рысью (TROT)\n"
	@printf "  ${GREEN}${BOLD}make crawl${NC}          Режим ползания (CRAWL)\n"
	@echo ""
	@printf "${BOLD}Waypoint навигация:${NC}\n"
	@printf "  ${GREEN}${BOLD}make waypoint-start${NC}               Запуск навигации по всем waypoints\n"
	@printf "  ${GREEN}${BOLD}make waypoint-navigate INDEX=2${NC}    Навигация к конкретному waypoint\n"
	@printf "  ${GREEN}${BOLD}make waypoint-stop${NC}                Остановка текущей навигации\n"
	@printf "  ${GREEN}${BOLD}make waypoint-resume${NC}              Продолжить навигацию с прерванного waypoint\n"
	@printf "  ${GREEN}${BOLD}make waypoint-load FILE=wp.json${NC}   Загрузить waypoints из JSON-файла\n"
	@printf "  ${GREEN}${BOLD}make waypoint-clear${NC}               Очистка waypoints и остановка\n"
	@echo ""
	@printf "${BOLD}Положение робота:${NC}\n"
	@printf "  ${GREEN}${BOLD}make set-pose X=1.0 Y=0.0 Z=0.0 YAW=0.0${NC}   Установка положения\n"
	@printf "  ${GREEN}${BOLD}make reset-pose${NC}                           Сброс положения в начало\n"
	@echo ""
	@printf "${BOLD}Тестирование:${NC}\n"
	@printf "  ${GREEN}${BOLD}make test${NC}             Полный цикл тестирования\n"
	@printf "  ${GREEN}${BOLD}make test-build${NC}       Только сборка образа\n"
	@printf "  ${GREEN}${BOLD}make test-container${NC}   Тестовый запуск контейнера\n"
	@printf "  ${GREEN}${BOLD}make test-clean${NC}       Очистка после тестов\n"
	@echo ""
	@printf "${BOLD}Тесты корректности и производительности:${NC}\n"
	@printf "  ${GREEN}${BOLD}make test-correctness${NC}    Запуск тестов корректности\n"
	@printf "  ${GREEN}${BOLD}make test-benchmark${NC}	   Замер производительности Python\n"
	@printf "  ${GREEN}${BOLD}make benchmark${NC}           Запуск бенчмарка Python + C++ с таблицей\n"
	@printf "  ${GREEN}${BOLD}make benchmark-python${NC}    Только Python бенчмарк\n"
	@printf "  ${GREEN}${BOLD}make benchmark-cpp${NC}       Только C++ бенчмарк\n"
	@echo ""
	@printf "${BOLD}Прочее:${NC}\n"
	@printf "  ${GREEN}${BOLD}make setup${NC}            Начальная настройка проекта\n"
	@printf "  ${GREEN}${BOLD}make backup${NC}           Создание бэкапа данных\n"
	@printf "  ${GREEN}${BOLD}make save-logs${NC}        Сохранение логов Gazebo сессии\n"
	@printf "  ${GREEN}${BOLD}make help${NC}             Эта справка\n"
	@echo ""
	@printf "${BOLD}Технологии:${NC}\n"
	@printf "  • ROS 2 ${BOLD}$(ROS_DISTRO)${NC}\n"
	@printf "  • Gazebo Harmonic\n"
	@printf "  • Docker + Docker Compose\n"
	@echo ""

# ════════════════════════════════════════════════════════════
# ТЕСТЫ
# ════════════════════════════════════════════════════════════

.PHONY: test-correctness test-benchmark benchmark benchmark-python benchmark-cpp

## Проверка корректности — запуск всех тестов в correctness/
test-correctness:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Тесты корректности...${NC}\n"
	@cd $(PROJECT_ROOT)/src/tests/correctness && python3 run_all.py
	@echo ""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Тесты корректности завершены${NC}\n"

## Benchmark производительности — замер времени
test-benchmark:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Benchmark производительности...${NC}\n"
	@cd $(PROJECT_ROOT) && python3 src/tests/benchmark_performance.py
	@echo ""
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Benchmark завершён${NC}\n"

## Запуск полного бенчмарка Python vs C++ с таблицей результатов
benchmark:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск Python + C++ сводной таблицы...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		cd /root/ws/src/quadropted_controller/scripts/benchmark && \
		python3 benchmark.py --combined"

## Запуск только Python бенчмарка
benchmark-python:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск Python бенчмарка...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		cd /root/ws/src/quadropted_controller/scripts/benchmark && \
		python3 benchmark.py"

## Запуск только C++ бенчмарка
benchmark-cpp:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск C++ бенчмарка...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		/root/ws/build/quadropted_controller_cpp/benchmark"

# ════════════════════════════════════════════════════════════
# CI/CD — ЛОКАЛЬНАЯ ПРОВЕРКА
# ════════════════════════════════════════════════════════════

.PHONY: ci-lint ci-test ci-lint-yaml ci-lint-python ci-lint-cpp ci-test-cpp

## Полный CI lint check (YAML + Python + C++)
ci-lint: ci-lint-yaml ci-lint-python ci-lint-cpp
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Все lint проверки пройдены${NC}\n"

## YAML lint (yamllint)
ci-lint-yaml:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}YAML lint (yamllint)...${NC}\n"
	@if command -v yamllint &> /dev/null; then \
		yamllint -c .yamllint .github/workflows/ && \
		yamllint -c .yamllint src/docker/*.yml && \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}YAML lint OK${NC}\n"; \
	else \
		pip install yamllint -q && \
		yamllint -c .yamllint .github/workflows/ && \
		yamllint -c .yamllint src/docker/*.yml && \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}YAML lint OK${NC}\n"; \
	fi

## Python lint (ruff)
ci-lint-python:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Python lint (ruff)...${NC}\n"
	@if command -v ruff &> /dev/null; then \
		ruff check src/ && \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Python lint OK${NC}\n"; \
	else \
		pip install ruff -q && \
		ruff check src/ && \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Python lint OK${NC}\n"; \
	fi

## C++ lint (clang-format check)
ci-lint-cpp:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}C++ format check (clang-format)...${NC}\n"
	@if command -v clang-format &> /dev/null; then \
		find src/quadropted_controller_cpp -name '*.hpp' -o -name '*.cpp' | \
			xargs clang-format --dry-run --Werror && \
		printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}C++ format OK${NC}\n"; \
	else \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}clang-format не установлен, пропускаем${NC}\n"; \
	fi

## Локальный запуск C++ тестов (через Docker)
ci-test: ci-test-cpp
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}Все тесты пройдены${NC}\n"

## C++ unit tests через Docker
ci-test-cpp:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск C++ unit тестов...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		cd /root/ws && \
		colcon test --packages-select quadropted_controller_cpp && \
		colcon test-result --verbose"
	@printf "${GREEN}${BOLD}[✓]${NC} ${GREEN}C++ tests OK${NC}\n"

# ════════════════════════════════════════════════════════════
# DEFAULT TARGET
# ════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
