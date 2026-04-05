# Отчёт: Оптимизация производительности WalkingRobotSim

**Дата:** 6 апреля 2026
**Ветка:** `fix-memory-performance` → `jazzy_cpp`
**Коммиты:** `21dc4598`, `b6dd93ba`, `5e0ba72f`, `c1dcf74f`, `79e36818`, `bec85c84`, `3b0827fb`, `1fa3ffdd`

---

## Часть 1: Python оптимизации

### Критические баги (исправлены)

| # | Файл | Проблема | Решение |
|---|------|----------|---------|
| 1 | `homogeneous_transforms.py` | `inverse = matrix` — мутация входных данных | `matrix.copy()` |
| 2 | `PIDController.py` | Два вызова `Time()` — рассинхрон sec/nsec | Один вызов, распаковка |
| 3 | `RobotController.py` | Дублирующие подписки на `robot_mode`/`robot_velocity` | Удалены (уже есть в узле) |

### Оптимизации Python

| # | Функция | Old (мс) | New (мс) | Δ% | Что изменилось |
|---|---------|:--------:|:--------:|:---:|:--------------|
| 1 | `rotxyz` | 0.0101 | 0.0025 | **-75.4%** | Аналитическая формула вместо 3 матриц + 2 dot |
| 2 | `forward_kinematics_all_legs (FK)` | 0.4419 | 0.0976 | **-77.9%** | Кэш статичных матриц, inline вычисления |
| 3 | `compute_local_positions` | 0.1306 | 0.0438 | **-66.5%** | Предвычисленная R_LEGS, np.empty вместо np.block |
| 4 | `GaitController.phase_ticks` | 0.0127 | 0.0000 | **-99.6%** | Кэш в `__init__` вместо пересчёта каждый тик |
| 5 | `homog_transform_inverse` | 0.0049 | 0.0048 | -3.4% | Поэлементное присваивание, без .copy() |
| 6 | `compute_all_joint_angles (IK)` | 0.0048 | 0.0031 | -33.9% | Lookup table, precalc констант, inline цикл |
| 7 | `Sliding average — old` | 0.0004 | 0.0005 | +2.7% | Статистический шум (~0.0001мс) |
| 8 | `Sliding average — new` | — | 0.0001 | — | `average_delta()` — O(1), только новая версия |
| | **ИТОГО** | **0.6053** | **0.1522** | **-74.9%** | |

---

## Часть 2: C++ пакет (quadropted_controller_cpp)

### Структура

```
src/quadropted_controller_cpp/
├── include/quadropted_controller_cpp/
│   ├── utils/           ← math_utils, rotation_matrices, homogeneous_transforms, message_builders
│   ├── kinematics/      ← forward_kinematics, inverse_kinematics
│   ├── odometry/        ← odometry (State + update)
│   ├── controllers/     ← PID, Gait, Rest, Stand, Trot*, Crawl*
│   ├── states/          ← State, Command, BehaviorState
│   └── *.hpp            ← алиасы для обратной совместимости
├── src/
│   ├── utils/    4 .cpp файла
│   ├── kinematics/  2 .cpp
│   ├── odometry/    2 .cpp
│   ├── controllers/ 9 .cpp
│   ├── states/      1 .cpp
│   └── nodes/       odometry_node.cpp, robot_controller_node.cpp
├── test/  8 gtest файлов
├── launch/
└── CMakeLists.txt, package.xml
```

**Итого:** 21 `.hpp` + 18 `.cpp` + 2 ROS узла + 8 тестов

---

## Часть 3: C++ vs Python Benchmark (5000 итераций)

> Сравнение производительности Python и C++ реализаций на идентичных входных данных.
> Запуск: `make bench-cpp`

| Функция | Python (мс) | C++ (мс) | Ускорение |
|---------|:-----------:|:--------:|:---------:|
| `rotxyz` | 0.0017 | 0.0002 | **10.4x** |
| `homog_transform_inverse` | 0.0079 | 0.0003 | **27.3x** |
| `FK` | 0.0882 | 0.0012 | **76.2x** |
| `IK` | 0.0030 | 0.0004 | **6.9x** |
| `local_positions` | 0.0415 | 0.0004 | **96.2x** |
| `GaitController.phase_ticks` | 0.0001 | 0.0000 | **6.2x** |
| `update_odometry` | 0.0021 | 0.0001 | **16.8x** |
| **ИТОГО** | **0.1443** | **0.0026** | **55.5x** |

### Почему такое ускорение?

| Функция | Причина ускорения |
|---------|-------------------|
| **local_positions (96x)** | Матричные операции Eigen3 vs NumPy, отсутствие overhead на создание временных массивов |
| **FK (76x)** | Прямые вычисления через Eigen без аллокаций, кэширование констант |
| **homog_transform_inverse (27x)** | Поэлементное присваивание в C++ vs np.dot + transpose в Python |
| **update_odometry (17x)** | C++ deque + прямое обращение vs Python deque + dict access |
| **rotxyz (10x)** | Аналитическая формула Eigen vs numpy array аллокации в Python |
| **IK (7x)** | Минимальная математика, Python уже быстр на простых операциях |
| **phase_ticks (6x)** | Python dict lookup vs C++ const reference |

---

## Часть 4: Корректность

### Кросс-языковой тест (12/12)

| Функция | Значений | Точность совпадения |
|---------|---------|-------------------|
| `rotxyz` | 9 | < 1e-05 |
| `homog_transform_inverse` | 16 | < 1e-10 |
| `FK.forward_kinematics_all_legs` | 12 | < 1e-05 |
| `IK.compute_all_joint_angles` | 12 | < 1e-05 |
| `compute_local_positions` | 12 | < 1e-05 |
| `GaitController.phase_ticks` | 4 | точное |
| `PID_controller.run` | 2 | < 1e-08 |
| `update_odometry` | 3 | < 1e-05 |
| `normalize_angle` | 5 | < 1e-05 |
| `build_quaternion_from_yaw` | 16 | < 1e-05 |
| `build_odometry_data` | 5 | < 1e-10 |
| `build_tf_data` | 3 | < 1e-05 |

### Тестовое покрытие

| Тест | Что проверяет | Результат |
|------|--------------|-----------|
| **gtest (8)** | C++ модульные тесты | **8/8 ✅** |
| **test-cross (12)** | Python vs C++ на одних данных | **12/12 ✅** |
| **test-correctness (34)** | Python old vs new | **34/34 ✅** |

---

## Как запускать

```bash
# Python тесты
make test-correctness   # Python old vs new (34 теста)
make test-benchmark     # Замер производительности Python
make test-cross         # Кросс-языковой тест Python vs C++ (12/12 + 8/8 gtest)

# C++ benchmark
make bench-cpp          # C++ vs Python benchmark (55.5x ускорение)

# Запуск симуляции
make gazebo-py          # Python контроллер
make gazebo-cpp         # C++ контроллер
```
