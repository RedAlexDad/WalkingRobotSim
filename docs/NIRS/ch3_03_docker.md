# Глава 3. Разработка модуля Elevation Mapping и terrain-aware планирования

## 3.3 Подготовка окружения и Docker-интеграция

Воспроизводимость окружения является критическим требованием для робототехнических проектов, включающих множество зависимостей и специфичных версий библиотек. Для обеспечения изоляции и повторяемости проект использует Docker-контейнеризацию с двухконтейнерной архитектурой, разделяющей среду симуляции Gazebo и среду обработки данных. Первый контейнер отвечает за запуск симуляции и сбор сенсорных данных, второй — за выполнение алгоритмов elevation mapping и планирования. Такой подход позволяет перезапускать серверную часть без остановки симуляции и наоборот. В данном разделе описываются базовые образы, используемые зависимости и процесс сборки контейнеров.

### 3.3.1 Базовый образ и зависимости

GPU-образ собирается на основе официального образа NVIDIA CUDA `nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.10`. Выбор версии CUDA 12.6.3 обусловлен совместимостью с NVIDIA GTX 1650 Ti (Compute Capability 7.5, архитектура Turing) и поддержкой в CuPy CUDA 12.x [10].

В Dockerfile установлены следующие группы зависимостей.

Системные зависимости: build-essential, cmake, git для сборки C++ пакетов; python3-pip, python3-dev для Python-пакетов; поддержка X11 (libx11-dev, libgl1-mesa-dev) для RViz; языковые пакеты (locales, ru_RU.UTF-8).

Python-зависимости: CuPy 13.x (CUDA 12.x) — GPU-ядра для elevation mapping; numpy<2.0 — совместимость с CuPy JIT (numpy 2.0 ломает CuPy JIT); PyTorch (индекс cu126) — нейросетевые компоненты.

ROS 2-зависимости: ROS 2 Jazzy (base), устанавливаемый через apt; Cyclone DDS RMW — `rmw_cyclonedds_cpp`; пакеты `elevation_mapping_cupy`, `grid_map`, `rviz2`.

В ходе интеграции были выявлены и решены следующие проблемы совместимости.

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

Для разработки и отладки без GPU passthrough создан альтернативный Dockerfile (`Dockerfile.cpu`), базирующийся на официальном образе ROS 2 Jazzy. Пакет elevation_mapping_cupy работает в режиме CPU-fallback на чистом numpy, обеспечивая частоту обновления карты около 5 Гц — достаточно для отладки, но не для real-time навигации.

### 3.3.2 Структура compose.yml, запуск и конфигурация

Корневой `compose.yml` описывает оба сервиса. Для устранения дублирования общих полей (сетевой режим, переменные окружения, монтирования) применяются YAML-якоря:
```
&basic — базовые настройки (network_mode, restart, privileged);
&env_gui — переменные DISPLAY, X11-монтирования;
&elevation_common — общие для elevation-сервисов настройки (зависимости, конфиги).
```

Конфигурация сервиса simulator содержит: образ `walking_robot_sim:latest`, сетевой режим host, переменные окружения DISPLAY, ROS_DOMAIN_ID=0, RMW_IMPLEMENTATION, монтирование X11 Unix-сокета, исходного кода, конфигурации Cyclone DDS и устройств `/dev/dri`. Сервису предоставлены привилегии privileged для доступа к графическим устройствам.

Конфигурация сервиса elevation-gpu содержит: образ `elevation_mapping_cupy:latest`, сетевой режим host, переменные окружения DISPLAY, ROS_DOMAIN_ID=0, RMW_IMPLEMENTATION, NVIDIA_VISIBLE_DEVICES=all, MESA_GLSL_CACHE_DISABLE=true, монтирование X11-сокета, исходного кода elevation_mapping_cupy, конфигурационных файлов, `/run/user/1000` для X11. Сервис использует `deploy.resources.reservations.devices` для резервирования NVIDIA GPU.

Сервис elevation-cpu использует образ `elevation_mapping_cupy:cpu`, наследует общие настройки через YAML-якоря, но не требует GPU-устройств.

Для запуска системы необходимо выполнить следующие шаги:

1) предоставить доступ к X11: `xhost +local:`;

2) собрать образы: `make simulator-build` и `make elevation-build` (или `make elevation-cpu-build`);

3) запустить симулятор: `make simulator-bg`;

4) в отдельном терминале запустить elevation: `make elevation-bg` (или `make elevation-cpu-bg`);

5) для визуализации: `make elevation-rviz`;

Для обеспечения гибкой настройки без пересборки образа конфигурационные файлы монтируются как volumes. К ним относятся: `core_param.yaml` (основные параметры elevation_mapping: resolution, map_length, min_valid_distance, max_ray_length), `go2_lidar3d.yaml` (robot-specific конфигурация: топики, фреймы, слои), `cyclonedds.xml` (конфигурация DDS для межконтейнерной связи), `nav2_params.yaml` (параметры Nav2 planner и controller), `elevation_to_costmap.launch.py` (launch-файл моста) и `elevation.rviz` (конфигурация RViz для визуализации). Данный подход позволяет изменять параметры на лету и перезапускать ноду без пересборки Docker-образа [7].
