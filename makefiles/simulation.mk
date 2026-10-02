# makefiles/simulation.mk

.PHONY: gazebo gazebo-rust gazebo-cpp teleop teleop-simple set-pose reset-pose kill-ros exec test-aliases save-logs \
        mujoco mujoco-viewer mujoco-lite mujoco-kill

# ════ MuJoCo ════
MUJOCO_DIR    := $(PROJECT_ROOT)/src/mujoco
MUJOCO_VENV   := $(PROJECT_ROOT)/.venv-mujoco
MUJOCO_BRIDGE := $(MUJOCO_DIR)/mujoco_ros_bridge.py

# ════ Gazebo: аргументы launch ════
# В переменных, а не в $(call) — make делит аргументы call по запятым,
# а внутри $(if ...) они есть.
GAZEBO_COMMON_ARGS := use_sim_time:=true gui:=true
GAZEBO_RUST_ARGS   := $(GAZEBO_COMMON_ARGS) $(if $(WORLD),world:=${WORLD}) $(if $(FPS),camera_fps:=${FPS}) $(if $(RVZ),enable_rviz:=${RVZ}) $(if $(ELEVATION),use_elevation:=${ELEVATION})
GAZEBO_LITE_ARGS   := $(GAZEBO_COMMON_ARGS) camera_fps:=5 enable_rviz:=false $(if $(WORLD),world:=${WORLD}) $(if $(ELEVATION),use_elevation:=${ELEVATION})
GAZEBO_CPP_ARGS    := $(GAZEBO_COMMON_ARGS) $(if $(FPS),camera_fps:=${FPS}) $(if $(ELEVATION),use_elevation:=${ELEVATION})

##! Запуск MuJoCo симуляции (Rust контроллер — по умолчанию, с окном)
mujoco: mujoco-viewer

##! Запуск MuJoCo с GUI-окном + Rust контроллер
## Опции: VX=0.5 команда скорости, DURATION=60 длительность (с)
mujoco-viewer:
	$(require-container)
	$(check-x11)
	@printf "$(INFO)Запуск MuJoCo + Rust контроллер...${NC}\n"
	$(start-rust-controller)
	$(wait-controller)
	@source /opt/ros/lyrical/setup.bash 2>/dev/null || true; \
	 $(MUJOCO_VENV)/bin/python $(MUJOCO_BRIDGE) \
		--duration $(if $(DURATION),${DURATION},60) $(if $(VX),--vx ${VX}) --viewer
	@$(MAKE) mujoco-kill

##! Лёгкий режим: MuJoCo без окна (меньше нагрузка, для автотестов)
mujoco-lite:
	$(require-container)
	@printf "$(INFO)Запуск MuJoCo (headless)...${NC}\n"
	$(start-rust-controller)
	$(wait-controller)
	@source /opt/ros/lyrical/setup.bash 2>/dev/null || true; \
	 $(MUJOCO_VENV)/bin/python $(MUJOCO_BRIDGE) \
		--duration $(if $(DURATION),${DURATION},60) $(if $(VX),--vx ${VX})
	@$(MAKE) mujoco-kill

##! Очистка MuJoCo и Rust-контроллера
mujoco-kill:
	@pkill -f mujoco_ros_bridge 2>/dev/null || true
	@docker exec $(CONTAINER_NAME) pkill -f robot_controller_node 2>/dev/null || true
	@printf "$(OK)MuJoCo и Rust-контроллер остановлены${NC}\n"

## Запуск Gazebo симуляции (Rust контроллер — по умолчанию)
gazebo: gazebo-rust

##! Запуск Gazebo симуляции с Rust контроллером (контроллер + одометрия)
## Опции: WORLD=terrain.world (по умолчанию cafe.world), FPS=5 camera_fps,
##         RVZ=false — без RViz (лёгкий режим)
gazebo-rust: rust-build
	$(require-container)
	$(check-x11)
	@printf "$(INFO)Запуск Gazebo симуляции с Rust контроллером...${NC}\n"
	$(call gazebo-launch,launch.launch.py,$(GAZEBO_RUST_ARGS))
	@printf "$(INFO)Симуляция завершена, сохранение логов...${NC}\n"
	@$(MAKE) save-logs

##! Лёгкий режим: Gazebo (Rust) без RViz и с пониженным FPS камеры —
## меньше нагрузка на CPU (полезно при тормозах ноутбука)
gazebo-lite: rust-build
	$(require-container)
	$(check-x11)
	@printf "$(INFO)Запуск Gazebo (Rust) в лёгком режиме: RViz выключен, камера 5 FPS...${NC}\n"
	$(call gazebo-launch,launch.launch.py,$(GAZEBO_LITE_ARGS))
	@printf "$(INFO)Симуляция завершена, сохранение логов...${NC}\n"
	@$(MAKE) save-logs

##! Запуск Gazebo симуляции с C++ контроллером
gazebo-cpp:
	$(require-container)
	$(check-x11)
	@printf "$(INFO)Запуск Gazebo симуляции с C++ контроллером...${NC}\n"
	$(call gazebo-launch,launch_cpp.launch.py,$(GAZEBO_CPP_ARGS))
	@printf "$(INFO)Симуляция завершена, сохранение логов...${NC}\n"
	@$(MAKE) save-logs

## Запуск управления роботом (teleop) — скорость + переключение походки (1 TROT 2 CRAWL 3 STAND 4 REST)
teleop:
	$(require-container)
	@printf "$(INFO)Запуск teleop (скорость + походка)...${NC}\n"
	@docker cp scripts/robot_teleop.py $(CONTAINER_NAME):/tmp/robot_teleop.py >/dev/null
	@$(PROJECT_ROOT)/scripts/wrs-exec.sh -it python3 /tmp/robot_teleop.py --ns /robot1 $(if $(VX),--vx ${VX}) $(if $(WZ),--wz ${WZ})

## Простой teleop (только скорость, без переключения походки)
teleop-simple:
	$(require-container)
	@printf "$(INFO)Запуск teleop_twist_keyboard...${NC}\n"
	@$(PROJECT_ROOT)/scripts/wrs-exec.sh -it ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel

## Установка положения робота в Gazebo (пример: make set-pose X=1.0 Y=0.0 Z=0.0 YAW=0.0)
set-pose:
	$(require-container)
	@if [ -z "$(X)" ] || [ -z "$(Y)" ] || [ -z "$(Z)" ] || [ -z "$(YAW)" ]; then \
		printf "$(ERR)Укажите все параметры: X Y Z YAW${NC}\n"; \
		printf "Пример: make set-pose X=1.0 Y=0.0 Z=0.0 YAW=0.0\n"; \
		exit 1; \
	fi
	@printf "$(INFO)Установка положения робота: X=$(X) Y=$(Y) Z=$(Z) YAW=$(YAW)${NC}\n"
	@$(call gz-set-pose,$(X),$(Y),$(Z),$(YAW))
	@printf "$(OK)Положение установлено${NC}\n"

## Сброс положения робота в начало (0, 0, 0.5, 0)
reset-pose:
	$(require-container)
	@printf "$(INFO)Сброс положения робота в начало...${NC}\n"
	@$(call gz-set-pose,0,0,0.5,0)
	@printf "$(OK)Положение сброшено${NC}\n"

## Выполнение команды в контейнере (пример: make exec CMD="ros2 topic list")
exec:
	$(require-container)
	@if [ -z "$(CMD)" ]; then \
		printf "$(ERR)Укажите команду для выполнения${NC}\n" >&2; \
		printf "Пример: make exec CMD='ros2 topic list'\n" >&2; \
		exit 1; \
	fi
	@$(PROJECT_ROOT)/scripts/wrs-exec.sh -i $(CMD)

## Проверка алиасов в контейнере
test-aliases:
	$(require-container)
	@printf "$(INFO)Проверка алиасов в контейнере...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		source ~/.bashrc && \
		echo 'Проверка алиасов:' && \
		alias topics && \
		echo 'Топики (первые 3):' && \
		topics | head -3 && \
		echo 'Алиасы работают!'"

## Очистка всех ROS/Gazebo процессов в контейнере
kill-ros:
	@printf "$(INFO)Очистка всех ROS/Gazebo процессов...${NC}\n"
	@if docker ps --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		printf "$(INFO)Убиваем ROS/Gazebo процессы в контейнере...${NC}\n"; \
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
				printf '$(WARN)Некоторые ROS процессы все еще запущены${NC}\n'; \
				pgrep -f 'ros2\|gz sim\|rviz2' || true; \
			else \
				printf '$(OK)Все ROS/Gazebo процессы успешно остановлены${NC}\n'; \
			fi"; \
	else \
		printf "$(WARN)Контейнер $(CONTAINER_NAME) не запущен${NC}\n"; \
	fi

## Сохранение логов Gazebo сессии
save-logs:
	@if docker ps --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		printf "$(INFO)Сохранение логов сессии Gazebo...${NC}\n"; \
		timestamp=$$(date +%s); \
		hostname=$$(hostname); \
		backup_folder="$(PROJECT_ROOT)/logs/gazebo_backup_$${timestamp}_$${hostname}"; \
		gazebo_folder="$(PROJECT_ROOT)/logs/gazebo"; \
		mkdir -p "$$backup_folder" 2>/dev/null || { \
			printf "$(WARN)Не удалось создать $$backup_folder, используем /tmp/${NC}\n"; \
			backup_folder="/tmp/gazebo_backup_$${timestamp}_$${hostname}"; \
			mkdir -p "$$backup_folder"; \
		}; \
		printf "$(INFO)Копирование ROS логов из контейнера...${NC}\n"; \
		docker cp $(CONTAINER_NAME):/root/ws/logs/. "$$backup_folder/" 2>/dev/null || true; \
		printf "$(INFO)Объединение логов по типам...${NC}\n"; \
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
		done; \
		cd "$(PROJECT_ROOT)"; \
		if [ -d "$$gazebo_folder" ]; then \
			cp -r "$$gazebo_folder"/* "$$backup_folder/" 2>/dev/null || true; \
		fi; \
		$(COMPOSE) logs --no-color > "$$backup_folder/docker_compose.log" 2>/dev/null || true; \
		{ \
			echo "=== Логи сессии Walking Robot Simulator ==="; \
			echo "Время: $$(date)"; \
			echo "Тип: Gazebo симуляция"; \
			echo "Хост: $$hostname"; \
			echo "Контейнер: $(CONTAINER_NAME)"; \
		} > "$$backup_folder/session_info.log"; \
		if [ -d "$$gazebo_folder" ]; then \
			printf "$(INFO)Очистка папки gazebo...${NC}\n"; \
			docker run --rm -v "$$gazebo_folder":/tmp/clean alpine sh -c "rm -rf /tmp/clean/*" 2>/dev/null || true; \
		fi; \
		mkdir -p "$$gazebo_folder"; \
		file_count=$$(find "$$backup_folder" -type f 2>/dev/null | wc -l); \
		merged_count=$$(find "$$backup_folder/merged_logs" -type f 2>/dev/null | wc -l); \
		printf "$(OK)Логи сохранены: $$backup_folder${NC}\n"; \
		printf "Всего файлов: $$file_count\n"; \
		printf "Объединенных логов: $$merged_count\n"; \
		printf "Проверьте: $$backup_folder/merged_logs/\n"; \
	else \
		printf "$(WARN)Контейнер не запущен, логи не сохранены${NC}\n"; \
	fi

## Очистка старых логов сборки colcon (старше 30 дней)
clean-build-logs:
	@printf "$(INFO)Очистка старых логов сборки...${NC}\n"
	@find log/ -maxdepth 1 -type d -name "build_*" -mtime +30 -exec rm -rf {} + 2>/dev/null || true
	@printf "$(OK)Логи сборки старше 30 дней удалены${NC}\n"

## Очистка логов Gazebo
clean-gazebo-logs:
	@printf "$(INFO)Очистка логов Gazebo...${NC}\n"
	@rm -rf logs/gazebo/* 2>/dev/null || true
	@printf "$(OK)Логи Gazebo очищены${NC}\n"

## Очистка всех логов
clean-logs: clean-build-logs clean-gazebo-logs
	@printf "$(OK)Все логи очищены${NC}\n"
