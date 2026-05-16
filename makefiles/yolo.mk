# makefiles/yolo.mk

.PHONY: yolo-detector yolo-visualizer

## Запуск YOLO детектора (инференс, вывод логов)
yolo-detector:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск YOLO детектора...${NC}\n"
	@docker exec -it $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		ros2 run quadropted_perception yolo_detector$(if $(MODEL), --ros-args -p model:=${MODEL})"

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
