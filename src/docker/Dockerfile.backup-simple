ARG BASE_IMG=osrf/ros:jazzy-desktop
FROM ${BASE_IMG}

ARG ROS_DISTRO=jazzy

# Кэширование apt-get
RUN  --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    ros-${ROS_DISTRO}-desktop \
    ros-dev-tools \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    ros-${ROS_DISTRO}-rclcpp \
    ros-${ROS_DISTRO}-rclpy \
    ros-${ROS_DISTRO}-urdf \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-angles \
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-gz-ros2-control \
    ros-${ROS_DISTRO}-controller-manager \
    ros-${ROS_DISTRO}-hardware-interface \
    ros-${ROS_DISTRO}-pluginlib \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-ros2launch \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-camera-info-manager \
    ros-${ROS_DISTRO}-rqt-robot-steering \
    ros-${ROS_DISTRO}-tf-transformations \
    ros-${ROS_DISTRO}-teleop-twist-keyboard \
    ros-${ROS_DISTRO}-ros2-controllers \
    ros-${ROS_DISTRO}-ros-gz-image \
    ros-${ROS_DISTRO}-ros-gz-bridge \
    ros-${ROS_DISTRO}-ros-gz-sim \
    ros-${ROS_DISTRO}-opennav-docking \
    ros-${ROS_DISTRO}-apriltag-ros \
    ros-${ROS_DISTRO}-apriltag-msgs \
    ros-${ROS_DISTRO}-image-proc \
    ros-${ROS_DISTRO}-image-view \
    ros-${ROS_DISTRO}-geometry-msgs \
    ros-${ROS_DISTRO}-nav2-simple-commander \
    ros-${ROS_DISTRO}-tf2-ros \
    ros-${ROS_DISTRO}-tf2 \
    ros-${ROS_DISTRO}-robot-localization \
    tmux \
    tmuxinator \
    python3-colcon-common-extensions \
    ccache \
    ros-${ROS_DISTRO}-topic-tools \
    python3 python3-pip

# Установка colcon-cache
RUN pip3 install --break-system-packages git+https://github.com/ruffsl/colcon-cache.git

# Копируем исходный код
COPY ../ /root/ws/src

WORKDIR /root/ws

SHELL ["/bin/bash", "-c"]

# Сборка пакетов
RUN --mount=type=cache,target=/root/.ccache \
    . /ros_entrypoint.sh && \
    colcon cache lock && \
    ccache colcon build --symlink-install \
    --mixin ccache

# Настройка entrypoint
RUN sed -i '/exec "\$@"/i umask 002' /ros_entrypoint.sh
ENV WORKSPACE_DIR=/root/ws
RUN sed -i '/exec "\$@"/i source "$WORKSPACE_DIR/install/setup.bash"' /ros_entrypoint.sh

# Метаданные образа
LABEL maintainer="Walking Robot Team"
LABEL version="3.0"
LABEL description="Walking Robot Simulation - ROS 2 Jazzy with Gazebo"
LABEL architecture="linux/amd64"

# Установка рабочей директории по умолчанию
WORKDIR ${WORKSPACE_DIR}

# Создание необходимых директорий
RUN mkdir -p ${WORKSPACE_DIR}/logs ${WORKSPACE_DIR}/data

# Health check для проверки работоспособности
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD bash -c 'source /opt/ros/${ROS_DISTRO}/setup.bash && source ${WORKSPACE_DIR}/install/setup.bash && ros2 node list' || exit 1

# Установка точки входа по умолчанию
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
