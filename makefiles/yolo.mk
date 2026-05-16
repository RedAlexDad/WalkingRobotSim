# makefiles/yolo.mk

.PHONY: yolo yolo-detector yolo-visualizer

## Запуск YOLO детектора
yolo: yolo-detector

## Запуск YOLO детектора (инференс)
yolo-detector:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск YOLO детектора...${NC}\n"
	@docker exec -d $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector"

## Запуск визуализации детекций в RViz
yolo-visualizer:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск визуализации детекций...${NC}\n"
	@docker exec -d $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception visualizer"
