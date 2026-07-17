# Быстрый справочник Isaac Sim

## Системные требования

| Параметр | Минимум            | Рекомендуется |
| -------- | ------------------ | ------------- |
| ОС       | Ubuntu 22.04/24.04 | Ubuntu 24.04  |
| RAM      | 32 GB              | 64 GB         |
| VRAM     | 16 GB              | 16 GB+        |
| GPU      | RTX 4080           | RTX 5080+     |
| Драйвер  | 595.58.03 (Linux)  | 595.58.03     |
| Диск     | 50 GB              | 100 GB        |

## Запуск

```bash
# GUI
./isaac-sim.sh

# С ROS2
./isaac-sim.sh --ros2

# Headless (без GUI)
./isaac-sim.sh --headless

# Docker
docker run -it --rm \
    --runtime nvidia \
    -e ACCEPT_EULA=Y \
    -e PRIVACY_CONSENT=Y \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    --network host \
    nvcr.io/nvidia/isaac-sim:6.0.1
```

## OCuLink RTX 5070 Ti

```bash
# Проверка линка
nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv
# → 4, 4 (Gen4 x4)

# Мониторинг
nvidia-smi -l 1
```

## ROS2 топики Isaac Sim

| Топик                               | Тип         | Направление |
| ----------------------------------- | ----------- | ----------- |
| `/isaac_sim/odom`                   | Odometry    | Isaac → ROS |
| `/isaac_sim/scan`                   | LaserScan   | Isaac → ROS |
| `/isaac_sim/points`                 | PointCloud2 | Isaac → ROS |
| `/isaac_sim/tf`                     | TFMessage   | Isaac → ROS |
| `/isaac_sim/camera/color/image_raw` | Image       | Isaac → ROS |
| `/cmd_vel`                          | Twist       | ROS → Isaac |

## Террейн

```bash
# Heightmap Importer: Extensions → Heightmap Importer
# Вход: occupancy map PNG
# Выход: USD terrain с collision
# Cell size: м/пиксель (0.1-1.0)
```

## Полезные ссылки

- Документация: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/
- ROS2 туториал: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/ros2_tutorials/
- Форум: https://forums.developer.nvidia.com/c/omniverse/isaac-sim/
- nvblox: https://github.com/nvidia-isaac/nvblox
- Isaac ROS: https://nvidia-isaac-ros.github.io/
