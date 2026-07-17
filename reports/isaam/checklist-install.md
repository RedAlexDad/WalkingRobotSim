# Чек-лист установки Isaac Sim 6.0.1

## Система

- [ ] Ubuntu 24.04.4 LTS ✅
- [ ] RTX 5070 Ti (OCuLink) ✅
- [ ] 32GB RAM ✅
- [ ] 1TB NVMe SSD ✅

## Этап 1: Подготовка (драйвер)

- [ ] `sudo apt purge *nvidia*`
- [ ] `sudo apt autoremove`
- [ ] `sudo systemctl isolate multi-user.target`
- [ ] `sudo modprobe -r nvidia-drm nvidia-modeset nvidia`
- [ ] Установить `NVIDIA-Linux-x86_64-595.58.03.run` (open kernel module)
- [ ] `sudo reboot`
- [ ] `nvidia-smi` → проверить версию **595.58.03**
- [ ] `nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv`

## Этап 2: GCC 11

- [ ] `sudo apt install -y gcc-11 g++-11`
- [ ] `sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 200`
- [ ] `sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 200`
- [ ] `gcc --version` → **11.x**

## Этап 3: Системные зависимости

- [ ] `sudo apt install -y libegl1 libgl1 libopengl0 libxkbcommon0 libxcb-cursor0 libsm6 libice6 libxi6 libxrandr2 libxinerama1 libxcursor1 python3-pip python3-venv`

## Этап 4: Omniverse Launcher

- [ ] `wget https://install.launcher.omniverse.nvidia.com/installers/omniverse-launcher-linux.AppImage`
- [ ] `chmod +x omniverse-launcher-linux.AppImage`
- [ ] Установка
- [ ] Вход в NVIDIA Developer аккаунт

## Этап 5: Isaac Sim

- [ ] Library → Isaac Sim → Install → **6.0.1**
- [ ] Путь: `~/.local/share/ov/pkg/isaac_sim-2026.1.0`
- [ ] `./isaac-sim.sh` — тестовый запуск
- [ ] `./isaac-sim.sh --ros2` — проверка ROS2 bridge
- [ ] Проверить топики: `ros2 topic list`

## Этап 6: Terrain

- [ ] Открыть Heightmap Importer extension
- [ ] Загрузить occupancy map PNG
- [ ] Нажать Generate Heightmap
- [ ] Валидация: коллизия, визуал

## Этап 7: ROS2 интеграция

- [ ] Спавн робота через ROS2 bridge
- [ ] `/cmd_vel` → Isaac Sim
- [ ] `/odom`, `/scan`, `/tf` → ROS2
- [ ] Запуск elevation_mapping_cupy
- [ ] Проверка карты высот

## Этап 8: Docker

- [ ] `docker pull nvcr.io/nvidia/isaac-sim:6.0.1`
- [ ] Тестовый запуск контейнера
- [ ] compose.yml — секция isaac_sim
