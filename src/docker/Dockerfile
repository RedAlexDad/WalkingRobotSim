# ============================================================
# ЭТАП 1: Базовый образ с системными зависимостями
# ============================================================
ARG BASE_IMG=osrf/ros:jazzy-desktop
ARG ROS_DISTRO=jazzy
FROM ${BASE_IMG} AS base-system

ARG ROS_DISTRO

# Кэширование системных пакетов
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
    # ROS build tools (не входят в rosdep)
    ros-dev-tools \
    python3-colcon-common-extensions \
    libbenchmark-dev \
    libbenchmark-tools \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ЭТАП 2: ROS зависимости через rosdep + Python пакеты
# ============================================================
FROM base-system AS ros-deps

ARG ROS_DISTRO

WORKDIR /root/ws

# Копируем только package.xml — кэш не сбивается при изменении .cpp/.py
COPY src/ /root/ws/src/
RUN find src/ -type f ! -name 'package.xml' -delete && \
    find src/ -type d -empty -delete 2>/dev/null; true

# Установка ROS-зависимостей через rosdep (единый источник — package.xml)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src --skip-keys "Eigen3 torch ultralytics" -y && \
    rm -rf /var/lib/apt/lists/*

# Кэширование pip пакетов
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --no-cache-dir --break-system-packages \
    git+https://github.com/ruffsl/colcon-cache.git \
    'numpy<2' \
    scipy \
    pandas \
    PyYAML

# YOLO + torch (по умолчанию CPU, для GPU укажи --build-arg TORCH_INDEX_URL=...)
# Важно: numpy фиксируем <2 из-за несовместимости cv_bridge (собран под numpy 1.x)
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed \
    torch --index-url ${TORCH_INDEX_URL} \
    && pip3 install --no-cache-dir --break-system-packages --ignore-installed \
    ultralytics --no-deps \
    && pip3 install --no-cache-dir --break-system-packages \
    opencv-python-headless 'numpy<2'

# ============================================================
# ЭТАП 3: Сборка workspace
# ============================================================
FROM ros-deps AS workspace

ARG ROS_DISTRO

WORKDIR /root/ws

# Полная копия исходного кода (предыдущий слой с package.xml перезаписывается)
COPY src/ /root/ws/src/

# Кэширование сборки ROS пакетов
RUN --mount=type=cache,target=/root/.ccache \
    bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && colcon cache lock 2>/dev/null; ccache colcon build --symlink-install --mixin ccache"

# ============================================================
# ЭТАП 4: Финальный образ
# ============================================================
FROM workspace AS final

ARG ROS_DISTRO
ARG WORKSPACE_DIR=/root/ws

# Настройка entrypoint
RUN sed -i '/exec "\$@"/i umask 002' /ros_entrypoint.sh
RUN sed -i '/exec "\$@"/i source "'"$WORKSPACE_DIR"'/install/setup.bash"' /ros_entrypoint.sh

LABEL maintainer="Walking Robot Team"
LABEL version="3.2"
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
