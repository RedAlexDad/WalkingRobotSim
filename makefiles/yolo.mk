# makefiles/yolo.mk

.PHONY: yolo-detector yolo-visualizer

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
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector \
			--ros-args \
			-p log_interval_sec:=${LOG_INTERVAL} \
			-p log_file:=/tmp/yolo_detections.log \
			$(if $(MODEL),-p model:=${MODEL}) \
			$(if $(CONF),-p confidence_threshold:=${CONF})"
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Лог детекций: /tmp/yolo_detections.log (в контейнере)${NC}\n"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Скопировать на хост: docker cp $(CONTAINER_NAME):/tmp/yolo_detections.log .${NC}\n"

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
