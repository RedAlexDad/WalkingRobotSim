IMAGE_NAME ?= elevation_mapping_cupy:jazzy
WORKSPACE ?= $(HOME)/ros2_ws

.PHONY: help build docker-build docker-test docker-build-test docker-run docker-demo setup-ws

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build              Build Docker image (docker build)"
	@echo "  setup-ws           Create ROS 2 workspace with source (requires sudo)"
	@echo "  docker-build       Build ROS packages inside container"
	@echo "  docker-test        Run tests inside container"
	@echo "  docker-build-test  Build + test"
	@echo "  docker-run         Interactive container shell"
	@echo "  docker-demo        Run synthetic_depth_demo with RViz"
	@echo ""
	@echo "Variables:"
	@echo "  IMAGE_NAME=$(IMAGE_NAME)   Docker image tag"
	@echo "  WORKSPACE=$(WORKSPACE)    ROS 2 workspace path"

build:
	docker build -f docker/Dockerfile.x64 -t $(IMAGE_NAME) .

docker-build:
	docker run --rm --gpus all --net=host \
		-v $(WORKSPACE):/ws -w /ws $(IMAGE_NAME) bash -lc '\
			set -e; \
			source /opt/ros/jazzy/setup.bash; \
			colcon build --symlink-install \
				--packages-select elevation_map_msgs elevation_mapping_cupy; \
		'

docker-test:
	docker run --rm --gpus all --net=host \
		-v $(WORKSPACE):/ws -w /ws $(IMAGE_NAME) bash -lc '\
			set -e; \
			source /opt/ros/jazzy/setup.bash; \
			source install/setup.bash; \
			colcon test --packages-select elevation_mapping_cupy \
				--event-handlers console_direct+; \
			colcon test-result --verbose; \
		'

docker-build-test: docker-build docker-test

docker-run:
	docker run -it --rm --gpus all --net=host \
		-v $(WORKSPACE):/ws -w /ws $(IMAGE_NAME) bash -l

docker-demo:
	docker run -it --rm --gpus all --net=host \
		-e DISPLAY=$(DISPLAY) \
		-e XAUTHORITY=$(XAUTHORITY) \
		-v /tmp/.X11-unix:/tmp/.X11-unix:rw \
		-v $(XAUTHORITY):$(XAUTHORITY):ro \
		-v $(WORKSPACE):/ws -w /ws $(IMAGE_NAME) bash -lc '\
			source /opt/ros/jazzy/setup.bash; \
			source install/setup.bash; \
			ros2 launch elevation_mapping_cupy synthetic_depth_demo.launch.py; \
		'

setup-ws:
	sudo rm -rf $(WORKSPACE)
	mkdir -p $(WORKSPACE)/src
	cp -r $(CURDIR) $(WORKSPACE)/src/
