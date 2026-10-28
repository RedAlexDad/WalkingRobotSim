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
		printf "$(ERR)Контейнер $(CONTAINER_NAME) не запущен.${NC}\n" >&2; \
		printf "$(WARN)Запустите: make deploy${NC}\n" >&2; \
		exit 1; \
	fi
endef

## Проверка и настройка X11 для GUI
define check-x11
	@if [ -z "$$DISPLAY" ]; then \
		printf "$(ERR)DISPLAY не установлен.${NC}\n" >&2; \
		printf "$(WARN)Установите: export DISPLAY=:0${NC}\n" >&2; \
		exit 1; \
	fi
	@xhost +local:root >/dev/null 2>&1 || true
	@xhost +local:$(USER) >/dev/null 2>&1 || true
	@printf "$(OK)X11 настроен: DISPLAY=$$DISPLAY${NC}\n"
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
	@printf "$(INFO)Перевод робота в режим $(1)...${NC}\n"
	@$(call ros-exec,ros2 topic pub --once /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand \"{mode: $(1)$(comma) robot_id: 1}\")
	@printf "$(OK)Режим $(1) установлен${NC}\n"
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
	@printf "$(INFO)Ожидание регистрации контроллера...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; for i in \$$(seq 1 20); do n=\$$(ros2 topic info /robot1/joint_group_controller/commands 2>/dev/null | awk '/Publisher count/{print \$$3}'); [ \"\$$n\" = 1 ] && break; sleep 0.5; done"
endef

# ════ RViz: внешний конфиг (RVIZ=<path>|ergonomic) ════
# RVIZ_FILE пуст — используется штатный RViz из launch; иначе конфиг
# копируется в контейнер и RViz стартует отдельно (полный контроль над
# окном, конфигом и издателем ИМ).
define prepare-rviz-config
	@if [ -n "$(RVIZ_FILE)" ]; then \
		if [ ! -f "$(RVIZ_FILE)" ]; then \
			printf "$(ERR)RViz-конфиг не найден: $(RVIZ_FILE)${NC}\n"; \
			exit 1; \
		fi; \
		docker cp "$(RVIZ_FILE)" $(CONTAINER_NAME):/tmp/wrs_rviz.rviz >/dev/null || exit 1; \
		printf "$(OK)RViz-конфиг: $(RVIZ_FILE)${NC}\n"; \
	fi
endef

define start-custom-rviz
	@if [ -n "$(RVIZ_FILE)" ]; then \
		if [ -z "$(DISPLAY)" ]; then \
			printf "$(ERR)DISPLAY не задан — внешний RViz не запустить${NC}\n"; \
			exit 1; \
		fi; \
		for p in $$(pgrep -x rviz2 || true); do kill -9 $$p 2>/dev/null || true; done; \
		docker exec $(CONTAINER_NAME) pkill -9 -x rviz2 2>/dev/null || true; \
		docker exec $(CONTAINER_NAME) pkill -f "/tmp/im_publisher.py" 2>/dev/null || true; \
		docker exec $(CONTAINER_NAME) pkill -f "waypoint_collector.py" 2>/dev/null || true; \
		sleep 1; \
		if [ -n "$(RVIZ_ERGO_ANY)" ]; then \
			docker cp "$(PROJECT_ROOT)/experiments/ergonomics_rviz/im_publisher.py" $(CONTAINER_NAME):/tmp/im_publisher.py >/dev/null || exit 1; \
			docker exec -d $(CONTAINER_NAME) bash -lc "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; python3 /tmp/im_publisher.py --ros-args -p use_sim_time:=true -p text_scale:=0.76 -p state:=normal -r /tf:=/robot1/tf -r /tf_static:=/robot1/tf_static > /tmp/im_pub.log 2>&1"; \
			docker exec -d $(CONTAINER_NAME) bash -lc "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; ros2 run gazebo_sim waypoint_collector.py --ros-args -r __ns:=/robot1 -p localizer:=slam_toolbox > /tmp/wpc.log 2>&1"; \
			sleep 2; \
			docker exec $(CONTAINER_NAME) bash -lc 'tail -2 /tmp/im_pub.log' || true; \
		fi; \
		docker exec -d $(CONTAINER_NAME) bash -lc "source /opt/ros/$(ROS_DISTRO)/setup.bash; source /root/ws/install/setup.bash 2>/dev/null || true; export DISPLAY=$(DISPLAY); export QT_QPA_PLATFORM=xcb; rviz2 $(RVIZ_FULLSCREEN) -d /tmp/wrs_rviz.rviz --ros-args -p use_sim_time:=true -r __ns:=/robot1 -r /tf:=tf -r /tf_static:=tf_static > /tmp/wrs_rviz.log 2>&1"; \
		printf "$(OK)RViz запущен в контейнере: /tmp/wrs_rviz.rviz${NC}\n"; \
		if [ -n "$(RVIZ_ERGO)" ]; then \
			docker cp "$(PROJECT_ROOT)/experiments/ergonomics_rviz/ru_hud.py" $(CONTAINER_NAME):/tmp/ru_hud.py >/dev/null || true; \
			docker exec -d $(CONTAINER_NAME) bash -lc "source /opt/ros/$(ROS_DISTRO)/setup.bash; export DISPLAY=$(DISPLAY); export QT_QPA_PLATFORM=xcb; python3 /tmp/ru_hud.py --bypass-wm --x 1908 --y 732 > /tmp/ru_hud.log 2>&1"; \
			sleep 3; \
			docker exec $(CONTAINER_NAME) bash -lc 'grep -m1 winid /tmp/ru_hud.log' || true; \
		fi; \
		( sleep 45; python3 $(PROJECT_ROOT)/scripts/check_flicker.py --title "wrs_rviz.rviz" --settle 0 > /tmp/wrs_flicker.log 2>&1 || { \
			printf "$(ERR)Мерцание: окно RViz закрыто${NC}\n" >> /tmp/wrs_flicker.log; \
			docker exec $(CONTAINER_NAME) pkill -9 -x rviz2 2>/dev/null || true; } ) >/dev/null 2>&1 & \
	fi
endef

define stop-custom-rviz
	@if [ -n "$(RVIZ_FILE)" ]; then \
		for p in $$(pgrep -x rviz2 || true); do kill -9 $$p 2>/dev/null || true; done; \
		docker exec $(CONTAINER_NAME) pkill -9 -x rviz2 2>/dev/null || true; \
		docker exec $(CONTAINER_NAME) pkill -f "/tmp/im_publisher.py" 2>/dev/null || true; \
		docker exec $(CONTAINER_NAME) pkill -f "waypoint_collector.py" 2>/dev/null || true; \
		docker exec $(CONTAINER_NAME) pkill -f "ru_hud.py" 2>/dev/null || true; \
	fi
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
