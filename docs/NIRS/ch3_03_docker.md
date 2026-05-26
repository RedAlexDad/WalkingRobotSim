# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.3 Подготовка окружения и Docker-интеграция

### 3.3.1 Базовый образ и зависимости

GPU-образ собирается на основе официального образа NVIDIA CUDA:

```
nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04
```

Выбор версии CUDA 12.6.3 обусловлен совместимостью с NVIDIA GTX 1650 Ti
(Compute Capability 7.5, архитектура Turing) и поддержкой в CuPy CUDA 12.x.

В Dockerfile установлены следующие группы зависимостей:

**Системные зависимости:**
- build-essential, cmake, git — для сборки C++ пакетов.
- python3-pip, python3-dev — для Python-пакетов.
- Поддержка X11 (libx11-dev, libgl1-mesa-dev) для RViz.
- Языковые пакеты (locales, ru_RU.UTF-8).

**Python-зависимости:**
- CuPy 13.x (CUDA 12.x) — GPU-ядра для elevation mapping.
- numpy<2.0 — совместимость с CuPy JIT (numpy 2.0 ломает CuPy JIT).
- PyTorch (индекс cu126) — нейросетевые компоненты (опционально).

**ROS 2 зависимости:**
- ROS 2 Jazzy (base) — устанавливается через apt.
- Cyclone DDS RMW — rmw_cyclonedds_cpp.
- Пакеты: elevation_mapping_cupy, grid_map, rviz2.

### 3.3.2 Проблемы совместимости и их решения

В ходе интеграции были выявлены и решены следующие проблемы:

**1. CuPy JIT падает на numpy 2.x с GPU CC 7.5**

При использовании numpy>=2.0 CuPy JIT-компиляция падает с ошибкой
`AttributeError: module 'numpy' has no attribute 'int'`.

*Причина:* CuPy JIT использует устаревшие атрибуты numpy (numpy.int,
numpy.float), удалённые в numpy 2.0. Проблема проявляется на GPU
с Compute Capability < 8.0 (включая GTX 1650 Ti CC 7.5).

*Решение:* пин numpy<2.0 в requirements.txt:
```
numpy<2.0
```

**2. PyTorch cu121 несовместим с CUDA 12.8 на хосте**

Официальные PyTorch wheels собираются для CUDA 12.1, в то время как
на хосте установлена CUDA 12.8. PyTorch cu121 загружает библиотеку
libcuda.so.1 и может работать, но при вызове CUDA-ядер возникает
ошибка `CUDA driver version is insufficient`.

*Решение:* использование PyTorch из индекса cu126 (собран для CUDA 12.6,
совместим с 12.8 по обратной совместимости драйвера):
```
pip install --index-url https://download.pytorch.org/whl/cu126 torch
```

**3. RViz падает с SIGSEGV в GPU-контейнере**

При запуске RViz в GPU-контейнере возникает segmentation fault
в драйвере Mesa (Intel iGPU) при попытке доступа к шейдерному кэшу.

*Причина:* в системе с гибридной графикой (Intel iGPU + NVIDIA dGPU)
Mesa пытается кэшировать скомпилированные шейдеры, но не может
создать файл в /run/user/1000 (не существует в контейнере).

*Решение:*
```bash
MESA_GLSL_CACHE_DISABLE=true
# Создание /run/user/1000 в контейнере
# xhost +local: на хосте для доступа к X11
```

**4. DDS discovery между контейнерами**

Node в разных контейнерах не обнаруживают друг друга, хотя используют
один ROS_DOMAIN_ID и host network.

*Причина:* Cyclone DDS использует Shared Memory (SHM) транспорт,
который не работает между контейнерами.

*Решение:*
```xml
<!-- cyclonedds.xml -->
<CycloneDDS>
    <Domain>
        <General>
            <Interfaces>lo</Interfaces>
        </General>
        <Internal>
            <SharedMemory>
                <Enable>false</Enable>
            </SharedMemory>
        </Internal>
    </Domain>
</CycloneDDS>
```

Отключение SHM заставляет Cyclone использовать UDP на lo interface,
который работает через host network.

**5. TF на namespaced топике**

Симулятор публикует трансформации на `/robot1/tf`, а elevation_mapping_node
слушает `/tf`.

*Решение:* создан Python-скрипт `tf_relay.py`, который подписывается
на оба namespaced топика и републикует на `/tf` и `/tf_static`
с корректными QoS профилями (TRANSIENT_LOCAL для статических).

### 3.3.3 Структура compose.yml

Корневой docker-compose.yml описывает оба сервиса:

```yaml
version: '3.8'
services:
  simulator:
    image: walking_robot_sim:latest
    build:
      context: .
      dockerfile: Dockerfile.sim
    network_mode: host
    environment:
      - DISPLAY=${DISPLAY}
      - ROS_DOMAIN_ID=0
      - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ./src/gazebo_sim:/ros_ws/src/gazebo_sim
      - ./cyclonedds.xml:/cyclonedds.xml
      - /usr/share/glvnd/egl_vendor.d:/usr/share/glvnd/egl_vendor.d:ro
    devices:
      - /dev/dri:/dev/dri
    privileged: true

  elevation:
    image: elevation_mapping_cupy:latest
    build:
      context: .
      dockerfile: Dockerfile.gpu
    network_mode: host
    environment:
      - DISPLAY=${DISPLAY}
      - ROS_DOMAIN_ID=0
      - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
      - NVIDIA_VISIBLE_DEVICES=all
      - MESA_GLSL_CACHE_DISABLE=true
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ./elevation_mapping_cupy:/ros_ws/src/elevation_mapping_cupy
      - ./config:/ros_ws/config
      - ./cyclonedds.xml:/cyclonedds.xml
      - /run/user/1000:/run/user/1000
    devices:
      - /dev/dri:/dev/dri
    privileged: true
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### 3.3.4 Инструкция по запуску

Для запуска системы выполнить:

```bash
# 1. Предоставить доступ к X11
xhost +local:

# 2. Собрать образы (если ещё не собраны)
docker compose build

# 3. Запустить оба контейнера
docker compose up -d

# 4. Войти в контейнер симулятора
docker compose exec simulator bash

# 5. Запустить симуляцию Gazebo
ros2 launch gazebo_sim walking_robot.launch.py

# 6. Войти в контейнер elevation (отдельный терминал)
docker compose exec elevation bash

# 7. Запустить elevation mapping
ros2 launch elevation_mapping_cupy bot.launch.py

# 8. Для визуализации
rviz2 -d /ros_ws/config/elevation.rviz
```

### 3.3.5 Монтирование конфигурационных файлов

Для обеспечения гибкой настройки без пересборки образа конфигурационные
файлы монтируются как volumes:

- `core_param.yaml` — основные параметры elevation_mapping
  (resolution, map_length, min_valid_distance, max_ray_length).
- `go2_lidar3d.yaml` — robot-specific конфигурация (топики, фреймы, слои).
- `cyclonedds.xml` — конфигурация DDS для межконтейнерной связи.
- `elevation.rviz` — конфигурация RViz для визуализации.

Это позволяет изменять параметры на лету и перезапускать ноду
без пересборки Docker-образа.
