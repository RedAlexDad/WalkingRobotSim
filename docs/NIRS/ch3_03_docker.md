# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.3 Подготовка окружения и Docker-интеграция

### 3.3.1 Базовый образ и зависимости

GPU-образ собирается на основе официального образа NVIDIA CUDA `nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.10`. Выбор версии CUDA 12.6.3 обусловлен совместимостью с NVIDIA GTX 1650 Ti (Compute Capability 7.5, архитектура Turing) и поддержкой в CuPy CUDA 12.x [10].

В Dockerfile установлены следующие группы зависимостей.

Системные зависимости: build-essential, cmake, git для сборки C++ пакетов; python3-pip, python3-dev для Python-пакетов; поддержка X11 (libx11-dev, libgl1-mesa-dev) для RViz; языковые пакеты (locales, ru_RU.UTF-8).

Python-зависимости: CuPy 13.x (CUDA 12.x) — GPU-ядра для elevation mapping; numpy<2.0 — совместимость с CuPy JIT (numpy 2.0 ломает CuPy JIT); PyTorch (индекс cu126) — нейросетевые компоненты.

ROS 2-зависимости: ROS 2 Jazzy (base), устанавливаемый через apt; Cyclone DDS RMW — `rmw_cyclonedds_cpp`; пакеты `elevation_mapping_cupy`, `grid_map`, `rviz2`.

### 3.3.2 Проблемы совместимости и их решения

В ходе интеграции были выявлены и решены следующие проблемы.

**Проблема 1: CuPy JIT падает на numpy 2.x с GPU CC 7.5**

При использовании numpy >= 2.0 CuPy JIT-компиляция падает с ошибкой `AttributeError: module 'numpy' has no attribute 'int'`. Причина: CuPy JIT использует устаревшие атрибуты numpy (numpy.int, numpy.float), удалённые в numpy 2.0. Проблема проявляется на GPU с Compute Capability < 8.0 (включая GTX 1650 Ti CC 7.5). Решение: фиксация numpy<2.0 в requirements.txt.

**Проблема 2: PyTorch cu121 несовместим с CUDA 12.8 на хосте**

Официальные PyTorch wheels собираются для CUDA 12.1, в то время как на хосте установлена CUDA 12.8. При вызове CUDA-ядер возникает ошибка `CUDA driver version is insufficient`. Решение: использование PyTorch из индекса cu126 (собран для CUDA 12.6, совместим с 12.8 по обратной совместимости драйвера).

**Проблема 3: RViz падает с SIGSEGV в GPU-контейнере**

При запуске RViz в GPU-контейнере возникает segmentation fault в драйвере Mesa (Intel iGPU) при попытке доступа к шейдерному кэшу. Причина: в системе с гибридной графикой (Intel iGPU + NVIDIA dGPU) Mesa пытается кэшировать скомпилированные шейдеры, но не может создать файл в `/run/user/1000`, который не существует в контейнере. Решение: установка `MESA_GLSL_CACHE_DISABLE=true` и создание `/run/user/1000` в контейнере.

**Проблема 4: DDS discovery между контейнерами**

Ноды в разных контейнерах не обнаруживают друг друга, хотя используют один ROS_DOMAIN_ID и host network. Причина: Cyclone DDS использует Shared Memory (SHM) транспорт, который не работает между контейнерами [8]. Решение: отключение SHM в конфигурации Cyclone DDS, что заставляет использовать UDP на lo-интерфейсе, работающий через host network.

**Проблема 5: TF на namespaced топике**

Симулятор публикует трансформации на `/robot1/tf`, а elevation_mapping_node слушает `/tf`. Решение: создан Python-скрипт `tf_relay.py`, который подписывается на оба namespaced топика и републикует на `/tf` и `/tf_static` с корректными QoS-профилями.

### 3.3.3 Структура compose.yml

Корневой docker-compose.yml описывает оба сервиса. Конфигурация сервиса simulator содержит: образ `walking_robot_sim:latest`, сетевой режим host, переменные окружения DISPLAY, ROS_DOMAIN_ID=0, RMW_IMPLEMENTATION, монтирование X11 Unix-сокета, исходного кода, конфигурации Cyclone DDS и устройств `/dev/dri`. Сервису предоставлены привилегии privileged для доступа к графическим устройствам.

Конфигурация сервиса elevation содержит: образ `elevation_mapping_cupy:latest`, сетевой режим host, переменные окружения DISPLAY, ROS_DOMAIN_ID=0, RMW_IMPLEMENTATION, NVIDIA_VISIBLE_DEVICES=all, MESA_GLSL_CACHE_DISABLE=true, монтирование X11-сокета, исходного кода elevation_mapping_cupy, конфигурационных файлов, `/run/user/1000` для X11. Сервис использует `deploy.resources.reservations.devices` для резервирования NVIDIA GPU.

### 3.3.4 Запуск системы

Для запуска системы необходимо выполнить следующие шаги:

1) предоставить доступ к X11: `xhost +local:`;

2) собрать образы: `docker compose build`;

3) запустить оба контейнера: `docker compose up -d`;

4) войти в контейнер симулятора: `docker compose exec simulator bash`, запустить симуляцию Gazebo: `ros2 launch gazebo_sim walking_robot.launch.py`;

5) в отдельном терминале войти в elevation-контейнер: `docker compose exec elevation bash`, запустить elevation mapping: `ros2 launch elevation_mapping_cupy bot.launch.py`;

6) для визуализации: `rviz2 -d /ros_ws/config/elevation.rviz`.

### 3.3.5 Монтирование конфигурационных файлов

Для обеспечения гибкой настройки без пересборки образа конфигурационные файлы монтируются как volumes. К ним относятся: `core_param.yaml` (основные параметры elevation_mapping: resolution, map_length, min_valid_distance, max_ray_length), `go2_lidar3d.yaml` (robot-specific конфигурация: топики, фреймы, слои), `cyclonedds.xml` (конфигурация DDS для межконтейнерной связи) и `elevation.rviz` (конфигурация RViz для визуализации). Данный подход позволяет изменять параметры на лету и перезапускать ноду без пересборки Docker-образа [7].
