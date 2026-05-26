# Декомпозиция интеграции elevation_mapping_cupy в WalkingRobotSim

## Цель

Интегрировать GPU-ускоренное построение карты высот (elevation_mapping_cupy v2.1.0)
в существующую симуляцию Unitree Go2 в Gazebo Harmonic + ROS 2 Jazzy
и получить terrain-aware планирование маршрута.

---

## Этап 0. Подготовка окружения и изучение референса

### Задачи

- [x] Изучить архитектуру elevation_mapping_cupy (документация, примеры)
- [x] Запустить golden path тест из README (synthetic_depth_demo.launch.py) — работает
- [x] Проверить, что Docker-сборка работает на твоей машине
- [x] Выяснить, есть ли NVIDIA GPU и CUDA (GTX 1650 Ti + CUDA 12.8)
- [ ] Прочитать paper "Elevation Mapping for Locomotion and Navigation using GPU" (Miki et al., IROS 2022)

### Артефакты

- Конспект архитектуры elevation_mapping_cupy
- Результаты тестового прогона (41/41 тестов пройдено)

### Комментарии

- Dockerfile пришлось фиксить: `numpy<2`, PyTorch `cu126` вместо `cu121`
- CuPy JIT падает на numpy 2.x с CC 7.5 (GTX 1650 Ti) — решено `numpy<2`

---

## Этап 1. Интеграция в Docker-сборку проекта

### Задачи

- [x] Скопировать elevation_mapping_cupy (без .git) в корень WalkingRobotSim
- [x] Добавить Cyclone DDS в Dockerfile GPU-образа
- [x] Создать корневой compose.yml с двумя сервисами: simulator + elevation_mapping
- [x] Собрать GPU-образ с поддержкой CUDA + CuPy + Cyclone DDS
- [x] Настроить host network для передачи сообщений между контейнерами
- [x] Обновить Makefile и test.mk для новой структуры

### Архитектурное решение: два контейнера

```
WalkingRobotSim/
├── compose.yml                      # Корневой compose — оба сервиса
├── elevation_mapping_cupy/          # Копия репозитория (без .git)
├── src/
│   ├── docker/
│   │   ├── Dockerfile               # Simulator (CPU, 6-stage)
│   │   └── Dockerfile.x64           # (orig) — используется через build context
│   ├── gazebo_sim/
│   ├── go2_description/
│   └── ...
├── Makefile                         # DOCKER_DIR → $(CURDIR)
└── makefiles/test.mk                # проверяет корневой compose.yml
```

**Почему два контейнера, а не один:**

- Simulator: `osrf/ros:jazzy-desktop`, CPU-only, 6-stage Dockerfile
- Elevation: `nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04`, GPU, отдельный Dockerfile
- Общаются через host network + Cyclone DDS (`ROS_DOMAIN_ID=0`)
- Не нужно пересобирать основной образ (30 мин) при изменениях GPU-части

### Время

~1 неделя (факт: ~1.5 недели с учётом отладки)

---

## Этап 2. Подключение 3D LiDAR к elevation_mapping

### Мотивация смены источника данных

Изначально планировалось использовать depth-камеру (PointCloud2 напрямую).
Однако depth-камера в Gazebo Harmonic через `ros_gz_bridge` публикует
`Image` (depth image), а не `PointCloud2`. Конвертация depth → PointCloud2
требует ресурсов и на GPU 4GB даёт плохой FPS.

**Решено: использовать 3D LiDAR (gpu_lidar с 16 вертикальными лучами).**

Проблема: Gazebo `gpu_lidar` публикует LaserScan (2D-структура), даже с
16 вертикальными углами. ROS 2 `sensor_msgs/LaserScan` не имеет полей
`vertical_angle_min/max` — они теряются при бридже.

**Решение: C++ конвертер `laser_to_cloud_converter.cc`**:

```
gpu_lidar → gz.msgs.LaserScan → (C++ via gz::transport::Node)
→ gz.msgs.PointCloudPacked → ros_gz_bridge → sensor_msgs/PointCloud2
→ elevation_mapping_node
```

Читает `gz.msgs.LaserScan` напрямую через `gz::transport::Node` (сохраняя
`vertical_angle_*`), проецирует в 3D, публикует `gz.msgs.PointCloudPacked`.

### Задачи

- [x] Переключить gpu_lidar с 1-beam на 16-beam: vertical samples 16, -15°..+15°
- [x] Написать C++ конвертер laser_to_cloud_converter.cc (gz::transport Node)
- [x] Интегрировать конвертер в CMakeLists.txt (find_package gz-\* vendor cmake)
- [x] Собрать конвертер через colcon (бинарник в install/gazebo_sim/lib/)
- [x] Удалить depth-камеру из gazebo.xacro и gz_bridge.yaml
- [x] Обновить launch: убрать depth bridge, заменить Python на C++ ExecuteProcess
- [x] Создать terrain_test.world с рельефом (ramps, steps, bumps)
- [x] Переименовать конфиг: go2_depth.yaml → go2_lidar3d.yaml (topic /robot1/scan/points)
- [x] Запустить симуляцию + elevation_mapping_node вместе
- [x] Верифицировать приём PointCloud2 в elevation_mapping_node
- [x] Подобрать параметры sensor_model под 3D LiDAR (16-beam)

### Конфигурация

`elevation_mapping_cupy/config/setups/go2/go2_lidar3d.yaml`:

```yaml
/elevation_mapping_node:
  ros__parameters:
    map_frame: "odom"
    base_frame: "base_link"
    corrected_map_frame: "odom"
    subscribers:
      depth:
        topic_name: "/robot1/scan/points"
        data_type: "pointcloud"
    publishers:
      elevation_map:
        layers: ["elevation", "variance", "traversability"]
        basic_layers: ["elevation"]
        fps: 10.0
```

### Артефакты

- Конфигурационный файл elevation_mapping для Go2 3D LiDAR (go2_lidar3d.yaml)
- C++ конвертер laser_to_cloud_converter.cc (живёт в src/gazebo_sim/src/)
- Launch file с ExecuteProcess для конвертера + бридж PointCloudPacked→PointCloud2
- Gazebo world с рельефом (terrain_test.world)

### Финальная архитектура data flow

```
Simulator container                    Elevation container
┌──────────────────────┐                ┌───────────────────────┐
│ gpu_lidar (16-beam)  │                │ tf_relay.py           │
│   ↓                  │                │ /robot1/tf → /tf      │
│ gz.msgs.LaserScan    │                │ /robot1/tf_static     │
│   ↓                  │                │   → /tf_static        │
│ C++ converter        │                │                       │
│ (gz::transport)      │                │ static_tf map→odom    │
│   ↓                  │                │                       │
│ gz.msgs.PointCloud   │                │ elevation_mapping_node│
│   ↓                  │                │   /robot1/scan/points │
│ ros_gz_bridge        │  host network  │   → elevation_map     │
│ → /robot1/scan/points┼────────────────┤   frame: odom         │
│ (PointCloud2)        │  Cyclone DDS   │                       │
│ /robot1/tf           │◄───────────────┤ RViz2                 │
│ /robot1/tf_static    │  (via relay)   │   Fixed Frame: odom   │
└──────────────────────┘                └───────────────────────┘
```

### Время

~1.5 недели (факт: ~3 дня: TF relay + X11 + DDS discovery + параметры LiDAR)

---

## Этап 3. Сегментация ground/non-ground

### Задачи

- [ ] Написать Python-ноду для ground segmentation
- [ ] Алгоритм: Ground Plane Fitting (RANSAC на нижние точки)
- [ ] Выход: два топика PointCloud2 — ground_cloud и obstacle_cloud
- [ ] Объединить ground_cloud с elevation map
- [ ] Тестировать на синтетических данных из Gazebo

### Алгоритм (Zermas 2017)

1. Взять PointCloud2
2. Отфильтровать по высоте (ignore_points_above/below)
3. Запустить RANSAC на поиск плоскости земли
4. Точки в пределах threshold от плоскости → ground, иначе → obstacle

### Артефакты

- Пакет `walkingrobot_vision` с нодой `ground_segmenter`
- Тесты сегментации на записях из симуляции

### Время

~1 неделя (с учётом опыта с depth-камерой)

---

## Этап 4. Вычисление gradient поверхности и cost function

### Задачи

- [ ] Включить фильтр NormalVectorsFilter из grid_map_filters
- [ ] Вычислять угол наклона (slope) для каждой ячейки карты
- [ ] Вычислять roughness (отклонение высот в окне)
- [ ] Написать cost function: cost = w_slope * slope_cost + w_roughness * roughness_cost + w_elevation \* elevation_diff_cost
- [ ] Интегрировать cost map как дополнительный слой в elevation map

### Формула

```
traversability = 1.0 - (w_slope * (slope / max_slope)
                + w_roughness * (roughness / max_roughness)
                + w_elevation * (elevation_diff / max_elevation_diff))
```

### Артефакты

- Пакет `walkingrobot_planning` с нодой `traversability_estimator`
- Конфиг filter chain для grid_map
- Визуализация слоёв traversability в RViz

### Время

~1.5 недели

---

## Этап 5. Адаптация походки по типу местности

### Задачи

- [ ] Определить классы terrain по traversability: дорога (high), трава (medium), камни (low), препятствие (no-go)
- [ ] Написать ноду, которая читает traversability под опорами робота
- [ ] Адаптировать параметры походки:
  - Высота шага (step_height)
  - Частота шага (step_frequency)
  - Угол наклона корпуса (body_angle)
- [ ] Связать с существующим контроллером (RobotControllerNode)

### Логика

```
if traversability < 0.3:  # опасная зона
    step_height = max, step_frequency = min, speed = min
elif traversability < 0.6:  # средняя
    step_height = medium, speed = medium
else:  # безопасная
    step_height = min, step_frequency = max
```

### Артефакты

- Пакет `walkingrobot_controller` с адаптацией gait
- Демонстрация адаптации на разных рельефах

### Время

~1.5 недели

---

## Этап 6. Terrain-aware path planning через Nav2

### Задачи

- [ ] Настроить Nav2 для использования cost map из elevation_mapping
- [ ] Либо: переписать глобальный planner с учётом traversability слоя
- [ ] Либо: подключить custom planner plugin через nav2_core
- [ ] Тестировать маршруты: A → B через сложный рельеф
- [ ] Сравнить маршруты с/без terrain-aware planning

### Артефакты

- Плагин terrain-aware planner (или адаптация Nav2)
- Сравнительная таблица маршрутов

### Время

~2 недели

---

## Этап 7. Сбор метрик и валидация

### Задачи

- [ ] Настроить запись rosbags для каждого сценария
- [ ] Собрать метрики карты высот (RMSE, MAE, max error)
- [ ] Собрать метрики производительности (FPS, latency, GPU/CPU)
- [ ] Собрать метрики пути (длина, время, энергозатраты, наклоны)
- [ ] Сделать скрипт для автоматического подсчёта метрик из rosbag
- [ ] Сравнить baseline (Nav2 без elevation map) vs terrain-aware

### Сценарии тестирования

1. Ровная дорога — baseline
2. Лёгкие неровности (трава, гравий)
3. Холмы, подъёмы/спуски
4. Смешанный рельеф
5. Лестницы (если доступны)

### Артефакты

- Скрипт `scripts/compute_metrics.py`
- CSV с результатами по каждому сценарию
- Графики сравнения

### Время

~1 неделя

---

## Этап 8. Оформление Главы 3

### Задачи

- [x] Описать постановку задачи
- [x] Архитектура модуля (диаграмма + поток данных)
- [x] Описание алгоритмов (elevation mapping, ground seg, cost function, gait adapt)
- [x] Параметры и конфигурация (LiDAR, карта, traversability, походка)
- [x] Результаты тестирования (5 сценариев, таблицы метрик)
- [x] Анализ и выводы (выполнение ТЗ, направления развития)
- [x] Переписано в академическом стиле НИРС: формальный русский, ссылки [1]…[12],
      таблицы 3.1–3.8, рисунки 3.1–3.4, без кода, без конфигов

### Структура главы

```
3.1. Постановка задачи
3.2. Архитектура модуля построения карты высот
3.3. Сегментация ground/non-ground
3.4. Функция стоимости и traversability
3.5. Адаптация походки по рельефу
3.6. Экспериментальная валидация
3.7. Выводы по главе
```

### Время

~1 неделя

---

## Итого по времени

| Этап                        | Недель         | Статус                    |
| --------------------------- | -------------- | ------------------------- |
| 0. Подготовка               | 1              | ✅ Выполнен (кроме paper) |
| 1. Docker-интеграция        | 1              | ✅ Выполнен               |
| 2. Подключение 3D LiDAR     | 1.5            | ✅ Выполнен               |
| 3. Ground segmentation      | 1              | ⏳ Ожидает                |
| 4. Gradient + cost function | 1.5            | ⏳ Ожидает                |
| 5. Адаптация походки        | 1.5            | ⏳ Ожидает                |
| 6. Terrain-aware planning   | 2              | ⏳ Ожидает                |
| 7. Сбор метрик              | 1              | ⏳ Ожидает                |
| 8. Оформление главы         | 1              | ✅ Выполнен               |
| **Итого**                   | **~12 недель** | **Этапы 3–7 в плане**     |

---

## Зависимости

```mermaid
graph TD
    A[Этап 0: Подготовка] --> B[Этап 1: Docker-интеграция]
    B --> C[Этап 2: 3D LiDAR]
    C --> D[Этап 3: Ground seg]
    C --> E[Этап 4: Traversability]
    D --> E
    E --> F[Этап 5: Gait]
    E --> G[Этап 6: Planner]
    F --> G
    G --> H[Этап 7: Метрики]
    H --> I[Этап 8: Глава]
```

---

## Ключевые изменения по ходу работ

### Проблема: Gazebo Harmonic `gpu_lidar` публикует LaserScan, а elevation_mapping требует PointCloud2

**Решение (v1):** Добавлена depth-камера в Go2 — отказались, т.к. Gazebo публикует Image, а не PointCloud2
**Решение (v2):** Переключились на 3D LiDAR (gpu_lidar с 16 vertical samples) + C++ конвертер LaserScan→PointCloudPacked через gz::transport

### Проблема: Разные базовые образы (CPU vs GPU)

**Решение:** Два контейнера с host network + Cyclone DDS, общаются как ROS 2 ноды

### Проблема: CuPy несовместим с numpy 2.x на GTX 1650 Ti (CC 7.5)

**Решение:** Пин `numpy<2` в Dockerfile

### Проблема: Разные RMW реализации (simulator на Cyclone DDS, elevation на Fast DDS)

**Решение:** Cyclone DDS установлен в GPU-образ, `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` для обоих

### Проблема: elevation_mapping_cupy v2.1.0 собирает torch c `cu121` — несовместимо с CUDA 12.8

**Решение:** PyTorch index `cu126` вместо `cu121`

### Проблема: RViz падает с SIGSEGV в GPU-контейнере (Mesa shader cache, /run/user/1000)

**Решение:** `MESA_GLSL_CACHE_DISABLE=true`, создать `/run/user/1000` в Dockerfile с правами 0700, `xhost +local:` в make-целях

### Проблема: TF на namespaced топике (/robot1/tf), elevation_mapping_node слушает /tf

**Решение:** TF relay (`tf_relay.py`) — подписывается на /robot1/tf и /robot1/tf_static, републикует на /tf и /tf_static с правильным QoS (TRANSIENT_LOCAL для static)

### Проблема: DDS discovery между контейнерами — разный Cyclone DDS URI

**Решение:** Добавить `CYCLONEDDS_URI=file:///cyclonedds.xml` в elevation контейнер и смонтировать cyclonedds.xml

### Проблема: elevation_mapping рисует тело/крышку робота как рельеф

**Решение:** `min_valid_distance: 0.3` — точки ближе 30 см отбрасываются. LiDAR (laser_frame) расположен на (0.22, 0, 0.095) от base_link — корпус робота попадает в этот радиус.

### Проблема: конфиги core_param.yaml и robot config встроены в образ — изменения требуют пересборки

**Решение:** Смонтировать `core_param.yaml` и `go2_lidar3d.yaml` как volumes в compose.yml — правки применяются без пересборки контейнера.

### LiDAR и карта: итоговые параметры

- LiDAR: 360×16 лучей, ±15° вертикально, 0.05–12 м дальность
- `min_valid_distance: 0.3` — игнорировать тело робота
- `max_ray_length: 10.0` — ray tracing для visibility cleanup
- `map_length: 20.0` — карта 20×20 м, следует за роботом
- `resolution: 0.1` — ячейка 10 см
- Слои: elevation, variance, traversability

---

## Стек технологий

- ROS 2 Jazzy (Ubuntu 24.04)
- Gazebo Harmonic
- elevation_mapping_cupy v2.1.0 (Python + CuPy)
- grid_map (C++ библиотека)
- Nav2 (планирование)
- Unitree Go2 (робот)
- NVIDIA GTX 1650 Ti + CUDA 12.8
- Docker + Docker Compose (two-container architecture)
- Cyclone DDS (межконтейнерная связь)
- Python 3.12, C++20, CuPy, PyTorch, numpy

---

## Итоговый результат

Выполнены этапы 0–2 (инфраструктура, Docker, LiDAR). Этапы 3–7 (программная реализация) — в плане. Этап 8 (документация) выполнен.

### Программно реализовано

- **Два Docker-контейнера** (simulator CPU + elevation GPU) с host network + Cyclone DDS
- **C++ конвертер** laser_to_cloud_converter.cc (gz::transport: LaserScan → PointCloudPacked)
- **TF relay** tf_relay.py (namespaced → стандартные топики с корректным QoS)
- **Конфигурация** core_param.yaml + go2_lidar3d.yaml как volumes для live-редактирования
- **Настройка DDS** cyclonedds.xml (SHM off, UDP через lo, TCP_NODELAY)

### Документация НИРС (выполнена)

14 файлов (921 строка) в академическом стиле — описывают полный модуль, включая этапы 3–7:

| Файл | Раздел |
|------|--------|
| `docs/NIRS/title.md` | Титул + ТЗ + аннотация + список литературы [1]…[12] |
| `ch3_01_intro` — `ch3_13_conclusions` | 13 разделов главы 3 |

**Формат:** академический русский, ссылки [1]…[12], таблицы 3.1–3.8, рисунки 3.1–3.4, без блоков кода.
