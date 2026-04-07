# Отчёт: Оптимизация памяти и производительности на Python

**Дата:** 5 апреля 2026
**Ветки:** `fix-memory-performance`
**Коммиты:** `21dc4598`, `b6dd93ba`

---

## Раунд 1: Критические баги и базовые оптимизации

### Критические баги (исправлены)

| #   | Файл                        | Проблема                                              | Решение                   |
| --- | --------------------------- | ----------------------------------------------------- | ------------------------- |
| 1   | `homogeneous_transforms.py` | `inverse = matrix` — мутация входных данных           | `matrix.copy()`           |
| 2   | `PIDController.py`          | Два вызова `Time()` — рассинхрон sec/nsec             | Один вызов, распаковка    |
| 3   | `RobotController.py`        | Дублирующие подписки на `robot_mode`/`robot_velocity` | Удалены (уже есть в узле) |

### Оптимизации раунда 1

| #   | Что                 | Было      | Стало       | Экономия |
| --- | ------------------- | --------- | ----------- | -------- |
| 4   | FK матрицы          | ~1400/сек | ~600/сек    | -57%     |
| 5   | Odometry msg        | 200/сек   | 0           | -200     |
| 6   | Marker msg          | 250/сек   | 0           | -250     |
| 7   | Sliding avg sum     | 4×O(n)×50 | 4×O(1)×50   | -93%     |
| 8   | `list(msg.data)`    | 50/сек    | 0 (inplace) | -50      |
| 9   | `Float64MultiArray` | 60/сек    | 0 (кэш)     | -60      |

---

## Раунд 2: Глубокая оптимизация hot path

### Векторизация и кэширование

| #   | Файл                   | Проблема                                                                                    | Решение                                                    | Влияние                             |
| --- | ---------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------- |
| 10  | `joint_angles.py`      | Python-цикл 4 ноги × 3 `.append()`                                                          | Векторизация `np.column_stack` для всех 4 ног              | 60 Гц × 12 итераций → 1 numpy-вызов |
| 11  | `GaitController.py`    | `phase_ticks`, `stance_ticks`, `swing_ticks`, `phase_length` — пересчёт констант каждый тик | Кэширование в `__init__`, lazy evaluation                  | 60 проверок/сек → 0                 |
| 12  | `RobotController.py`   | `default_stance` property — `np.array` при каждом обращении                                 | Кэш `_default_stance` в `__init__`, убран property         | 5+ аллокаций при инициализации → 1  |
| 13  | `rotation_matrices.py` | `rotxyz` = 3 матрицы 3×3 + 2 dot                                                            | Аналитическая формула Rx*Ry*Rz (9 элементов за 12 sin/cos) | 3 аллокации + 2 dot → 1 аллокация   |
| 14  | `local_positions.py`   | Тяжёлый `np.block` для простых данных                                                       | `np.empty` + прямое заполнение + исправление индексации    | Устранены накладные расходы block   |

### Переиспользование сообщений

| #   | Файл             | Проблема                                                                 | Решение                                       | Влияние                   |
| --- | ---------------- | ------------------------------------------------------------------------ | --------------------------------------------- | ------------------------- |
| 15  | `trot_gait.py`   | Двойная публикация `Twist` на один топик + `RobotFootContact` каждый тик | Одно `_velocity_msg`, кэш `_foot_contact_msg` | -120 аллокаций/сек (60×2) |
| 16  | `trot_swing.py`  | `np.array([1,1,0])` создаётся 2× за вызов                                | Класс-константа `_XY_MASK`                    | -240 аллокаций/сек        |
| 17  | `crawl_swing.py` | Аналогично trot_swing                                                    | Класс-константа `_XY_MASK`                    | -240 аллокаций/сек        |

### Ленивые вычисления

| #   | Файл                         | Проблема                                          | Решение                                                      | Влияние                       |
| --- | ---------------------------- | ------------------------------------------------- | ------------------------------------------------------------ | ----------------------------- |
| 18  | `robot_controller_gazebo.py` | `change_controller()` — 60 проверок/сек с if/elif | Флаг `_controller_change_needed`, вызов только при изменении | 60 проверок/сек → 0 (в покое) |

### Багфиксы

| #   | Файл                 | Проблема                                                       | Решение                                        |
| --- | -------------------- | -------------------------------------------------------------- | ---------------------------------------------- |
| 19  | `RestController.py`  | `temp = self.default_stance` без `.copy()` — мутация оригинала | `self.default_stance.copy()`                   |
| 20  | `trot_gait.py`       | `velocity[0] == 0` — сравнение float через `==`                | `np.abs(v) < 1e-9`                             |
| 21  | `PIDController.py`   | Создание `Time()` каждый вызов `run()`                         | Параметр `current_time` (optional)             |
| 22  | `local_positions.py` | Неправильная форма и индексация (`[:, i]` вместо `[i]`)        | Исправлено транспонирование + индексация строк |

---

## Сводная таблица всех оптимизаций (реальный benchmark)

> Данные получены из `src/tests/benchmark_performance.py` — 1500 итераций, замеры в отдельных процессах.
> Запуск: `make benchmark`

| #   | Функция                            |  Old (мс)  |  New (мс)  |     Δ%     | Что изменилось                                   |
| --- | ---------------------------------- | :--------: | :--------: | :--------: | :----------------------------------------------- |
| 1   | `rotxyz`                           |   0.0101   |   0.0025   | **-75.4%** | Аналитическая формула вместо 3 матриц + 2 dot    |
| 2   | `forward_kinematics_all_legs (FK)` |   0.4419   |   0.0976   | **-77.9%** | Кэш статичных матриц, inline вычисления          |
| 3   | `compute_local_positions`          |   0.1306   |   0.0438   | **-66.5%** | Предвычисленная R_LEGS, np.empty вместо np.block |
| 4   | `GaitController.phase_ticks`       |   0.0127   |   0.0000   | **-99.6%** | Кэш в `__init__` вместо пересчёта каждый тик     |
| 5   | `homog_transform_inverse`          |   0.0049   |   0.0048   |   -3.4%    | Поэлементное присваивание, без .copy()           |
| 6   | `compute_all_joint_angles (IK)`    |   0.0048   |   0.0031   |   -33.9%   | Lookup table, precalc констант, inline цикл      |
| 7   | `Sliding average — old`            |   0.0004   |   0.0005   |   +2.7%    | Статистический шум (~0.0001мс)                   |
| 8   | `Sliding average — new`            |     —      |   0.0001   |     —      | `average_delta()` — O(1), только новая версия    |
|     | **ИТОГО (paired)**                 | **0.6053** | **0.1522** | **-74.9%** |                                                  |

---

## Изменённые файлы (раунд 1 + раунд 2)

```
 src/quadropted_controller/scripts/ForwardKinematics/forward_kinematics.py     | 102 +++---
 src/quadropted_controller/scripts/InverseKinematics/joint_angles.py           |  40 ++-
 src/quadropted_controller/scripts/InverseKinematics/local_positions.py        |  15 +-
 src/quadropted_controller/scripts/QuadrupedOdometry/node_publishers.py        | 114 ++++---
 src/quadropted_controller/scripts/QuadrupedOdometry/node_subscriptions.py     |   3 +-
 src/quadropted_controller/scripts/QuadrupedOdometry/odometry_state.py         |  24 ++-
 src/quadropted_controller/scripts/QuadrupedOdometry/odometry_update.py        |  14 +-
 src/quadropted_controller/scripts/QuadrupedOdometryNode.py                    |   4 +
 src/quadropted_controller/scripts/RobotController/GaitController.py           |  30 +-
 src/quadropted_controller/scripts/RobotController/PIDController.py            |   4 +-
 src/quadropted_controller/scripts/RobotController/RestController.py           |   4 +-
 src/quadropted_controller/scripts/RobotController/RobotController.py          |  44 ++-
 src/quadropted_controller/scripts/RobotController/crawl_gait/crawl_swing.py   |   6 +-
 src/quadropted_controller/scripts/RobotController/trot_gait/trot_gait.py      |  35 +-
 src/quadropted_controller/scripts/RobotController/trot_gait/trot_swing.py     |   7 +-
 src/quadropted_controller/scripts/RoboticsUtilities/homogeneous_transforms.py |   2 +-
 src/quadropted_controller/scripts/RoboticsUtilities/rotation_matrices.py      |  21 +-
 src/quadropted_controller/scripts/robot_controller_gazebo.py                  |  10 +-
 18 files changed, 312 insertions(+), 186 deletions(-)
```
