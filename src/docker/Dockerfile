# ============================================================
# ЭТАП 1: Базовый образ с системными зависимостями
# ============================================================
ARG BASE_IMG=osrf/ros:jazzy-desktop
ARG ROS_DISTRO=jazzy
FROM ${BASE_IMG} AS base-system

ARG ROS_DISTRO

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    nano \
    tmux \
    python3 \
    python3-pip \
    python3-dev \
    ccache \
    libeigen3-dev \
    ros-dev-tools \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    ros-${ROS_DISTRO}-rclcpp \
    ros-${ROS_DISTRO}-rclpy \
    ros-${ROS_DISTRO}-urdf \
    ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-angles \
    ros-${ROS_DISTRO}-tf2-ros \
    ros-${ROS_DISTRO}-tf2 \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ЭТАП 3: ROS пакеты - Control
# ============================================================
FROM ros-core AS ros-control

ARG ROS_DISTRO=jazzy

# Кэширование ROS control пакетов
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    # ROS Control
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-gz-ros2-control \
    ros-${ROS_DISTRO}-controller-manager \
    ros-${ROS_DISTRO}-hardware-interface \
    ros-${ROS_DISTRO}-pluginlib \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ЭТАП 4: ROS пакеты - Simulation
# ============================================================
FROM ros-control AS ros-simulation

ARG ROS_DISTRO=jazzy

# Кэширование ROS simulation пакетов
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    # Gazebo и simulation
    ros-${ROS_DISTRO}-ros-gz-image \
    ros-${ROS_DISTRO}-ros-gz-bridge \
    ros-${ROS_DISTRO}-ros-gz-sim \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ЭТАП 5: ROS пакеты - Navigation
# ============================================================
FROM ros-simulation AS ros-navigation

ARG ROS_DISTRO=jazzy

# Кэширование ROS navigation пакетов
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    # Navigation
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-nav2-simple-commander \
    ros-${ROS_DISTRO}-robot-localization \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ЭТАП 6: ROS пакеты - Vision и Sensors
# ============================================================
FROM ros-navigation AS ros-vision

ARG ROS_DISTRO=jazzy

# Кэширование ROS vision пакетов
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    # Vision и sensors
    ros-${ROS_DISTRO}-camera-info-manager \
    ros-${ROS_DISTRO}-image-proc \
    ros-${ROS_DISTRO}-image-view \
    ros-${ROS_DISTRO}-apriltag-ros \
    ros-${ROS_DISTRO}-apriltag-msgs \
    ros-${ROS_DISTRO}-geometry-msgs \
    ros-${ROS_DISTRO}-topic-tools \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ЭТАП 7: ROS пакеты - Tools
# ============================================================
FROM ros-vision AS ros-tools

ARG ROS_DISTRO=jazzy

# Кэширование ROS tools пакетов
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    # Tools
    ros-${ROS_DISTRO}-ros2launch \
    ros-${ROS_DISTRO}-rqt-robot-steering \
    ros-${ROS_DISTRO}-tf-transformations \
    ros-${ROS_DISTRO}-teleop-twist-keyboard \
    ros-${ROS_DISTRO}-opennav-docking \
    # Тестирование и бенчмарки
    ros-${ROS_DISTRO}-ament-cmake-gtest \
    ros-${ROS_DISTRO}-ament-cmake-gmock \
    ros-${ROS_DISTRO}-ament-cmake-pytest \
    ros-${ROS_DISTRO}-test-msgs \
    python3-colcon-common-extensions \
    libbenchmark-dev \
    libbenchmark-tools \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ЭТАП 2: Изоляция package.xml для кэша rosdep
# ============================================================
FROM base-system AS package-xmls

WORKDIR /tmp
COPY src/ /tmp/src/
RUN find src/ -type f ! -name 'package.xml' -delete && \
    find src/ -type d -empty -delete 2>/dev/null; true

# ============================================================
# ЭТАП 3: ROS зависимости через rosdep + Python пакеты
# ============================================================
FROM base-system AS ros-deps

ARG ROS_DISTRO

WORKDIR /root/ws

COPY --from=package-xmls /tmp/src/ /root/ws/src/

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src --skip-keys "Eigen3 torch ultralytics" -y && \
    rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --no-cache-dir --break-system-packages \
    git+https://github.com/ruffsl/colcon-cache.git \
    'numpy<2' \
    scipy \
    pandas \
    PyYAML

# Установка Rust toolchain (для quadropted_controller_rust)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Установка PyTorch CPU + YOLO (для quadropted_perception)
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed \
    torch --index-url ${TORCH_INDEX_URL} \
    && pip3 install --no-cache-dir --break-system-packages --ignore-installed \
    ultralytics --no-deps \
    && pip3 install --no-cache-dir --break-system-packages \
    opencv-python-headless 'numpy<2'

# ============================================================
# ЭТАП 4: Сборка workspace
# ============================================================
FROM ros-deps AS workspace

ARG ROS_DISTRO

WORKDIR /root/ws

COPY src/ /root/ws/src/

RUN --mount=type=cache,target=/root/.ccache \
    bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && colcon cache lock 2>/dev/null; ccache colcon build --symlink-install --mixin ccache"

# ============================================================
# ЭТАП 5: Финальный образ
# ============================================================
FROM workspace AS final

ARG ROS_DISTRO
ARG WORKSPACE_DIR=/root/ws

RUN sed -i '/exec "\$@"/i umask 002' /ros_entrypoint.sh
RUN sed -i '/exec "\$@"/i source "'"$WORKSPACE_DIR"'/install/setup.bash"' /ros_entrypoint.sh

LABEL maintainer="Walking Robot Team"
LABEL version="3.3"
LABEL description="Walking Robot Simulation - ROS 2 Jazzy with Gazebo (rosdep)"
LABEL architecture="linux/amd64"

WORKDIR ${WORKSPACE_DIR}

RUN mkdir -p ${WORKSPACE_DIR}/logs ${WORKSPACE_DIR}/data

ENV WORKSPACE_DIR=${WORKSPACE_DIR}
ENV ROS_DISTRO=${ROS_DISTRO}
ENV ROS_LOG_DIR=${WORKSPACE_DIR}/logs
ENV LD_LIBRARY_PATH=/usr/local/lib:/opt/ros/${ROS_DISTRO}/lib

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD bash -c 'source /opt/ros/${ROS_DISTRO}/setup.bash && source ${WORKSPACE_DIR}/install/setup.bash && ros2 node list || exit 1'

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
