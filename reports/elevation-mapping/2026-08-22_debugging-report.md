# Отчёт: Диагностика и исправление проблем elevation + нативный запуск

## WalkingRobotSim — проблемы сессии 2026-08-22

### Дата: 2026-08-22

### Ветка: feat/rust-migration

---

## Оглавление

1. [Executive Summary](#1-executive-summary)
2. [Контекст](#2-контекст)
3. [Проблема 1: Сеть Docker — registry/pypi таймауты](#3-проблема-1-сеть-docker--registrypypi-таймауты)
4. [Проблема 2: nvidia-container-toolkit отсутствовал](#4-проблема-2-nvidia-container-toolkit-отсутствовал)
5. [Проблема 3: Нативный запуск elevation — cupy 14 + CUDA 13](#5-проблема-3-нативный-запуск-elevation--cupy-14--cuda-13)
6. [Проблема 4: Python 3.14 несовместимости в тестах](#6-проблема-4-python-314-несовместимости-в-тестах)
7. [Проблема 5: DDS-связка контейнер ↔ нативный код](#7-проблема-5-dds-связка-контейнер--нативный-код)
8. [Проблема 6: .bashrc — неверные пути ROS](#8-проблема-6-bashrc--неверные-пути-ros)
9. [Проблема 7: Сборка elevation-build — cupy float16](#9-проблема-7-сборка-elevation-build--cupy-float16)
10. [Проблема 8: Контроллер сломан — дубли ros2_control](#10-проблема-8-контроллер-сломан--дубли-ros2control)
11. [Проблема 9: RViz — meshes не отображались](#11-проблема-9-rviz--meshes-не-отображались)
12. [Проблема 10: SLAM-карта не сохранялась](#12-проблема-10-slam-карта-не-сохранялась)
13. [Проблема 11: Зомби-процессы и двойные симуляции](#13-проблема-11-зомби-процессы-и-двойные-симуляции)
14. [Проблема 12: Высота робота в RViz (z=0)](#14-проблема-12-высота-робота-в-rviz-z0)
14b. [Проблема 13: Ложные FAIL в тесте (устаревший ros2 daemon)](#14b-проблема-13-ложные-fail-в-интеграционном-тесте-устаревший-ros2-daemon)
15. [Сводная таблица проблем](#15-сводная-таблица-проблем)
16. [Коммиты сессии](#16-коммиты-сессии)
17. [Заключение](#17-заключение)

---

## 1. Executive Summary

За сессию 2026-08-22 выявлено и устранено **12 проблем** в стеке elevation mapping + Docker + нативный запуск. Ключевые:

1. **Сеть** — Docker registry/pypi недоступны через VPN (PPPoE) → решено `network: host` + `registry-mirror mirror.gcr.io`
2. **CUDA/cupy** — cupy 14.2 не компилирует float16 kernels с CUDA 13 → переведено на float/float32
3. **Python 3.14** — несовместимости в тестах (RecursionError, string annotations, cupy strict)
4. **Контроллер** — дублирующий ros2_control блок ломал `gz_ros2_control` → удалён
5. **RViz** — meshes не отображались (namespace, пути) → исправлены конфиги и volumes

Итог: **473 теста elevation проходят нативно** (GPU), контейнерная сборка работает, контроллеры стабильны.

---

## 2. Контекст

Проект использует два пути запуска elevation_mapping_cupy:
- **Docker** (`make elevation` / `elevation-build`) — образ на `nvidia/cuda:12.8.0-cudnn-devel-ubuntu24.04`
- **Нативный** (новый) — ROS Lyrical + Python 3.14 + cupy 14.2 на хосте Ubuntu 26.04

Хост — Ubuntu 26.04 (Resolute), интернет через PPPoE-VPN, доступ к зарубежным registry ограничен.

---

## 3. Проблема 1: Сеть Docker — registry/pypi таймауты

### Симптомы
- `docker pull nvidia/cuda:...` → `net/http: timeout awaiting response headers`
- `pip install cupy` внутри buildkit → таймаут
- curl с хоста работал, а Docker/apt внутри сборки — нет

### Причина
Интерфейс `ppp0` (PPPoE, MTU 1492) + IPv6-приоритет DNS. Docker не мог достучаться до `registry-1.docker.io`, pypi.org, packages.ros.org. `curl -4` работал, но Docker/apt использовали IPv4 через проблемный маршрут.

### Решение
```yaml
# compose.yml — сборка через host-сеть
build:
  context: ...
  network: host
```
```json
// /etc/docker/daemon.json — registry-mirror (решает VPN-блокировку)
{
  "mtu": 1400,
  "registry-mirrors": ["https://mirror.gcr.io"],
  "runtimes": { "nvidia": { "args": [], "path": "nvidia-container-runtime" } }
}
```
Дополнительно: `/etc/gai.conf` (предпочтение IPv4), `/etc/hosts` (IPv4 для registry).

**Ключевое:** `registry-mirror mirror.gcr.io` — основной фикс, найденный через анализ 24.04 ОС (там этот mirror уже был настроен).

---

## 4. Проблема 2: nvidia-container-toolkit отсутствовал

### Симптомы
- `make elevation-build` → «nvidia-container-toolkit не установлен»
- `nvidia-ctk` не найден

### Причина
Пакет был удалён/отсутствовал на 26.04 (в 24.04 — был установлен).

### Решение
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```
Проверено: `docker run --rm --gpus all nvidia/cuda:12.8.0-base nvidia-smi -L` → RTX 5070 Ti.

---

## 5. Проблема 3: Нативный запуск elevation — cupy 14 + CUDA 13

### Симптомы
- Kernel'ы с `float16` не компилируются: `error: incomplete type "float16"`
- raw-массивы как скаляры: `CArray<float> → int` конверсия не работает

### Причина
cupy 14.2 + CUDA 13 (nvrtc 13.0) строже: `float16` устарел, raw-массивы требуют `[0]`, ElementwiseKernel требует `size=`.

### Решение (в `kernels/`)
```python
# float16 → float (CUDA-тип)
__device__ float clamp(float x, ...)  # вместо float16

# raw-массивы как скаляры → [0]
image_width → image_width[0]
map_idx → map_idx[0]
x1 → x1[0], y1 → y1[0], z1 → z1[0]

# 2D-индексация polygon
polygon[j, 0]  # вместо polygon[j*2+0]

# Вызовы с size=
kernel(..., size=w*h)
```

---

## 6. Проблема 4: Python 3.14 несовместимости в тестах

### Симптомы
- `test_backend.py`: `RecursionError: maximum recursion depth exceeded` (monkeypatch `__import__`)
- `parameter.py`: `'str' object has no attribute '__name__'` (строковые аннотации)
- `_detect_cuda` не сбрасывал состояние при повторных вызовах

### Решение
- **test_backend.py**: сохранять `orig_import = builtins.__import__`, не вызывать `__import__` рекурсивно; удалять `cupy*` из `sys.modules` и переимпортировать; `monkeypatch.undo()` перед восстановлением
- **backend.py**: `_detect_cuda()` сбрасывает `GPU_AVAILABLE/cp/xp/scipy_ndimage` в начале
- **parameter.py**: `get_types()` обрабатывает и классы, и строковые аннотации

---

## 7. Проблема 5: DDS-связка контейнер ↔ нативный код

### Симптомы
Нативный Lyrical не видел топики контейнера Jazzy.

### Причина
- `CYCLONEDDS_URI` указывал на несуществующий `~/.cyclonedds.xml`
- Оба должны использовать CycloneDDS + `ROS_DOMAIN_ID=0`

### Решение
```bash
# Скопировать конфиг из проекта
cp src/docker/cyclonedds.xml ~/.cyclonedds.xml
# Оба: RMW_IMPLEMENTATION=rmw_cyclonedds_cpp, ROS_DOMAIN_ID=0
```
Проверено: pub в контейнере → echo нативно (и наоборот) работают. Связка `make gazebo` (контейнер) ↔ нативный elevation возможна.

---

## 8. Проблема 6: .bashrc — неверные пути ROS

### Симптомы
- `source /opt/ros/jazzy/setup.bash` — на хосте 26.04 нет Jazzy (только Lyrical)
- `CMAKE_PREFIX_PATH=/opt/unitree_robotics` — путь не существовал
- `~/ROS2/unitree_sdk2` — реально `~/ROS/unitree_sdk2`

### Решение (26.04 .bashrc)
```bash
# ROS2 (нативный Lyrical)
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/redalexdad/.cyclonedds.xml

# Unitree SDK + CycloneDDS (скопированы с 24.04)
export CMAKE_PREFIX_PATH=/opt/unitree_robotics:$CMAKE_PREFIX_PATH
export LD_LIBRARY_PATH=/home/redalexdad/ROS/unitree_sdk2/...:...
export CYCLONEDDS_HOME=/opt/cyclonedds

# Функция активации нативного elevation
elevation-native() { source /opt/ros/lyrical/setup.bash; export ... PYTHONPATH ...; }
```
Скопированы с 24.04: `/opt/unitree_robotics`, `/opt/cyclonedds`, `~/ROS/unitree_sdk2/thirdparty/lib/x86_64/`.

В 24.04 .bashrc исправлен путь `~/ROS2/` → `~/ROS/`.

---

## 9. Проблема 7: Сборка elevation-build — cupy float16

### Симптомы
- `elevation-force-build` падал на `pip install cupy`: `float16` в kernel'ах
- Сборка cupy из исходников шла ~30 минут

### Решение
Добавлен `network: host` в build-секцию elevation-сервисов compose. Образ собрался (29.8GB), контейнер запускается.

---

## 10. Проблема 8: Контроллер сломан — дубли ros2_control

### Симптомы
- `controller_manager: Tried to insert StateInterface with already existing key`
- Контроллеры не работали, TF odom не публиковался, симуляция нестабильна

### Причина
В `leg.xacro` был **отдельный** `ros2_control` блок для каждой ноги с **битым** плагином `gazebo_ros2_control/GazeboSystem` (правильный — `gz_ros2_control/GazeboSimSystem`). Изначально битый класс не загружался, поэтому конфликта не было. После исправления класса — оба блока (gazebo.xacro + leg.xacro) стали активными → дублирование интерфейсов.

### Решение
Удалён `ros2_control` блок из `leg.xacro` (все 12 joint уже объявлены в `gazebo.xacro`).

```bash
xacro robot.xacro robot_name:=robot1 | grep -c 'ros2_control name'  # 5 → 1
```
Проверено: odom публикуется 50 Гц, robot_controller_rust работает.

---

## 11. Проблема 9: RViz — meshes не отображались

### Симптомы
- `rviz: Could not load resource file:///root/ws/install/go2_description/meshes/hip.dae`
- `GLSL link error: indexed_8bit_image`

### Причина
- RViz в elevation-контейнере резолвил `package://go2_description` через `/root/ws/install/...` (путь из robot_description контейнера walking_robot_sim), но elevation-контейнер не имел доступа к `/root/ws`
- rviz config использовал `Description Topic: /robot_description` (без namespace)

### Решение (compose.yml)
```yaml
x-el-env:
  AMENT_PREFIX_PATH: "/ws/install/go2_description:/ws/install/go1_description"

x-el-volumes:
  - ./src/go2_description/:/ws/install/go2_description/share/go2_description/:ro
  - ./src/go1_description/:/ws/install/go1_description/share/go1_description/:ro

x-el-command:  # в команде контейнера
  sudo mkdir -p /root/ws/install
  sudo chmod o+x /root /root/ws /root/ws/install
  sudo ln -s /ws/install/go2_description /root/ws/install/go2_description
  sudo ln -s /ws/install/go1_description /root/ws/install/go1_description
```
RViz config (`nav2_default_view.rviz`, `rviz_ns.rviz`): `/robot_description` → `/robot1/robot_description`.

`GLSL error` — только при старте, не влияет на работу (0 повторений).

---

## 12. Проблема 10: SLAM-карта не сохранялась

### Симптомы
- `slam_toolbox: Failed to open file: /root/ws/maps/rust_slam_map`

### Причина
Каталог `/root/ws/maps` не существовал и не был в volumes.

### Решение
```yaml
volumes:
  - ./data/gazebo/maps:/root/ws/maps
```
Создан `data/gazebo/maps/`.

---

## 13. Проблема 11: Зомби-процессы и двойные симуляции

### Симптомы
- Множественные копии gz sim, slam_toolbox, ekf, rviz, parameter_bridge (процессы от разных запусков)
- Зомби-процессы (STAT=Z)
- Высокая нагрузка CPU, нестабильность

### Причина
Повторные `docker compose up`/`restart` без полной очистки накопили несколько симуляций в одном контейнере.

### Решение
```bash
# Полная очистка
docker exec walking_robot_sim bash -c "pkill -9 -f 'gz sim'; pkill -9 -f 'ros2 launch'; ..."
docker restart walking_robot_sim
# Запуск ОДНОЙ симуляции
ros2 launch gazebo_sim launch.launch.py use_sim_time:=true gui:=true
```

---

## 14. Проблема 12: Высота робота в RViz (z=0)

### Симптомы
- В 3D-режиме RViz видно, что map (z=0) «прорезает» корпус робота
- Робот физически на z≈0.46, но TF даёт z=0

### Причина
Одометрия (C++ и Rust) публикует `position.z = 0.0` (2D-навигация). EKF сливает z из odom → base_link на z=0. RViz рисует меш робота по TF → на земле.

### Статус
**Частично решено** — `Draw Behind: true` у Map уже есть. Для полного решения нужно либо поднять base_link в TF (сложно, ломает 2D-nav), либо EKF должен давать реальную высоту. Робот ходит корректно; визуальное пересечение map/тела — особенность 2D-карт в 3D-режиме.

---

## 14b. Проблема 13: Ложные FAIL в интеграционном тесте (устаревший ros2 daemon)

### Симптомы
- Тест показал **9 FAIL / 6 WARN** при полностью рабочей симуляции
- `ros2 topic echo --once` и обычный echo падали с traceback:
  ```
  xmlrpc.client.ResponseError: unknown tag 'rclpy.endpoint_info.TopicEndpointInfo'
  ```
  в `choose_qos()` → `get_publishers_info_by_topic()`
- При этом `ros2 topic hz` работал (50 Гц), топики публиковались, подписки существовали
- `ros2 param get` показывал `Parameter not set` для параметров, реально переданных через params-file

### Причина
Устаревший `ros2 daemon` (фоновый процесс discovery) кэшировал endpoint-info в формате, несовместимом с текущей версией rclpy. Команды CLI, требующие QoS-интроспекции (`topic echo`, `topic info -v`, `param get`), обращались к daemon по XMLRPC и падали на сериализации типа `TopicEndpointInfo`.

### Решение
```bash
ros2 daemon stop   # daemon перезапустится автоматически при следующем вызове CLI
```
- В `scripts/test_sim_integration.sh` добавлен `ros2 daemon stop` один раз перед проверками
- После рестарта: тест **42 ✅ | 0 ❌ | 1 ⚠️** (было 27/9/6)
- Оставшийся WARN «карта не расширилась» — индикатор (робот прошёл < клетки), не ошибка

### Вывод
Перед любым тестом, использующим `ros2 topic echo/--once/param`, обязательно `ros2 daemon stop` — это устраняет ложные ошибки XMLRPC без перезапуска симуляции.

---

## 15. Сводная таблица проблем
|---|----------|---------|---------|--------|
| 1 | Docker registry/pypi таймаут | VPN PPPoE + IPv6 | `network: host`, `mirror.gcr.io`, MTU 1400 | ✅ |
| 2 | nvidia-container-toolkit нет | пакет отсутствовал | apt установка + runtime configure | ✅ |
| 3 | cupy float16 не компилируется | cupy 14.2 + CUDA 13 | float → float, [0], size= | ✅ |
| 4 | Python 3.14 в тестах | RecursionError, annotations | фиксы test_backend/backend/parameter | ✅ |
| 5 | DDS контейнер↔нативный | нет ~/.cyclonedds.xml | копия конфига, Cyclone, domain 0 | ✅ |
| 6 | .bashrc неверные пути | Jazzy vs Lyrical, unitree | Lyrical + unitree/cyclonedds с 24.04 | ✅ |
| 7 | elevation-build cupy float16 | сборка из исходников | network: host | ✅ |
| 8 | Контроллер сломан | дубли ros2_control | удалён блок из leg.xacro | ✅ |
| 9 | RViz meshes не грузятся | namespace, пути | AMENT_PREFIX_PATH + symlink + volume | ✅ |
| 10 | SLAM-карта не сохраняется | нет /root/ws/maps | volume ./data/gazebo/maps | ✅ |
| 11 | Зомби/двойные симуляции | накопление процессов | pkill + docker restart | ✅ |
| 12 | Высота робота z=0 | 2D-одометрия | Draw Behind; полное — сложно | ⚠️ |
| 13 | Ложные FAIL в тесте — устаревший `ros2 daemon` | daemon кэширует endpoint-info в несовместимом формате → `ros2 topic echo/--once` падает `unknown tag 'TopicEndpointInfo'` | `ros2 daemon stop` в начале теста | ✅ |

---

## 16. Коммиты сессии

| Коммит | Содержание |
|--------|-----------|
| `cac0dc3` | Интеграционные тесты +10 проверок (частоты, EKF, lifecycle, TF) |
| `db7f9a0` | Модульные тесты core до 115, покрытие 97.40% |
| `e93fe5f` | Нативный запуск elevation (Lyrical + Py3.14 + CUDA13), 473 теста |
| `e64e716` | Фикс контроллера ros2_control, meshes rviz, SLAM maps |
| `d3b4999` | Отчёт по диагностике проблем |
| `(далее)` | Фикс ros2 daemon в тесте + правки отчёта |

---

## 17. Заключение

- **Нативный запуск elevation работает**: 473 теста, GPU (cupy 14.2), связка с контейнером через DDS
- **Docker-путь починен**: сборка через host-сеть + mirror, контроллеры стабильны
- **Итоговая архитектура**: симуляция (make gazebo) в контейнере, elevation нативно через `elevation-native()` — оба общаются через CycloneDDS domain 0

**Осталось:** полное решение высоты робота в RViz (проблема 12) — опционально для визуализации, не влияет на работу elevation.
