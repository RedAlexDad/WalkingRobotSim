# Расхождение позиции робота: Gazebo vs RViz (Odometry Drift)

## Проблема

В симуляции робот физически застревает в террейне и не может двигаться, но его ноги продолжают совершать движения (ходьбу на месте). При этом:

- В **Gazebo** — робот стоит на месте, тело не перемещается в пространстве _(опционально: или тело всё же скользит по террейну)_
- В **RViz** — положение робота уезжает, координаты меняются
- **Odometry** продолжает интегрировать мнимое движение
- **Nav2** получает неверную одометрию и планирует маршруты относительно уехавшей позиции

## Root Cause Analysis

### Цепочка распространения ошибки

```
Gazebo Physics
  └─ robot stuck (collision with terrain, legs slip)
       └─ joint positions change (ноги двигаются)
            └─ Leg Odometry (forward kinematics + foot contacts)
                 ├─ вычисляет delta = foot_pos - prev_foot_pos
                 ├─ усредняет по 4 ногам
                 └─ интегрирует в мировые координаты (x, y, theta)
                      └─ топик /robot1/odom (remapped → /odometry/filtered)
                           └─ EKF (robot_localization)
                                ├─ fuse: leg odometry (x, y, z, vx, vy, yaw_vel)
                                ├─ fuse: IMU (orientation, angular_vel, accel)
                                └─ publish: /odometry/filtered + TF (odom→base_link)
                                     └─ RViz отображает уехавшую позицию
                                     └─ Nav2 планирует относительно неё
```

### Почему odometry не знает правды

| Компонент                          | Влияние                         | Комментарий                                                                                                        |
| ---------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Leg odometry (`odometry_node.cpp`) | 🔴 Интегрирует даже при stuck   | Алгоритм: если foot_contact = true, то body = foot_rel - prev_foot_rel. Ноги шевелятся → odometry считает движение |
| EKF (`ekf.yaml`)                   | 🔴 Доверяет leg odometry        | `odom0` config: x, y, z, vx, vy, yaw_vel — все `true`. Нет внешнего источника коррекции                            |
| AMCL (`nav2_amcl`)                 | 🟡 Правит map→odom, но медленно | Particle filter подтягивает глобальную позицию по лазерному скану, но лагает и не успевает за drift                |
| Gazebo TF bridge                   | 🟢 Только internal TF           | Публикует `base_link→laser_frame`, не world pose                                                                   |

### Конкретный сценарий

1. Робот идёт по террейну и упирается в препятствие (стенка, ступенька)
2. Gazebo Physics не даёт телу двигаться (collision)
3. Gait controller продолжает посылать позиции ног через `joint_group_controller/commands`
4. `gz_ros2_control` применяет эти позиции — ноги двигаются, тело нет
5. Leg odometry видит: foot_contact = true, foot_position изменилась → body moved
6. Интегрирует дельту → x, y растут
7. EKF подтверждает движение + IMU даёт правдоподобную ориентацию
8. RViz и Nav2 живут в "виртуальной" реальности

### Верификация: анализ логов Nav2 (AMCL drift)

#### Первая сессия: одометрия дрифтует, Gazebo ground truth неизвестен

При первом запуске симуляции и попытке планирования маршрута получены следующие логи:

```
[planner_server-21] [WARN] "Start Coordinates of(2.745979, -2.564980) was outside bounds"
[planner_server-21] [WARN] "Sensor origin at (2.74, -2.78) is out of map bounds (2.54, -2.46) to (22.49, 17.49)"
[robot_controller_node-11] cmd: vx=0.0000 vy=0.0000 ... pos: x=0.0000 y=0.0000 z=0.0000
```

**Что произошло (предположительно):**

| Величина                    | Значение            | Источник                          |
| --------------------------- | ------------------- | --------------------------------- |
| Odometry (robot_controller) | `(0, 0, 0)`         | Leg odometry через EKF            |
| AMCL map→odom               | `(2.75, -2.56)`     | Particle filter converged here    |
| Costmap bounds              | `(2.54, -2.46)` ... | Static map layer (карта мира)     |
| Робот (Gazebo physics)      | Неизвестна          | Ground truth publisher не работал |

#### Вторая сессия: Gazebo ground truth получен (26.05.2026)

Во второй сессии симуляция была запущена (`make gazebo-cpp`), робот сброшен (`make reset-pose`) и затем визуально сдвинут. **Gazebo ground truth был получен через `/world/default/dynamic_pose/info`:**

| Система             | X         | Y         | Z     | Yaw (qz)       | Источник данных                    |
| ------------------- | --------- | --------- | ----- | -------------- | ---------------------------------- |
| Gazebo ground truth | 2.818     | −4.092    | 0.460 | −0.707 (≈−90°) | `/world/default/dynamic_pose/info` |
| Odometry (EKF)      | 2.667     | −3.438    | 0.0   | −0.707 (≈−90°) | `/robot1/odometry/filtered`        |
| AMCL                | 2.832     | −3.580    | 0.0   | −0.699 (≈−89°) | AMCL output                        |
| Spawn position      | 0.0       | 0.0       | 0.5   | 0              | `reset-pose` / `spawn`             |
| Shift (GT − spawn)  | **+2.82** | **−4.09** | −0.04 | −90°           | —                                  |

**Наблюдения:**

1. **Три системы согласованы** — Gazebo, odometry и AMCL показывают близкие координаты. Нет "разрыва" между ними.
2. **Робот физически уехал** — Gazebo physics показывает (2.82, −4.09), а не (0, 0, 0.5). Ноги проскользнули по террейну, и тело реально сдвинулось.
3. **Odometry дрифтует относительно Gazebo** — odometry: (2.67, −3.44), Gazebo: (2.82, −4.09). Разница ≈ 0.7 м по Y — leg odometry насчитал меньше, чем реально проехал робот.
4. **IMU data flow работает корректно** — топик `/robot1/imu_plugin/out` публикуется Gazebo bridge'ом, odometry_cpp на него подписан.

**Вывод:** Дрифт одометрии реален, но он не единственная проблема. Робот **физически скользит** по террейну при старте (ноги разъезжаются, тело уезжает в сторону). Одометрия при этом тоже неточна (0.7 м расхождения по Y), но основная проблема — физическое скольжение тела в Gazebo.

### Ключевое открытие: Gazebo не публикует `/model/robot1_my_bot/pose`

При анализе Gazebo топиков выяснилось:

```
$ gz topic -l | grep pose
/model/robot1_my_bot/pose         ← топик существует в списке
/world/default/dynamic_pose/info   ← содержит позы ВСЕХ моделей
/world/default/pose/info           ← содержит позы ВСЕХ моделей

$ gz topic --info /model/robot1_my_bot/pose
Topic: /model/robot1_my_bot/pose
  Publishers: 0          ← Gazebo НЕ публикует на этот топик!
  Subscribers: 1         ← только bridge подписан
  Message count: 0       ← никогда не было сообщений
```

Gazebo Garden/Harmonic **не публикует** per-model pose топики автоматически, хотя список топиков включает `/model/robot1_my_bot/pose`. Publish появляется только если какой-то другой Gazebo компонент явно подписался и инициировал стриминг.

**Решение:** Bridged `/world/default/dynamic_pose/info` (тип `gz.msgs.Pose_V`) → `/world_poses_info` (тип `geometry_msgs/PoseArray`). Ground truth publisher подписан на оба топика и использует первый пришедший.

### Ground truth publisher: QoS mismatch

Исходный `ground_truth_publisher.py` подписывался с `RELIABLE` QoS:

```python
reliable_qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, ...)
```

Gazebo bridge по умолчанию использует `BEST_EFFORT`. При mismatch подписчик не видит сообщений.

**Фикс:** QoS → `BEST_EFFORT`. Дополнительно добавлен fallback через `/world_poses_info` с парсингом PoseArray и фильтром по имени модели.

### Stall detection: архитектура и ограничения

#### Реализация (этап 2, выполнено)

Stall detection добавлен в `update_odometry()` библиотеки `quadropted_controller_cpp`:

```
for each control cycle:
  compute delta = current_leg_pose - prev_leg_pose
  delta_mag = |delta|

  if delta_mag > STALL_DELTA_THRESHOLD (0.0001):
    if |imu_angular_velocity| < STALL_ANG_VEL_THRESHOLD (0.05 rad/s):
      stall_consecutive_count++
      if stall_consecutive_count >= stall_window:
        is_stalled = true
    else:
      stall_consecutive_count = 0

  if not is_stalled:
    integrate delta into position / orientation
  else:
    skip integration (delta = 0)
    if |imu_angular_velocity| > STALL_EXIT_ANG_VEL_THRESHOLD (0.15 rad/s):
      is_stalled = false
```

Параметры вынесены в odometry node:

- `stall_window` (дефолт: 5) — количество циклов подряд для входа в STALL
- `stall_ang_vel_threshold` (дефолт: 0.05) — порог угловой скорости для входа в STALL
- `stall_exit_ang_vel_threshold` (дефолт: 0.15) — порог для выхода из STALL

Сигнал `is_stalled` публикуется в `/stall_status` (`std_msgs/Bool`).

#### 🚨 Критическое ограничение: Stall detection НЕ срабатывает в REST mode

Stall detection требует `delta_mag > 0.0001` (ноги должны реально двигаться, чтобы появилась дельта). В режиме **REST** (робот стоит, gait controller не шлёт движения ног) дельта между циклами ≈ 0, поэтому stall никогда не войдёт.

**Когда stall НЕ поможет:**

| Сценарий                                 | delta_mag | ang_vel | Сработает STALL?         |
| ---------------------------------------- | --------- | ------- | ------------------------ |
| REST — ноги не двигаются, тело стоит     | ≈ 0       | ≈ 0     | ❌ (delta ≈ 0)           |
| TROT — упирается в стену, ноги циклируют | > 0.0001  | ≈ 0     | ✅                       |
| TROT — стартовое движение "вставание"    | > 0.0001  | ≈ 0     | ✅ (но нужно...)         |
| TROT — робот реально идёт                | > 0.0001  | > 0.05  | ❌ (ang_vel > threshold) |

**Проблема стартового дрифта:** При запуске симуляции ноги проходят переход из согнутого/стартового положения в рабочее. За это короткое время (первые секунды) ноги меняют конфигурацию → `delta_mag > 0` → stall может сработать, но **робот физически может реально скользить** по террейну в этот момент. После входа в REST (ноги на месте, режим ожидания) `delta_mag ≈ 0` и stall неактивен.

Stall detection решает **сценарий "уперся в стену при ходьбе"**, но не решает **стартовый дрифт** и **физическое скольжение тела в Gazebo**.

#### План по доработке stall detection для REST mode

Идея: детектить STALL не только по `delta_mag`, но и когда ноги не двигаются (`delta_mag ≈ 0`) при включённом режиме ходьбы, но с нулевым перемещением тела по IMU.

Вариант: если `gait_mode == WALK` (или команда ненулевая) И `delta_mag ≈ 0` И `|imu_angular_velocity| < threshold` И `|imu_linear_acceleration_xy| < threshold` → stalled.

Но это требует доступа к gait mode / cmd в odometry node.

## Текущие механизмы (недостаточны)

| Механизм                   | Что делает                             | Почему не спасает                                   | Статус                |
| -------------------------- | -------------------------------------- | --------------------------------------------------- | --------------------- |
| EKF                        | Сглаживает leg odometry + IMU          | Нет внешнего источника коррекции                    | Без изменений         |
| AMCL                       | Корректирует map→odom через laser scan | Дискретный, медленный, не точный для малых смещений | Без изменений         |
| Sliding window (14 sample) | Усредняет дельты                       | Сглаживает шум, не дрейф                            | Без изменений         |
| `OdometryState::reset()`   | Сброс одометрии в ноль                 | **Никогда не вызывается**                           | Без изменений         |
| Stall detection (новый)    | Не интегрирует delta при stuck         | Не срабатывает в REST (delta ≈ 0)                   | ✅ Скомпилирован      |
| Ground truth publisher     | Публикует Gazebo GT в ROS              | QoS mismatch (RELIABLE vs BEST_EFFORT)              | ✅ Починен + fallback |

## Статус решений

### ✅ Решение 1: Ground Truth Bridge (выполнено)

| Компонент                   | Статус       | Детали                                                                                  |
| --------------------------- | ------------ | --------------------------------------------------------------------------------------- |
| `gz_bridge.yaml`            | ✅ Выполнено | Добавлен bridge `/model/robot1_my_bot/pose` → `/robot1/pose_ground_truth`               |
| `gz_bridge.yaml`            | ✅ Выполнено | Добавлен bridge `/world/default/dynamic_pose/info` → `/world_poses_info` (fallback)     |
| `ground_truth_publisher.py` | ✅ Выполнено | QoS BEST_EFFORT, подписка на `/world_poses_info` (PoseArray, фильтр по `robot1_my_bot`) |

### ✅ Решение 2: Заморозка odometry (stall detection) — выполнено (compiled)

Stall detection реализован в `odometry_update.cpp`, скомпилирован в `quadropted_controller_cpp`.
**Не протестирован** в симуляции — требуется новый запуск `make gazebo-cpp`.

### ❌ Решение 3: Reset odometry по сервису — не начато

Требует:

- `src/quadropted_msgs/srv/ResetOdometry.srv`
- Service server + reset вызов в odometry node

### ❌ Решение 4: Автокоррекция по ground truth — не начато

Требует этап 3 (reset) + подписку на ground truth в odometry node.

### ❌ Решение 5: AMCL tuning — не начато

## Рекомендация (обновлённая)

1. ✅ **Решение 1 (Ground Truth Bridge)** — выполнено, ожидает тестирования (1.7)
2. ✅ **Решение 2 (Stall Detection)** — выполнено, скомпилировано, ожидает тестирования
3. ❓ **Новая проблема: физическое скольжение тела в Gazebo** — stall detection не решает стартовый дрифт. Нужно либо:
   - Улучшать stall detection: детектить STALL не только по `delta_mag`, но и по отсутствию продвижения тела при работающих ногах (IMU-based standstill detection)
   - Либо разбираться с физикой Gazebo (трение ног, контактные параметры, масса робота)

## Lessons Learned

### 1. `ground_truth_publisher.py` — shebang и create_timer

При первом запуске ground truth publisher упал с ошибками:

- **"Exec format error"** — отсутствовал shebang `#!/usr/bin/env python3`. Исполняемые Python-скрипты в ROS2 **обязательно** должны иметь shebang.
- **`create_wall_timer()` не существует** — использовался C++ API (`rclcpp::WallTimer`). В Python `rclpy` нужно **`create_timer()`**.

**Статус:** Исправлено в `src/gazebo_sim/scripts/ground_truth_publisher.py`.

### 2. `nav2_params.yaml` — `topic` vs `map_topic` в StaticLayer

Nav2 `StaticLayer` читает параметр **`map_topic`**, а не `topic`. Если указать `topic: "/elevation_costmap"`, параметр игнорируется и StaticLayer подписывается на `/map` (значение по умолчанию). Subscription count на `/elevation_costmap` остаётся 0.

**Фикс:** `topic:` → `map_topic:` в обоих экземплярах (global + local costmap).

### 3. Gazebo не публикует `/model/name/pose` автоматически (26.05.2026)

Gazebo Garden/Harmonic создаёт топик `/model/robot1_my_bot/pose` в списке (`gz topic -l`), но **не публикует** на него данные. Publishers = 0, Message count = 0.

Для получения ground truth нужно использовать `/world/default/dynamic_pose/info` (`gz.msgs.Pose_V`) — он содержит позы всех моделей в мире.

### 4. QoS mismatch между Gazebo bridge и ROS2 подписчиком (26.05.2026)

`ros_gz_bridge` по умолчанию публикует ROS-сообщения с `BEST_EFFORT` QoS. Если ROS-подписчик использует `RELIABLE`, сообщения не доставляются.

**Фикс:** Всегда использовать `BEST_EFFORT` для топиков от Gazebo bridge:

```python
qos = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)
```

### 5. Stall detection не панацея (26.05.2026)

Stall detection требует `delta_mag > 0` (ноги должны двигаться). В REST mode `delta_mag ≈ 0`, поэтому stall не войдёт.

**Вывод:** Для режима ожидания (REST) нужен отдельный механизм детекции, либо stall detection должен работать и на `delta_mag ≈ 0` при наличии ненулевой команды движения.

### 6. Робот может реально скользить в Gazebo, не только дрифт одометрии (26.05.2026)

Сравнение Gazebo GT (2.82, −4.09) и spawn (0, 0, 0.5) показало, что тело робота физически переместилось. Это не только "одометрия дрифтует", а ещё и "Gazebo physics позволяет ногам проскальзывать".

**Возможные причины скольжения:**

- Недостаточное трение лап о террейн (mu, mu2 в SDF)
- Слишком большая масса робота
- Неправильная конфигурация контактов (force threshold, contact stiffness/damping)
- Ноги "разъезжаются" при старте из-за неоптимального initial joint config

**Что можно сделать:**

- Проверить параметры фрикции в SDF/model.sdf
- Уменьшить массу робота
- Увеличить mu контакта в Gazebo
- Откалибровать начальную позу ног, чтобы они сразу стояли устойчиво

## Relevant Files

| Файл                                                                                    | Роль                                                                           |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `src/gazebo_sim/config/ekf.yaml`                                                        | Конфигурация EKF (odom0, imu0)                                                 |
| `src/gazebo_sim/config/gz_bridge.yaml`                                                  | Bridge Gazebo↔ROS (теперь есть ground truth + world_poses_info)                |
| `src/gazebo_sim/scripts/ground_truth_publisher.py`                                      | Ground truth: Pose → Odometry + TF (BEST_EFFORT + fallback world_poses)        |
| `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py`                                 | Launch-файл C++ контроллеров                                                   |
| `src/gazebo_sim/launch/gazebo_multi_nav2_world.launch.py`                               | Launch-файл Python контроллеров                                                |
| `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`                             | C++ нода одометрии (stall params, IMU callback, /stall_status)                 |
| `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp`                        | Алгоритм leg odometry (stall detection logic)                                  |
| `src/quadropted_controller_cpp/src/odometry/odometry_state.cpp`                         | OdometryState::reset() — очищает stall state                                   |
| `src/quadropted_controller_cpp/include/quadropted_controller_cpp/odometry_state.hpp`    | OdometryState (реэкспорт `odometry.hpp`)                                       |
| `src/quadropted_controller_cpp/include/quadropted_controller_cpp/odometry/odometry.hpp` | OdometryState struct (is_stalled, stall_consecutive_count, stall_window, etc.) |
| `compose.yml`                                                                           | Docker compose                                                                 |

---

## Декомпозиция работ

### Этап 1 — Ground Truth Bridge (диагностика)

**Цель:** Визуализировать расхождение между Gazebo ground truth и leg odometry в RViz.

| №                | Задача                                                                                       | Файл(ы)                                                                                                                                             | Оценка      | Статус                                                          |
| ---------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------- |
| 1.1              | Исследовать Gazebo топики: `gz topic -l`, найти `/model/*/pose` и `/world/*/pose/info`       | —                                                                                                                                                   | 0.5 дня     | ✅                                                              |
| 1.2              | Добавить bridge `/model/robot1_my_bot/pose` → `/robot1/pose_ground_truth` в `gz_bridge.yaml` | `src/gazebo_sim/config/gz_bridge.yaml`                                                                                                              | 0.5 дня     | ✅                                                              |
| 1.3              | Написать ноду `ground_truth_publisher.py`: Pose → Odometry + TF (gt_odom→base_link_gt)       | `src/gazebo_sim/scripts/ground_truth_publisher.py`                                                                                                  | 1 день      | ✅ (баги исправлены: shebang + create_timer)                    |
| 1.4              | Добавить ground_truth_publisher в launch-файлы (cpp + world)                                 | `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py`, `src/gazebo_sim/launch/gazebo_multi_nav2_world.launch.py`, `src/gazebo_sim/CMakeLists.txt` | 0.5 дня     | ✅                                                              |
| 1.5              | Volume mount (compose.yml)                                                                   | `compose.yml`                                                                                                                                       | 0.5 дня     | ⏸️ Не требуется (уже смонтировано)                              |
| 1.6              | Добавить отображение ground truth в RViz (TF + Odometry display)                             | `src/gazebo_sim/rviz/multi_nav2_default_view.rviz`                                                                                                  | 0.5 дня     | ✅                                                              |
| 1.7              | Тестирование: сравнить позицию Gazebo vs RViz vs ground truth                                | —                                                                                                                                                   | 1 день      | ⏳ **Заблокировано** — `make gazebo` не запускался после фиксов |
| 1.8              | Фикс QoS mismatch + fallback world_poses_info                                                | `src/gazebo_sim/scripts/ground_truth_publisher.py`, `src/gazebo_sim/config/gz_bridge.yaml`                                                          | 0.5 дня     | ✅ Выполнено                                                    |
| **Итого этап 1** |                                                                                              |                                                                                                                                                     | **~5 дней** |                                                                 |

**Критерий готовности:** В RViz видно два робота — текущий (уехавший) и ground truth (стоящий на месте). Расхождение визуально очевидно.

---

### Этап 2 — Заморозка odometry при stuck (stall detection)

**Цель:** Не интегрировать leg odometry, когда робот физически не двигается.

| №                | Задача                                                                                  | Файл(ы)                                                          | Оценка      | Статус                                  |
| ---------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ----------- | --------------------------------------- |
| 2.1              | Анализ IMU данных на stuck: проверить correlation между contact и отсутствием ускорения | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`      | 1 день      | ✅ Выполнено (используется angular_vel) |
| 2.2              | Реализовать stall detector в `odometry_update.cpp`                                      | `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp` | 1.5 дня     | ✅ Выполнено                            |
| 2.3              | Добавить параметры в odometry node                                                      | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`      | 0.5 дня     | ✅ Выполнено                            |
| 2.4              | Публикация `/stall_status`                                                              | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`      | 0.5 дня     | ✅ Выполнено                            |
| 2.5              | Reset stall state в `OdometryState::reset()`                                            | `src/quadropted_controller_cpp/src/odometry/odometry_state.cpp`  | 0.25 дня    | ✅ Выполнено                            |
| 2.6              | Сборка (`colcon build`)                                                                 | —                                                                | 0.25 дня    | ✅ Выполнено                            |
| 2.7              | Тестирование на террейне                                                                | —                                                                | 1 день      | ⏳ Ожидает                              |
| **Итого этап 2** |                                                                                         |                                                                  | **~5 дней** |                                         |

**Важное ограничение (документировано 26.05.2026):** Stall detection не срабатывает в REST mode (`delta_mag ≈ 0`, т.к. ноги не циклируют). Требуется доработка: детектить stall по IMU-standstill даже при `delta_mag ≈ 0`, если gait controller шлёт ненулевую команду движения.

**Критерий готовности:** При коллизии с препятствием одометрия останавливается (позиция x, y не меняется). После освобождения — возобновляется корректно.

---

### Этап 3 — Reset odometry по сервису

**Цель:** Дать возможность внешнему наблюдателю сбросить одометрию.

| №                | Задача                                                                                     | Файл(ы)                                                     | Оценка     | Зависимости |
| ---------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------- | ---------- | ----------- |
| 3.1              | Добавить сервис `ResetOdometry.srv` в `quadropted_msgs`                                    | `src/quadropted_msgs/srv/ResetOdometry.srv`                 | 0.5 дня    | —           |
| 3.2              | Реализовать service server в odometry node: вызов `reset()` + публикация нулевого Odometry | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp` | 1 день     | 3.1         |
| 3.3              | Тестирование: вызов сервиса → одометрия обнуляется                                         | —                                                           | 0.5 дня    | 3.2         |
| **Итого этап 3** |                                                                                            |                                                             | **~2 дня** |             |

**Критерий готовности:** `ros2 service call /robot1/reset_odometry std_srvs/Empty` → одометрия сбрасывается в ноль.

---

### Этап 4 — Автоматическая коррекция по ground truth

**Цель:** Автоматически корректировать odometry при расхождении с Gazebo ground truth.

| №                | Задача                                                                                      | Файл(ы)                                                          | Оценка       | Зависимости |
| ---------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------ | ----------- |
| 4.1              | Подписать odometry node на `/ground_truth/pose`                                             | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`      | 0.5 дня      | 1.3, 2.2    |
| 4.2              | Реализовать коррекцию: если odom_est - gt_pose > threshold → reset или smooth interpolation | `src/quadropted_controller_cpp/src/odometry/odometry_update.cpp` | 1.5 дня      | 4.1         |
| 4.3              | Параметр `ground_truth_topic` (опциональный, только для Gazebo)                             | `src/quadropted_controller_cpp/src/nodes/odometry_node.cpp`      | 0.5 дня      | 4.2         |
| 4.4              | Тестирование: ground truth bridge включен → drift автоматически устраняется                 | —                                                                | 1 день       | 4.2, 4.3    |
| **Итого этап 4** |                                                                                             |                                                                  | **~3.5 дня** |             |

**Критерий готовности:** Odometry автоматически синхронизируется с ground truth при расхождении > threshold. Дрифт не накапливается.

---

### Этап 5 — AMCL tuning

**Цель:** Улучшить коррекцию map→odom через AMCL particle filter.

| №                | Задача                                                                         | Файл(ы)                                                | Оценка     | Зависимости |
| ---------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------ | ---------- | ----------- |
| 5.1              | Анализ текущих параметров AMCL (particles, update threshold, laser model)      | `src/gazebo_sim/config/nav2_params.yaml` (секция amcl) | 0.5 дня    | —           |
| 5.2              | Оптимизация: увеличить число particles, уменьшить update_min_d, alpha пересчёт | `src/gazebo_sim/config/nav2_params.yaml`               | 0.5 дня    | 5.1         |
| 5.3              | Тестирование: робот на террейне, Nav2 планирует корректно                      | —                                                      | 1 день     | 5.2         |
| **Итого этап 5** |                                                                                |                                                        | **~2 дня** |             |

**Критерий готовности:** AMCL успевает корректировать map→odom быстрее, чем дрифт одометрии.

---

### Сводная таблица

| Этап      | Описание                                | Оценка                 | Статус                                         |
| --------- | --------------------------------------- | ---------------------- | ---------------------------------------------- |
| 1         | Ground Truth Bridge (диагностика)       | ~5 дней                | ✅ Завершён (включая QoS fix + fallback)       |
| 2         | Stall Detection (заморозка odometry)    | ~5 дней                | ✅ Реализован + скомпилирован, ⏳ тестирование |
| 3         | Reset Odometry Service                  | ~2 дня                 | ⏳ Ожидает                                     |
| 4         | Automatic Ground Truth Correction       | ~3.5 дня               | ⏳ Ожидает                                     |
| 5         | AMCL Tuning                             | ~2 дня                 | ⏳ Ожидает                                     |
| 6 🔴      | **Физическое скольжение тела в Gazebo** | **не оценено**         | 🆕 Новая проблема (26.05.2026)                 |
| **Итого** |                                         | **~17.5 рабочих дней** |                                                |

### Приоритетность

1. ✅ **Этап 1** (Ground Truth Bridge) — завершён
2. ✅ **Этап 2** (Stall Detection) — реализован, ожидает тестирования в симуляции
3. 🆕 **Этап 6 (новый)** — Разобраться с физическим скольжением тела в Gazebo:
   - Проверить параметры трения лап в SDF/model.sdf
   - Уменьшить mu скольжения, увеличить mu сцепления
   - Проверить начальную позу ног при spawn
   - Возможно, потребуется tuning контроллера для мягкого старта
4. **Этап 3** (Reset Service) — полезен для отладки
5. **Этап 4** (Auto Correction) — полное автоматическое решение
6. **Этап 5** (AMCL Tuning) — чинит только Nav2, не корень проблемы

**Ключевой вывод (26.05.2026):** Дрифт одометрии — лишь половина проблемы. Вторая половина — физическое скольжение тела робота в Gazebe. Stall detection не решит проблему, если тело реально движется сквозь террейн.

### Интеграция с elevation mapping

Проблема дрифта одометрии напрямую влияет на качество карты высот:

- Если `odom→base_link` дрифтует, то `elevation_mapping` получает неверную позицию LiDAR
- Точки облака проецируются в неверные ячейки grid map
- Результат: карта высот размазывается / дублируется

**Вывод:** Исправление odometry drift — prerequisite для корректной работы elevation mapping.
**Статус:** ⏳ Отложено до завершения этапов 1–2 + решения проблемы физического скольжения (этап 6).
