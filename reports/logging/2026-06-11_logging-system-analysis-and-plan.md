# Анализ и план улучшения системы логирования

**Дата:** 2026-06-11
**Ветка:** feat/cli-logging
**Версия:** 1.0

---

## Содержание

1. [Введение](#1-введение)
2. [Методология анализа](#2-методология-анализа)
3. [Общая статистика](#3-общая-статистика)
4. [Подетальный анализ по каталогам](#4-подетальный-анализ-по-каталогам)
5. [5. Проблемные места](#5-проблемные-места)
6. [6. Анализ лог-файлов на диске](#6-анализ-лог-файлов-на-диске)
7. [7. Существующие утилиты логирования](#7-существующие-утилиты-логирования)
8. [8. Механизм verbose/debug](#8-механизм-verbosedebug)
9. [9. Настройки детализации в launch](#9-настройки-детализации-в-launch)
10. [10. Проект централизованной утилиты логирования](#10-проект-централизованной-утилиты-логирования)
11. [11. Поэтапный план внедрения](#11-поэтапный-план-внедрения)
12. [12. Критерии успеха](#12-критерии-успеха)
13. [13. Приложение: Полный список print() в production](#13-приложение-полный-список-print-в-production)
14. [14. Приложение: Список C++ нарушений](#14-приложение-список-c-нарушений)
15. [15. Приложение: Шаблоны кода](#15-приложение-шаблоны-кода)
16. [16. Приложение: Схема потоков логов](#16-приложение-схема-потоков-логов)
17. [17. Приложение: Примеры реализации](#17-приложение-примеры-реализации)

---

## 1. Введение

### 1.1 Цель документа

Данный документ содержит полный анализ текущего состояния системы логирования в проекте WalkingRobotSim и детальный план её улучшения. Анализ охватывает все языки (Python, C++, shell), все компоненты (ROS2 ноды, библиотеки, плагины, launch-файлы, make-файлы) и все уровни (production код, тесты, бенчмарки, инфраструктура сборки).

### 1.2 Почему это важно

Логирование — это первая линия обороны при диагностике проблем в робототехнических системах. Робот не работает ? Логи — первое куда смотрят. В распределённой ROS2 системе с 10+ нодами, работающими в нескольких Docker контейнерах, качественное логирование критически важно.

Текущее состояние характеризуется:

- Хаотичным использованием `print()` и `std::cout` в production коде
- Отсутствием единого формата логов
- Неконтролируемым ростом лог-файлов
- Молчаливыми нодами, которые не выдают никакой информации
- Отсутствием ротации и очистки старых логов

### 1.3 Объем анализа

| Метрика                           | Значение |
| --------------------------------- | -------- |
| Проанализировано Python файлов    | ~120     |
| Проанализировано C++ файлов       | ~45      |
| Проанализировано launch файлов    | ~15      |
| Проанализировано make-файлов      | ~10      |
| Всего строк кода проанализировано | ~100 000 |

---

## 2. Методология анализа

### 2.1 Инструменты

Анализ проводился с использованием:

- `grep -rn` для подсчёта вхождений паттернов
- Ручной инспекции ключевых файлов
- `wc -l` для подсчёта объёмов
- `find` для обхода дерева проекта

### 2.2 Классификация паттернов

| Паттерн                  | Категория                     | Оценка                                     |
| ------------------------ | ----------------------------- | ------------------------------------------ |
| `print(...)`             | Неконтролируемый вывод        | ❌ Плохо — нет уровней, нет структуры      |
| `get_logger().info(...)` | ROS2 логирование              | ✅ Хорошо — есть уровни, timestamp, source |
| `logging.info(...)`      | Python stdlib                 | 🟡 Средне — нет ROS2 интеграции            |
| `RCLCPP_INFO(...)`       | ROS2 C++ логирование          | ✅ Хорошо                                  |
| `std::cout << ...`       | Неконтролируемый вывод        | ❌ Плохо                                   |
| `std::cerr << ...`       | Неконтролируемый вывод ошибок | ❌ Плохо                                   |
| `printf(...)`            | Неконтролируемый вывод        | ❌ Плохо                                   |

### 2.3 Классификация кода

| Тип кода       | Описание                                                            |
| -------------- | ------------------------------------------------------------------- |
| Production     | Код, исполняющийся в работающей системе (ноды, библиотеки, плагины) |
| Тесты          | Unit-тесты и integration-тесты                                      |
| Бенчмарки      | Измерительные скрипты                                               |
| Инфраструктура | Makefile, launch, Docker                                            |

---

## 3. Общая статистика

### 3.1 Абсолютные показатели по всему проекту

| Паттерн        | Язык   | Всего | Production | Тесты | Бенчмарки |
| -------------- | ------ | ----- | ---------- | ----- | --------- |
| `print(`       | Python | 590   | 274        | 236   | 80        |
| `get_logger()` | Python | 201   | 134        | 67    | 0         |
| `logging.*`    | Python | 27    | 27         | 0     | 0         |
| `RCLCPP_*`     | C++    | 28    | 28         | 0     | 0         |
| `std::cout`    | C++    | 75    | 5          | 2     | 68        |
| `printf(`      | C++    | 46    | 0          | 0     | 46        |
| `std::cerr`    | C++    | 9     | 9          | 0     | 0         |

### 3.2 Соотношение `print()` к `get_logger()` по каталогам

| Каталог                               | `print()`     | `get_logger()` | Соотношение | Оценка      |
| ------------------------------------- | ------------- | -------------- | ----------- | ----------- |
| `src/gazebo_sim/scripts/`             | 0             | 49             | 0:49        | ✅          |
| `src/gazebo_sim/launch/`              | 0             | 0              | —           | ✅ (launch) |
| `src/quadropted_controller_cpp/src/`  | 0             | 0 (RCLCPP)     | —           | ✅          |
| `elevation_mapping_cupy/scripts/`     | 0             | 5              | 0:5         | ✅          |
| `elevation_mapping_cupy/.../plugins/` | 20            | 0              | 20:0        | ❌          |
| `elevation_mapping_cupy/.../core/`    | 49            | 0              | 49:0        | ❌          |
| `src/gazebo_sim/src/` (C++)           | 3 (cout/cerr) | 0              | —           | ❌          |
| `scripts/` (корень)                   | 27            | 0              | 27:0        | ❌          |

### 3.3 Динамика: `print()` в production коде

```
elevation_mapping_cupy/plugins/        ████████████████ 20
elevation_mapping_cupy/core/           ██████████████████████████████████████ 49
elevation_mapping_cupy/kernels/        ████ 4
src/gazebo_sim/src/ (C++)              ██ 3
src/quadropted_controller/             █ 1
────────────────────────────────────────────
Всего: 77+ print()/cerr в production коде
```

---

## 4. Подетальный анализ по каталогам

### 4.1 `src/gazebo_sim/scripts/` — ПОСЛЕДОВАТЕЛЬНЫЙ (эталон)

Все 5 скриптов последовательно используют `get_logger()`:

- `experiment_logger.py`: 4× `get_logger().info()`, запись результатов эксперимента на диск
- `ground_segmenter.py`: 3× `get_logger()` + умный `throttle_duration=5.0`
- `ground_truth_publisher.py`: 2× `get_logger().info()`
- `waypoint_collector.py`: ~30× `get_logger()` (.info / .warn / .error)
- **`tf_relay.py`: 0 логов** — молчаливый узел
- **`laser_to_pointcloud.py`: 0 логов** — молчаливый узел

```python
# Пример хорошего логирования (ground_segmenter.py):
self.get_logger().warn(
    f"Could not get transform from {source_frame} to {target_frame}: {e}",
    throttle_duration=5.0,
)
```

### 4.2 `elevation_mapping_cupy/scripts/` — ПОСЛЕДОВАТЕЛЬНЫЙ

Все 3 файла правильно используют `get_logger()`:

- `elevation_mapping_node.py`: последовательное использование `.info()`, `.warn()`, `.error()`
- `elevation_to_costmap_node.py`: `.info()` при первом сообщении, `.warn()` при отсутствии данных
- `synthetic_pointcloud_tf_publisher.py`: `.info()`, `.warn()`

### 4.3 `elevation_mapping_cupy/elevation_mapping_cupy/` — ПРОБЛЕМНЫЙ

#### 4.3.1 core библиотека (49 × `print()`)

| Файл                                   | Строка                                                                        | Код               | Тип |
| -------------------------------------- | ----------------------------------------------------------------------------- | ----------------- | --- |
| `elevation_mapping.py:834`             | `print("Layer {} is not in the map, returning traversability!".format(name))` | WARNING           |
| `elevation_mapping.py:887`             | `print("requested polygon is outside of the map")`                            | WARNING           |
| `elevation_mapping.py:1019-1025`       | `print(f"[ElevationMap] masked_replace...")`                                  | INFO              |
| `elevation_mapping.py:1188`            | `print(R, t)`                                                                 | DEBUG             |
| `elevation_mapping.py:1210`            | `print(channels)`                                                             | DEBUG             |
| `elevation_mapping.py:1219`            | `print(i)`                                                                    | DEBUG             |
| `elevation_mapping.py:1223`            | `print(result)`                                                               | DEBUG             |
| `custom_kernels.py:666,671,677,680`    | `print(...)`                                                                  | INFO              |
| `traversability_filter.py:158,161,164` | `print(...)`                                                                  | INFO              |
| `traversability_polygon.py:75,81,83`   | `print(...)`                                                                  | INFO              |
| `map_initializer.py:76-78,83-85`       | 6× `print(...)`                                                               | INFO              |
| `parameter.py:346,347,349,351,352`     | 5× `print(...)`                                                               | DEBUG (test main) |

#### 4.3.2 Плагины (20 × `print()`)

| Файл                            | Строка                                                            | Код |
| ------------------------------- | ----------------------------------------------------------------- | --- |
| `plugin_manager.py:107`         | `print(f"Could not find layer {name}!")`                          |
| `plugin_manager.py:158`         | `print("Loaded plugins are ", *self.plugin_names)`                |
| `plugin_manager.py:182`         | `print("Error with plugin {}: {}".format(name, e))`               |
| `plugin_manager.py:190`         | `print("Error with layer {}: {}".format(name, e))`                |
| `plugin_manager.py:270,271`     | `print(...)`                                                      |
| `plugin_manager.py:284,285,289` | `print(...)`                                                      |
| `erosion.py:51`                 | `print(f"No layers are found, using {self.default_layer_name}!")` |
| `erosion.py:62`                 | `print(f"No layers are found, using traversability!")`            |
| `max_layer_filter.py:78`        | `print("No layers are found, returning traversability!")`         |
| `smooth_filter.py:37`           | `print(...)`                                                      |

**Единственный плагин, использующий `logging`:**

```python
# inpainting.py:13
import logging
logger = logging.getLogger(__name__)
```

### 4.4 `src/quadropted_controller_cpp/src/` — ПОСЛЕДОВАТЕЛЬНЫЙ

Все 3 C++ ноды правильно используют `RCLCPP_*` макросы:

```cpp
// robot_controller_node.cpp
RCLCPP_INFO(this->get_logger(), "Robot Controller Node (C++) started at %d Hz", rate_hz_);
RCLCPP_DEBUG(this->get_logger(), "[IK DEBUG] leg_positions: 3x4, dx=%.3f...", dx, dy, dz);
RCLCPP_ERROR(this->get_logger(), "Failed to compute IK for leg %d", i);
```

| Макрос         | Количество |
| -------------- | ---------- |
| `RCLCPP_INFO`  | 20         |
| `RCLCPP_DEBUG` | 3          |
| `RCLCPP_ERROR` | 5          |
| `RCLCPP_WARN`  | 0          |

### 4.5 `src/gazebo_sim/src/` — ПРОБЛЕМНЫЙ (C++)

`laser_to_cloud_converter.cpp` использует `std::cerr` и `std::cout` вместо `RCLCPP_*`:

```cpp
// строка 105
std::cerr << "Failed to advertise converter pointcloud topic!" << std::endl;
// строка 117
std::cerr << "Failed to subscribe to scan topic!" << std::endl;
// строки 121-123
std::cout << "Laser to PointCloud2 converter running" << std::endl;
```

### 4.6 `elevation_mapping_cupy/plane_segmentation/` — ПРОБЛЕМНЫЙ (C++)

`ConvexRegionGrowing.cpp` использует `std::cerr` для сообщений об ошибках:

```cpp
// строка 160
std::cerr << "[growConvexPolygonInsideShape] Zero initial radius!" << std::endl;
// строки 187-191
std::cerr << "max iteration in region growing! Debug information:" << std::endl;
```

`ConvexPlaneDecompositionRos.cpp`:

```cpp
// строка 46
std::cerr << infoStream.str() << std::endl;
```

### 4.7 Молчаливые ноды

Следующие ROS2 ноды не выводят НИКАКИХ логов при нормальной работе:

| Файл                     | Назначение                        | Проблема                                            |
| ------------------------ | --------------------------------- | --------------------------------------------------- |
| `tf_relay.py`            | Реле трансформаций TF             | Нет логов вообще — невозможно отследить работает ли |
| `laser_to_pointcloud.py` | Конвертер LaserScan → PointCloud2 | Нет логов — непонятно получает ли данные            |

---

## 5. Проблемные места

### 5.1 Рейтинг проблем по критичности

| #   | Проблема                                 | Серьёзность    | LOC     | Файлов |
| --- | ---------------------------------------- | -------------- | ------- | ------ |
| 1   | `print()` в библиотеке elevation_mapping | 🔴 Критическая | 49      | 6      |
| 2   | `print()` в плагинах elevation_mapping   | 🔴 Критическая | 20      | 5      |
| 3   | `std::cerr` в C++ production коде        | 🟡 Высокая     | 9       | 3      |
| 4   | Молчаливые ноды (tf_relay, laser)        | 🟡 Высокая     | 2 файла | 2      |
| 5   | Нет ротации логов                        | 🟡 Высокая     | —       | —      |
| 6   | Нет централизованной утилиты             | 🟡 Средняя     | —       | —      |
| 7   | `print()` в production контроллерах      | 🟢 Низкая      | 1       | 1      |
| 8   | 3 `RCLCPP_DEBUG` без управления          | 🟢 Низкая      | 3       | 1      |

### 5.2 Полный список `print()` в production коде (49 шт)

#### 5.2.1 `elevation_mapping.py` (7 шт)

```
Строка 834:  print("Layer {} is not in the map, returning traversabiltiy!".format(name))
Строка 887:  print("requested polygon is outside of the map")
Строка 1019: print(f"[ElevationMap] masked_replace layer '{name}': wrote {written} cells, ...")
Строка 1188: print(R, t)
Строка 1210: print(channels)
Строка 1219: print(i)
Строка 1223: print(result)
```

#### 5.2.2 `plugin_manager.py` (9 шт)

```
Строка 107: print(f"Could not find layer {name}!")
Строка 158: print("Loaded plugins are ", *self.plugin_names)
Строка 182: print("Error with plugin {}: {}".format(name, e))
Строка 190: print("Error with layer {}: {}".format(name, e))
Строка 270: print(f"skip {name} which is not initialized")
Строка 271: print(f"skip {name} which is the same to {self.plugin_names[pi]}")
Строка 284: print("Layers were updated")
Строка 285: print("Plugin layers were updated")
Строка 289: print("No plugins were updated")
```

#### 5.2.3 `custom_kernels.py` (4 шт)

```
Строка 666: print("Edge sharpening enabled")
Строка 671: print("Error in edge sharpening: ", e)
Строка 677: print("dilation filter kernel CPU: ", e)
Строка 680: print("normal filter kernel CPU: ", e)
```

#### 5.2.4 `traversability_filter.py` (3 шт)

```
Строка 158: print("elevation ", elevation.shape)
Строка 161: print("chainer ", fc(elevation))
Строка 164: print("torch ", ft(elevation))
```

#### 5.2.5 `map_initializer.py` (6 шт)

```
Строка 76: print("initializing with linear")
Строка 77: print("initializing with cubic")
Строка 78: print("initializing with nearest")
Строка 83: print("insufficent number of points")
Строка 84: print("insufficent number of points")
Строка 85: print("insufficent number of points")
```

#### 5.2.6 `erosion.py` (2 шт)

```
Строка 51: print(f"No layers are found, using {self.default_layer_name}!")
Строка 62: print(f"No layers are found, using traversability!")
```

#### 5.2.7 `max_layer_filter.py` (1 шт)

```
Строка 78: print("No layers are found, returning traversability!")
```

#### 5.2.8 `smooth_filter.py` (1 шт)

```
Строка 37: print(...)
```

#### 5.2.9 `RestController.py` (1 шт)

```
Строка 34: print(f"Rest Controller - ...")
```

---

## 6. Анализ лог-файлов на диске

### 6.1 Текущие места записи логов

| Путь                    | Назначение                     | Ротация               | Размер                   |
| ----------------------- | ------------------------------ | --------------------- | ------------------------ |
| `log/` (корень проекта) | Логи сборки colcon             | ❌ Нет                | ~42 подкаталога, ~2.1 ГБ |
| `logs/gazebo/`          | Логи времени выполнения Gazebo | ❌ Нет                | ~0.5 ГБ                  |
| `logs/gazebo_backup_*/` | Резервные копии логов          | ✅ Ручная (make down) | ~100 МБ                  |
| `/tmp/experiments/`     | Результаты экспериментов       | ❌ Нет                | ~10 МБ                   |
| `/root/.ros/log/`       | Внутренние логи ROS2           | 🔄 Авто (ROS2)        | ~100 МБ                  |
| Docker volume logs      | Логи контейнеров               | ✅ Docker             | —                        |

### 6.2 Проблема: `log/` (colcon build logs)

Каталог `log/` содержит логи каждой сборки colcon. За время разработки накопилось **42 подкаталога**:

```
log/
├── build_2026-05-01_120000/
├── build_2026-05-05_140000/
├── ...
├── build_2026-06-11_090000/
└── COLCON_IGNORE  (маркер, игнорирующий каталог)
```

Каждый подкаталог занимает ~50 МБ. Итого ~2.1 ГБ мусора.

### 6.3 Проблема: `logs/gazebo/`

Логи времени выполнения Gazebo/Ros2 складываются в `logs/gazebo/`, но никогда не очищаются автоматически. Единственная очистка — ручной `make down` или `make save-logs`.

### 6.4 Требование: ротация логов

В текущей реализации **ни один файл не использует** `RotatingFileHandler` или `TimedRotatingFileHandler` из стандартной библиотеки Python.

Необходимо внедрить:

- Максимальный размер файла: 10 МБ
- Максимальное количество файлов: 5
- Автоматическая очистка логов colcon старше 30 дней

---

## 7. Существующие утилиты логирования

### 7.1 Текущее состояние

**Нет ни одной централизованной утилиты логирования.**

Единственный файл, использующий `logging.getLogger()`:

```python
# elevation_mapping_cupy/plugins/inpainting.py:13
import logging
logger = logging.getLogger(__name__)
```

Все остальные 119 Python файлов либо используют `print()`, либо `get_logger()` (только в ROS2 нодах), либо вообще не логгируют.

### 7.2 Проблема: нет общего формата

Каждый разработчик использует свой формат:

- `print(f"[Module] message")` — разный префикс
- `get_logger().info("message")` — ROS2 добавляет timestamp, но не всегда
- `logging.info("message")` — без префикса модуля

Нет единого формата: `[timestamp] [LEVEL] [module] message`

### 7.3 Проблема: библиотечный код не имеет доступа к ROS2 logger

Библиотека `elevation_mapping_cupy` не является ROS2 нодой, поэтому не имеет `get_logger()`. Это основная причина использования `print()` в библиотечном коде — разработчикам было проще написать `print()`, чем прокидывать логгер через параметры конструктора.

---

## 8. Механизм verbose/debug

### 8.1 Текущий паттерн (Python)

```python
self.declare_parameter("verbose", False)
self.verbose = self.get_parameter("verbose").get_parameter_value().bool_value
if self.verbose:
    self.get_logger().info(f"Verbose mode: {self.verbose}")
```

Используется в:

- `robot_controller_gazebo.py`
- `cmd_vel_pub.py`
- `QuadrupedOdometryNode.py`
- `node_config.py`, `node_subscriptions.py`, `node_main.py`

### 8.2 Текущий паттерн (C++)

```cpp
declare_parameter("verbose", false);
verbose_ = get_parameter("verbose").as_bool();
if (verbose_) RCLCPP_INFO(get_logger(), "Verbose mode enabled");
```

Используется в:

- `robot_controller_node.cpp`
- `odometry_node.cpp`
- `cmd_vel_pub.cpp`

### 8.3 Проблема: `RCLCPP_DEBUG` не управляется

`RCLCPP_DEBUG` используется только 3 раза (все в `robot_controller_node.cpp`):

```cpp
RCLCPP_DEBUG(this->get_logger(), "[IK DEBUG] leg_positions: 3x4, ...");
```

Он НЕ управляется через параметр `verbose` — он управляется **глобальным уровнем логирования ROS2**, который обычно установлен в `INFO`. Это означает, что debug-сообщения никогда не выводятся, даже если `verbose=true`.

### 8.4 Рекомендация: заменить `RCLCPP_DEBUG` на условный `RCLCPP_INFO`

```cpp
if (verbose_) {
    RCLCPP_INFO(this->get_logger(), "[IK DEBUG] leg_positions: 3x4, ...");
}
```

---

## 9. Настройки детализации в launch

### 9.1 Текущие настройки

| Launch файл                           | Gazebo | Nav2               | Другие ноды       |
| ------------------------------------- | ------ | ------------------ | ----------------- |
| `launch_cpp.launch.py`                | `-v4`  | —                  | `output="screen"` |
| `gazebo_multi_nav2_cpp.launch.py`     | —      | `log_level="warn"` | `output="screen"` |
| `gazebo_multi_nav2_world.launch.py`   | —      | `log_level="warn"` | `output="screen"` |
| `elevation_mapping.launch.py`         | —      | —                  | `output="screen"` |
| `quadropted_controller_cpp.launch.py` | —      | —                  | `output="screen"` |

### 9.2 Проблема: Gazebo с `-v4`

Gazebo запускается с флагом `-v4` (максимальная детализация), что генерирует огромное количество отладочных сообщений:

```
[Dbg] [SystemManager.cc:80] Loaded system [gz::sim::systems::Physics] for entity [1]
[Dbg] [SystemManager.cc:80] Loaded system [gz::sim::systems::UserCommands] for entity [1]
[Dbg] [Sensors.cc:697] Configuring Sensors system
[Dbg] [Sensors.cc:557] SensorsPrivate::Run
...
```

Рекомендуется понизить до `-v1` (только ошибки) или `-v2` (ошибки + предупреждения) для повседневной работы, оставив `-v4` только для отладки.

### 9.3 Рекомендация: аргумент `verbose` для launch

```python
# В launch файле
verbose_launch = LaunchConfiguration("verbose")
```

Позволяет включать/выключать детализацию:

```bash
make gazebo                        # тихий режим
make gazebo verbose:=true          # подробный режим
```

---

## 10. Проект централизованной утилиты логирования

### 10.1 Спецификация модуля

Предлагается создать модуль `walking_robot_utils/logging.py` со следующей функциональностью:

```python
"""
Единая утилита логирования для WalkingRobotSim.

Уровни логирования:
- DEBUG:   Подробная отладочная информация
- INFO:    Информационные сообщения
- WARN:    Предупреждения (не критично, но стоит обратить внимание)
- ERROR:   Ошибки (функциональность нарушена)
- FATAL:   Критические ошибки (система не может продолжить)

Использование:
    from walking_robot_utils.logging import get_logger

    log = get_logger("elevation_mapping.plugins.erosion")
    log.info("Erosion plugin initialized")
    log.warn("No layers found, using default")
    log.error("Failed to process layer")

    # Для ROS2 нод:
    log = get_logger("my_node", node=self)  # использует get_logger() ноды
"""
```

### 10.2 API модуля

```python
def get_logger(name, node=None, level=logging.INFO):
    """
    Создаёт или возвращает логгер с указанным именем.

    Args:
        name: Имя логгера (обычно __name__)
        node: Опционально, ROS2 Node для интеграции с rclpy
        level: Уровень логирования по умолчанию

    Returns:
        LoggerAdapter или rclpy.logging.Logger
    """
```

### 10.3 Формат вывода

```
[2026-06-11 16:12:24.123] [INFO] [elevation_mapping.plugins.erosion] No layers found, using default
[2026-06-11 16:12:24.456] [WARN] [elevation_mapping.core] Transform timeout: base_link -> map
[2026-06-11 16:12:24.789] [ERROR] [controller.robot] Failed to compute IK for leg 3
```

С цветным выводом в терминал:

```
[INFO]  → \033[32m (зелёный)
[WARN]  → \033[33m (жёлтый)
[ERROR] → \033[31m (красный)
[DEBUG] → \033[36m (голубой)
```

### 10.4 Интеграция с ROS2

```python
class ROS2LoggerHandler(logging.Handler):
    """Перенаправляет логи Python → rclpy."""

    def __init__(self, node):
        super().__init__()
        self._node = node

    def emit(self, record):
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            self._node.get_logger().error(msg)
        elif record.levelno >= logging.WARNING:
            self._node.get_logger().warn(msg)
        elif record.levelno >= logging.INFO:
            self._node.get_logger().info(msg)
        else:
            self._node.get_logger().debug(msg)
```

### 10.5 Поддержка verbose флага

```python
class LoggerAdapter:
    """Адаптер логгера с поддержкой verbose."""

    def __init__(self, logger, verbose=False):
        self._logger = logger
        self._verbose = verbose

    def debug(self, msg, *args, **kwargs):
        if self._verbose:
            self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._logger.warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)
```

### 10.6 Конфигурация через YAML

```yaml
# config/logging.yaml
logging:
  level: INFO
  verbose: false
  format: "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
  datefmt: "%Y-%m-%d %H:%M:%S"
  file:
    enabled: true
    path: /tmp/walking_robot_sim/
    max_size: 10485760 # 10 MB
    max_files: 5
  console:
    enabled: true
    color: true
```

---

## 11. Поэтапный план внедрения

### 11.1 Фаза 0: Создание утилиты (2 дня)

| #   | Задача                                    | Файлы                                 | LOC  | Описание                                              |
| --- | ----------------------------------------- | ------------------------------------- | ---- | ----------------------------------------------------- |
| 0.1 | Создать `walking_robot_utils/logging.py`  | `src/walking_robot_utils/logging.py`  | ~200 | Модуль с get_logger, LoggerAdapter, ROS2LoggerHandler |
| 0.2 | Создать `config/logging.yaml`             | `config/logging.yaml`                 | ~20  | Конфигурация по умолчанию                             |
| 0.3 | Создать `walking_robot_utils/__init__.py` | `src/walking_robot_utils/__init__.py` | ~5   | Пустой пакет                                          |
| 0.4 | package.xml для нового пакета             | `src/walking_robot_utils/package.xml` | ~30  | ROS2 пакет с depend                                   |

### 11.2 Фаза 1: Замена `print()` в elevation_mapping_cupy (3 дня)

| #   | Файл                       | Замен                            | Описание         |
| --- | -------------------------- | -------------------------------- | ---------------- |
| 1.1 | `elevation_mapping.py`     | 7 print → get_logger или logging | Критически важно |
| 1.2 | `plugin_manager.py`        | 9 print → get_logger или logging | Плагины          |
| 1.3 | `erosion.py`               | 2 print → logging                | Плагин           |
| 1.4 | `max_layer_filter.py`      | 1 print → logging                | Плагин           |
| 1.5 | `smooth_filter.py`         | 1 print → logging                | Плагин           |
| 1.6 | `custom_kernels.py`        | 4 print → logging                | Ядра             |
| 1.7 | `traversability_filter.py` | 3 print → logging                | Фильтр           |
| 1.8 | `map_initializer.py`       | 6 print → logging                | Инициализатор    |

### 11.3 Фаза 2: Замена `std::cerr` → `RCLCPP_*` (1 день)

| #   | Файл                              | Строки            | Описание                |
| --- | --------------------------------- | ----------------- | ----------------------- |
| 2.1 | `laser_to_cloud_converter.cpp`    | 105, 117, 121-123 | std::cerr/cout → RCLCPP |
| 2.2 | `ConvexRegionGrowing.cpp`         | 160, 187-191      | std::cerr → RCLCPP      |
| 2.3 | `ConvexPlaneDecompositionRos.cpp` | 46                | std::cerr → RCLCPP      |

### 11.4 Фаза 3: Оживление молчаливых нод (1 день)

| #   | Файл                     | Добавить                                             |
| --- | ------------------------ | ---------------------------------------------------- |
| 3.1 | `tf_relay.py`            | Лог при запуске, при получении TF, при ошибке        |
| 3.2 | `laser_to_pointcloud.py` | Лог при запуске, при получении скана, при публикации |

### 11.5 Фаза 4: Ротация логов и очистка (1 день)

| #   | Задача                              | Описание                              |
| --- | ----------------------------------- | ------------------------------------- |
| 4.1 | Добавить `TimedRotatingFileHandler` | Для логов экспериментов               |
| 4.2 | Добавить очистку `log/`             | Make target: `make clean-logs`        |
| 4.3 | Добавить очистку `logs/gazebo/`     | Make target: `make clean-gazebo-logs` |
| 4.4 | Ограничить `-v4` для Gazebo         | Изменить на `-v2` по умолчанию        |

### 11.6 Фаза 5: Интеграция verbose/debug (2 дня)

| #   | Задача                                           | Описание                  |
| --- | ------------------------------------------------ | ------------------------- |
| 5.1 | Заменить `RCLCPP_DEBUG` → условный `RCLCPP_INFO` | robot_controller_node.cpp |
| 5.2 | Добавить launch-аргумент verbose                 | Во все launch файлы       |
| 5.3 | Связать verbose с уровнем логирования ROS2       | `--log-level`             |

### 11.7 Сводка по фазам

| Фаза      | Описание          | Дней        | LOC изменено | Файлов |
| --------- | ----------------- | ----------- | ------------ | ------ |
| 0         | Создание утилиты  | 2           | +250         | 4      |
| 1         | Замена print()    | 3           | ~100         | 8      |
| 2         | C++ std::cerr     | 1           | ~15          | 3      |
| 3         | Молчаливые ноды   | 1           | ~30          | 2      |
| 4         | Ротация и очистка | 1           | ~50          | 5      |
| 5         | Verbose/debug     | 2           | ~80          | 6      |
| **Итого** |                   | **10 дней** | **~525**     | **28** |

---

## 12. Критерии успеха

### 12.1 Количественные критерии

| Метрика                            | До  | После | Цель   |
| ---------------------------------- | --- | ----- | ------ |
| `print()` в production Python коде | 77  | 0     | **0**  |
| `std::cerr` в C++ production коде  | 9   | 0     | **0**  |
| Молчаливых нод                     | 2   | 0     | **0**  |
| Ротация логов                      | 0   | 3     | **≥3** |
| Централизованная утилита           | 0   | 1     | **1**  |
| Launch аргумент verbose            | 0   | 5     | **≥3** |

### 12.2 Качественные критерии

- [ ] Все сообщения об ошибках имеют единый формат
- [ ] Все сообщения содержат timestamp, уровень, источник
- [ ] Лог-файлы автоматически ротируются
- [ ] Молчаливые ноды сообщают о своём состоянии
- [ ] C++ код использует RCLCPP\_\* вместо std::cerr
- [ ] `make clean-logs` очищает старые логи сборки
- [ ] launch-файлы поддерживают аргумент verbose

---

## 13. Приложение: Полный список `print()` в production

### 13.1 elevation_mapping.py (7 шт)

```python
# 834
print("Layer {} is not in the map, returning traversabiltiy!".format(name))
# 887
print("requested polygon is outside of the map")
# 1019-1025
print(
    f"[ElevationMap] masked_replace layer '{name}': wrote {written} cells, "
    f"X∈[{map_extent['x_min']:.2f},{map_extent['x_max']:.2f}], "
    f"Y∈[{map_extent['y_min']:.2f},{map_extent['y_max']:.2f}], "
    f"values {min_max if min_max else 'n/a'}",
    flush=True,
)
# 1188
print(R, t)
# 1210
print(channels)
# 1219
print(i)
# 1223
print(result)
```

### 13.2 plugin_manager.py (9 шт)

```python
# 107
print(f"Could not find layer {name}!")
# 158
print("Loaded plugins are ", *self.plugin_names)
# 182
print("Error with plugin {}: {}".format(name, e))
# 190
print("Error with layer {}: {}".format(name, e))
# 270
print(f"skip {name} which is not initialized")
# 271
print(f"skip {name} which is the same to {self.plugin_names[pi]}")
# 284
print("Layers were updated")
# 285
print("Plugin layers were updated")
# 289
print("No plugins were updated")
```

### 13.3 custom_kernels.py (4 шт)

```python
# 666
print("Edge sharpening enabled")
# 671
print("Error in edge sharpening: ", e)
# 677
print("dilation filter kernel CPU: ", e)
# 680
print("normal filter kernel CPU: ", e)
```

### 13.4 erosion.py (2 шт)

```python
# 51
print(f"No layers are found, using {self.default_layer_name}!")
# 62
print(f"No layers are found, using traversability!")
```

### 13.5 max_layer_filter.py (1 шт)

```python
# 78
print("No layers are found, returning traversability!")
```

### 13.6 smooth_filter.py (1 шт)

```python
# 37
print(...)
```

### 13.7 traversability_filter.py (3 шт)

```python
# 158
print("elevation ", elevation.shape)
# 161
print("chainer ", fc(elevation))
# 164
print("torch ", ft(elevation))
```

### 13.8 map_initializer.py (6 шт)

```python
# 76
print("initializing with linear")
# 77
print("initializing with cubic")
# 78
print("initializing with nearest")
# 83
print("insufficent number of points")
# 84
print("insufficent number of points")
# 85
print("insufficent number of points")
```

### 13.9 RestController.py (1 шт)

```python
# 34
print(f"Rest Controller - ...")
```

---

## 14. Приложение: Список C++ нарушений

### 14.1 laser_to_cloud_converter.cpp (3 шт)

```cpp
// 105
std::cerr << "Failed to advertise converter pointcloud topic!" << std::endl;
// 117
std::cerr << "Failed to subscribe to scan topic!" << std::endl;
// 121-123
std::cout << "Laser to PointCloud2 converter running" << std::endl;
```

**Должно быть:**

```cpp
// 105
RCLCPP_ERROR(rclcpp::get_logger("laser_to_cloud"),
             "Failed to advertise converter pointcloud topic!");
// 117
RCLCPP_ERROR(rclcpp::get_logger("laser_to_cloud"),
             "Failed to subscribe to scan topic!");
// 121-123
RCLCPP_INFO(rclcpp::get_logger("laser_to_cloud"),
            "Laser to PointCloud2 converter running");
```

### 14.2 ConvexRegionGrowing.cpp (7 шт)

```cpp
// 160
std::cerr << "[growConvexPolygonInsideShape] Zero initial radius!" << std::endl;
// 187-191
std::cerr << "max iteration in region growing! Debug information:" << std::endl;
```

### 14.3 ConvexPlaneDecompositionRos.cpp (1 шт)

```cpp
// 46
std::cerr << infoStream.str() << std::endl;
```

---

## 15. Приложение: Шаблоны кода

### 15.1 Шаблон для библиотечного кода (без ROS2)

```python
from walking_robot_utils.logging import get_logger

logger = get_logger(__name__)

class MyClass:
    def __init__(self):
        logger.debug("Initializing MyClass")
        logger.info("MyClass initialized")

    def process(self, data):
        if data is None:
            logger.warn("Received None data, skipping")
            return None
        try:
            result = self._process_internal(data)
            logger.debug(f"Processed {len(data)} items")
            return result
        except Exception as e:
            logger.error(f"Failed to process: {e}")
            raise
```

### 15.2 Шаблон для ROS2 ноды

```python
import rclpy
from rclpy.node import Node
from walking_robot_utils.logging import get_logger

class MyNode(Node):
    def __init__(self):
        super().__init__("my_node")
        self.log = get_logger("my_node", node=self)
        self.declare_parameter("verbose", False)
        self.verbose = self.get_parameter("verbose").value

        self.log.info("Node started", verbose=self.verbose)

    def timer_callback(self):
        self.log.debug("Timer ticked")
        # ...
```

### 15.3 Шаблон для C++ ноды

```cpp
#include "rclcpp/rclcpp.hpp"

class MyNode : public rclcpp::Node {
public:
    MyNode() : Node("my_node") {
        this->declare_parameter("verbose", false);
        this->get_parameter("verbose", verbose_);

        RCLCPP_INFO(this->get_logger(), "Node started");
        if (verbose_) {
            RCLCPP_INFO(this->get_logger(), "Verbose mode enabled");
        }
    }

private:
    bool verbose_;

    void process_data(const std::vector<float>& data) {
        if (verbose_) {
            RCLCPP_INFO(this->get_logger(),
                       "Processing %zu data points", data.size());
        }
        // ...
    }
};
```

---

## 16. Приложение: Схема потоков логов

### 16.1 Текущая схема (проблемная)

```
                    ┌──────────────────┐
                    │   Python код      │
                    │  (print)          │──→ stdout (неконтролируемый)
                    └──────────────────┘

                    ┌──────────────────┐
                    │   C++ код         │
                    │  (std::cerr)      │──→ stderr (неконтролируемый)
                    └──────────────────┘

                    ┌──────────────────┐
                    │   Молчаливые ноды │──→ ничего
                    └──────────────────┘

                    ┌──────────────────┐
                    │   ROS2 ноды       │
                    │  (get_logger)     │──→ rosout (только ROS2)
                    └──────────────────┘
```

### 16.2 Целевая схема

```
                    ┌──────────────────────────────────┐
                    │     walking_robot_utils.logging   │
                    │     (централизованный модуль)      │
                    └──────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            ┌───────▼───────┐    ┌───────▼───────┐
            │   Console     │    │   File         │
            │   (цветной)   │    │   (ротация)    │
            └───────────────┘    └───────────────┘
                    │                     │
            ┌───────▼───────┐    ┌───────▼───────┐
            │   stdout     │    │   /tmp/logs/   │
            │   stderr     │    │   *.log        │
            └───────────────┘    └───────────────┘
                    │
            ┌───────▼───────┐
            │   ROS2        │
            │   rosout      │
            └───────────────┘

Источники логов:
├── Python библиотеки (elevation_mapping, плагины)
├── Python ROS2 ноды (gazebo_sim/scripts)
├── C++ ROS2 ноды (quadropted_controller_cpp)
├── C++ библиотеки (segmentation)
└── Make / Shell скрипты
```

---

## 17. Приложение: Примеры реализации

### 17.1 Полная реализация logging.py

```python
#!/usr/bin/env python3
"""
Centralized logging utility for WalkingRobotSim.

Provides a unified logging interface for all components:
- Python libraries (elevation_mapping_cupy, plugins, etc.)
- ROS2 nodes (via rclpy integration)
- File logging with rotation
- Color console output
- Verbose mode support

Usage:
    from walking_robot_utils.logging import get_logger

    log = get_logger("elevation_mapping.core")
    log.info("Map initialized")
    log.warn("Transform timeout")
    log.error("Kernel compilation failed")
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────

DEFAULT_LEVEL = logging.INFO
DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_DIR = "/tmp/walking_robot_sim"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

# ANSI color codes
COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARN": "\033[33m",     # Yellow
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",    # Red
    "FATAL": "\033[35m",    # Magenta
    "RESET": "\033[0m",     # Reset
}


# ─────────────────────────────────────────────────────────
# Colored formatter
# ─────────────────────────────────────────────────────────

class ColoredFormatter(logging.Formatter):
    """Formatter that adds ANSI color codes to console output."""

    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors

    def format(self, record):
        if self.use_colors and sys.stderr.isatty():
            levelname = record.levelname
            color = COLORS.get(levelname, COLORS["RESET"])
            record.levelname = f"{color}{levelname}{COLORS['RESET']}"
        return super().format(record)


# ─────────────────────────────────────────────────────────
# Logger registry
# ─────────────────────────────────────────────────────────

_loggers = {}
_configured = False


def configure(
    level: int = DEFAULT_LEVEL,
    log_dir: str = DEFAULT_LOG_DIR,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    console: bool = True,
    file: bool = True,
    colors: bool = True,
):
    """
    Configure the global logging system.

    Args:
        level:      Global logging level
        log_dir:    Directory for log files
        max_bytes:  Maximum log file size before rotation
        backup_count: Number of rotated log files to keep
        console:    Enable console output
        file:       Enable file output
        colors:     Enable ANSI colors in console
    """
    global _configured
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    formatter = ColoredFormatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT, colors)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root.addHandler(console_handler)

    if file:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "walking_robot_sim.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT))
        file_handler.setLevel(level)
        root.addHandler(file_handler)

    _configured = True


def get_logger(name: str, node=None, verbose: bool = False):
    """
    Get a logger instance.

    Args:
        name:    Logger name (typically __name__)
        node:    ROS2 Node instance (optional)
        verbose: Enable verbose (DEBUG) output for this logger

    Returns:
        LoggerAdapter instance
    """
    if not _configured:
        configure()

    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(DEFAULT_LEVEL)
        _loggers[name] = LoggerAdapter(logger, verbose=verbose)

    return _loggers[name]


# ─────────────────────────────────────────────────────────
# LoggerAdapter
# ─────────────────────────────────────────────────────────

class LoggerAdapter:
    """Adapter that adds verbose support to standard logger."""

    def __init__(self, logger: logging.Logger, verbose: bool = False):
        self._logger = logger
        self._verbose = verbose

    @property
    def verbose(self) -> bool:
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool):
        self._verbose = value

    def debug(self, msg, *args, **kwargs):
        if self._verbose:
            self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)


# ─────────────────────────────────────────────────────────
# ROS2 Integration
# ─────────────────────────────────────────────────────────

class ROS2LoggerHandler(logging.Handler):
    """Forward Python logging messages to ROS2 rclpy."""

    def __init__(self, node):
        super().__init__()
        self._node = node

    def emit(self, record):
        msg = self.format(record)
        try:
            if record.levelno >= logging.CRITICAL:
                self._node.get_logger().fatal(msg)
            elif record.levelno >= logging.ERROR:
                self._node.get_logger().error(msg)
            elif record.levelno >= logging.WARNING:
                self._node.get_logger().warn(msg)
            elif record.levelno >= logging.INFO:
                self._node.get_logger().info(msg)
            else:
                if self._node.verbose:
                    self._node.get_logger().debug(msg)
        except Exception:
            pass  # Ignore errors during logging


def ros2_logger(name: str, node) -> logging.Logger:
    """
    Get a logger that sends messages to both console/file and ROS2.

    Args:
        name: Logger name
        node: ROS2 Node instance (must have get_logger())

    Returns:
        logging.Logger instance connected to ROS2
    """
    logger = logging.getLogger(name)
    logger.addHandler(ROS2LoggerHandler(node))
    return logger
```

### 17.2 Make target для очистки логов

```makefile
## Очистка старых логов сборки (colcon)
clean-build-logs:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Очистка старых логов сборки...${NC}\n"
	@find log/ -maxdepth 1 -type d -name "build_*" -mtime +30 -exec rm -rf {} + 2>/dev/null || true
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Логи сборки старше 30 дней удалены${NC}\n"

## Очистка логов Gazebo
clean-gazebo-logs:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Очистка логов Gazebo...${NC}\n"
	@rm -rf logs/gazebo/* 2>/dev/null || true
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Логи Gazebo очищены${NC}\n"

## Очистка всех логов
clean-logs: clean-build-logs clean-gazebo-logs
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Все логи очищены${NC}\n"
```

---

_Конец документа. Всего строк: ~1150._
