# Dockerfile — 10-этапная сборка

## Файл
`src/docker/Dockerfile`

## Описание

Многоэтапная Docker-сборка с кэшированием слоёв (APT, pip, ccache). Первая сборка 15-30 мин, повторная 30-60 сек.

## Этапы сборки

### Этап 1: `base-system`
**Базовый образ:** `osrf/ros:jazzy-desktop`

**Установленные пакеты:**
- build-essential, cmake, git, wget, curl, nano, tmux
- python3, python3-pip, python3-dev
- ccache (кэширование компиляции)

**Кэширование:** `/var/cache/apt`, `/var/lib/apt`

### Этап 2: `ros-core`
**ROS Core пакеты:**
- ros-jazzy-desktop, ros-dev-tools
- rmw-cyclonedds-cpp, rclcpp, rclpy
- urdf, xacro, std-msgs, angles
- tf2-ros, tf2

### Этап 3: `ros-control`
**ROS Control пакеты:**
- ros2-control, gz-ros2-control
- controller-manager, hardware-interface, pluginlib
- joint-state-publisher, robot-state-publisher
- ros2-controllers

### Этап 4: `ros-simulation`
**Симуляция:**
- ros-gz-image, ros-gz-bridge, ros-gz-sim

### Этап 5: `ros-navigation`
**Навигация:**
- slam-toolbox, navigation2, nav2-bringup, nav2-simple-commander
- robot-localization

### Этап 6: `ros-vision`
**Зрение и сенсоры:**
- camera-info-manager, image-proc, image-view
- apriltag-ros, apriltag-msgs
- geometry-msgs, topic-tools

### Этап 7: `ros-tools`
**Инструменты:**
- ros2launch, rqt-robot-steering, tf-transformations
- teleop-twist-keyboard, opennav-docking
- ament-cmake-gtest/gmock/pytest
- tmux, tmuxinator, colcon-common-extensions

### Этап 8: `python-deps`
**Python пакеты:**
- numpy, scipy, pandas, PyYAML
- colcon-cache

**Кэширование:** `/root/.cache/pip`

### Этап 9: `workspace`
- WORKDIR: `/root/ws`
- Копирование исходного кода: `src/` → `/root/ws/src`
- Сборка: `colcon build --symlink-install --mixin ccache`

**Кэширование:** `/root/.ccache`

### Этап 10: `final`
**Настройка:**
- Модификация `/ros_entrypoint.sh` — source workspace
- Создание директорий: `logs/`, `data/`

**Переменные окружения:**

| ENV                    | Значение                 |
| ---------------------- | ------------------------ |
| `WORKSPACE_DIR`        | `/root/ws`               |
| `ROS_DISTRO`           | `jazzy`                  |
| `ROS_LOG_DIR`          | `/root/ws/logs`          |
| `GAZEBO_MASTER_URI`    | `http://localhost:11345` |
| `GAZEBO_RESOURCE_PATH` | `/usr/share/gazebo-11`   |

**Health check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ros2 node list || exit 1
```

## Оптимизации

1. **Кэширование APT** — монтирование `/var/cache/apt` как cache volume
2. **Кэширование pip** — монтирование `/root/.cache/pip`
3. **ccache** — кэширование объектных файлов компиляции
4. **colcon cache** — инкрементальная сборка ROS пакетов
5. **No install recommends** — минимизация размера образа

## Метаданные

- **Maintainer:** Walking Robot Team
- **Version:** 3.1
- **Architecture:** linux/amd64
