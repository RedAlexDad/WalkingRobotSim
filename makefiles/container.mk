# makefiles/container.mk
#
# Общие обёртки для работы с контейнером: проверки и запуск команд с уже
# подгруженными ROS + workspace. Убирают повторяющийся boilerplate
# «docker exec … source …» из десятков целей.
#
# Примечание: команда для ros-exec* передаётся через $(call) и не должна
# содержать запятых — make делит аргументы call по запятым. Внутри команд
# с JSON используйте переменную $(comma) (определена ниже).

# ── проверки ──────────────────────────────────────────────

## Проверка что контейнер запущен
define require-container
	@if ! docker ps --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		printf "${RED}${BOLD}[x]${NC} ${RED}Контейнер $(CONTAINER_NAME) не запущен.${NC}\n" >&2; \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Запустите: make deploy${NC}\n" >&2; \
		exit 1; \
	fi
endef

## Проверка и настройка X11 для GUI
define check-x11
	@if [ -z "$$DISPLAY" ]; then \
		printf "${RED}${BOLD}[x]${NC} ${RED}DISPLAY не установлен.${NC}\n" >&2; \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Установите: export DISPLAY=:0${NC}\n" >&2; \
		exit 1; \
	fi
	@xhost +local:root >/dev/null 2>&1 || true
	@xhost +local:$(USER) >/dev/null 2>&1 || true
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}X11 настроен: DISPLAY=$$DISPLAY${NC}\n"
endef

# ── запуск в контейнере с ROS + workspace ─────────────────

# Неинтерактивно
define ros-exec
	docker exec $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; $(1)"
endef

# С TTY (интерактивно)
define ros-exec-it
	docker exec -it $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; $(1)"
endef

# В фоне (detached)
define ros-exec-d
	docker exec -d $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; $(1)"
endef

comma := ,

# ── типовые действия ──────────────────────────────────────

# Публикация режима робота (REST/TROT/CRAWL/STAND)
define set-robot-mode
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Перевод робота в режим $(1)...${NC}\n"
	@$(call ros-exec,ros2 topic pub --once /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand \"{mode: $(1)$(comma) robot_id: 1}\")
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Режим $(1) установлен${NC}\n"
endef

# Вызов сервиса std_srvs/Trigger по пути $(1)
define ros-call-trigger
	@$(call ros-exec,ros2 service call $(1) std_srvs/Trigger)
endef

# Установка позы робота в Gazebo. Аргументы: X Y Z YAW
define gz-set-pose
	docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		gz service -s /world/default/set_pose \
			--reqtype gz.msgs.Pose \
			--reptype gz.msgs.Boolean \
			--timeout 1000 \
			--req \"name: 'go2'$(comma) position: {x: $(1)$(comma) y: $(2)$(comma) z: $(3)}$(comma) orientation: {z: $(4)}\""
endef

# Запуск Rust-контроллера в контейнере (в фоне)
define start-rust-controller
	@docker exec -d $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; ros2 run quadropted_controller_rust robot_controller_node --ros-args -r __ns:=/robot1 > /tmp/rust.log 2>&1"
endef

# Ожидание регистрации контроллера
define wait-controller
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Ожидание регистрации контроллера...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; for i in \$$(seq 1 20); do n=\$$(ros2 topic info /robot1/joint_group_controller/commands 2>/dev/null | awk '/Publisher count/{print \$$3}'); [ \"\$$n\" = 1 ] && break; sleep 0.5; done"
endef

# Запуск Gazebo с указанным launch-файлом и аргументами.
# Аргументы передавайте переменной (напр. $(GAZEBO_RUST_ARGS)) — внутри
# $(call) не должно быть литеральных запятых.
define gazebo-launch
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash; \
		source /root/ws/install/setup.bash 2>/dev/null || true; \
		ros2 launch gazebo_sim $(1) $(2)"
endef
