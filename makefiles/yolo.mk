# makefiles/yolo.mk

.PHONY: yolo-detector yolo-log yolo-visualizer yolo-experiment-start yolo-experiment-stop yolo-experiment-result

## Запуск YOLO детектора (инференс, вывод логов)
yolo-detector:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск YOLO детектора...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector \
			$(if $(or $(MODEL),$(FPS),$(CONF)),--ros-args) \
			$(if $(MODEL),-p model:=${MODEL}) \
			$(if $(FPS),-p fps:=${FPS}) \
			$(if $(CONF),-p confidence_threshold:=${CONF})"

## YOLO детектор с логгированием детекций в файл (пример: make yolo-log LOG_INTERVAL=10)
yolo-log:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск YOLO с логгированием (интервал: $(LOG_INTERVAL) сек)...${NC}\n"
	@mkdir -p logs
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector \
			--ros-args \
			-p log_interval_sec:=${LOG_INTERVAL} \
			-p log_file:=/tmp/yolo_detections.log \
			$(if $(MODEL),-p model:=${MODEL}) \
			$(if $(CONF),-p confidence_threshold:=${CONF})"
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Лог детекций: /tmp/yolo_detections.log (в контейнере)${NC}\n"

## Запустить YOLO эксперимент (логгирование в фоне, пример: LOG_INTERVAL=10)
yolo-experiment-start:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск YOLO эксперимента (интервал: $(or $(LOG_INTERVAL),10) сек)...${NC}\n"
	@docker exec -d $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector \
			--ros-args \
			-p log_interval_sec:=${or $(LOG_INTERVAL),10} \
			-p log_file:=/tmp/yolo_experiment.log \
			$(if $(MODEL),-p model:=${MODEL}) \
			$(if $(CONF),-p confidence_threshold:=${CONF})"
	@sleep 2
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}YOLO эксперимент запущен (PID: см. docker exec)${NC}\n"

## Остановить YOLO эксперимент
yolo-experiment-stop:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Остановка YOLO эксперимента...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "pkill -f 'yolo_detector' 2>/dev/null; pkill -f 'yolo_experiment' 2>/dev/null || true"
	@sleep 1
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}YOLO детектор остановлен${NC}\n"

## Скопировать лог YOLO эксперимента на хост
yolo-experiment-result:
	$(require-container)
	@mkdir -p experiments
	@docker cp $(CONTAINER_NAME):/tmp/yolo_experiment.log experiments/ 2>/dev/null && \
		printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Лог скопирован в experiments/yolo_experiment.log${NC}\n" || \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Файл /tmp/yolo_experiment.log не найден в контейнере${NC}\n"
	@ls -la experiments/yolo_experiment.log 2>/dev/null || true

## Запуск визуализации детекций: RViz + visualizer (split: raw / detected)
yolo-visualizer:
	$(require-container)
	$(check-x11)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск визуализации детекций...${NC}\n"
	@docker exec -d $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception visualizer"
	@sleep 1
	@docker exec -d $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		rviz2 -d /root/ws/src/quadropted_perception/rviz/yolo_detection.rviz"
