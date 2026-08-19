# Архитектура проекта

Обзор компонентов, пакетов и связей между ними.

---

## Общая схема

```
┌───────────────────────────────────────────────────┐
│                    Gazebo Sim                     │
│  (физика, сенсоры, визуализация, worlds)          │
└──────┬─────────────────────────────┬──────────────┘
       │ /joint_states               │ /clock, /scan, /imu
       ▼                             ▼
┌──────────────┐           ┌──────────────────┐
│  JointState  │           │  robot_state_    │
│  Publisher   │           │  publisher (TF)  │
└──────┬───────┘           └────────┬─────────┘
       │ joint_states               │ /tf, /tf_static
       ▼                            ▼
┌────────────────────────────────────────────────────┐
│           quadropted_controller_cpp               │
│  (или quadropted_controller_cpp)                   │
│                                                    │
│  GaitManager → GaitController (Trot/Crawl/Rest)    │
│  ForwardKinematics → OdometryPublisher             │
│  RobotController (cmd_vel → IK → joint commands)   │
└──────┬─────────────────────────────────┬───────────┘
       │ /joint_commands                 │ /odom
       ▼                                 ▼
┌──────────────┐               ┌───────────────────┐
│ ros2_control │               │ robot_localization│
│ Position     │               │ EKF (odom + imu)  │
│ Controller   │               └───────────────────┘
└──────────────┘
```

---

## Пакеты

### quadropted_controller_cpp

C++ контроллер ходьбы, 53.5x быстрее Python. Полная кросс-валидация.

- `TrotGaitController`, `CrawlGaitController`, `RestController`, `StandController`
- Eigen3 для кинематики
- Одометрия с O(1) скользящим средним
- PID контроллер

### quadropted_perception (YOLO Object Detection)

Распознавание объектов через YOLO (Ultralytics).

- `yolo_detector.py` — ROS 2 node, подписка на камеру, инференс YOLO, публикация детекций
- `visualizer.py` — визуализация bounding boxes в RViz через MarkerArray
- `config/yolo_detector.yaml` — параметры (модель, пороги, топики)
- `rviz/yolo_detection.rviz` — RViz конфиг split-screen (raw камера + детекции)

### quadropted_msgs

Кастомные ROS 2 сообщения:

- `RobotModeCommand.msg` — режим робота
- `RobotBehaviorCommand.srv` — поведение (walk/up/sit)
- `Waypoint.msg` — точка маршрута
- `RobotVelocity.msg` — скорости ног

### gazebo_sim

- Launch файлы (одиночный и мультироботный режимы)
- Миры SDF
- Конфигурация waypoints
- RViz конфиги

### rviz_waypoint_tool

Плагин RViz для расстановки waypoint-точек мышкой на карте.

### go1_description / go2_description

URDF модели: линки, джойнты, инерциальные параметры, трансмиссии.

---

## Топики

| Топик                            | Тип                          | Откуда → Куда                 |
| -------------------------------- | ---------------------------- | ----------------------------- |
| `/robot1/joint_states`           | `sensor_msgs/JointState`     | Gazebo → все                  |
| `/robot1/odom`                   | `nav_msgs/Odometry`          | OdometryPublisher → EKF, Nav2 |
| `/robot1/odometry/filtered`      | `nav_msgs/Odometry`          | EKF → Nav2                    |
| `/robot1/imu`                    | `sensor_msgs/Imu`            | Gazebo → EKF                  |
| `/robot1/cmd_vel`                | `geometry_msgs/Twist`        | teleop/Nav2 → Controller      |
| `/robot1/joint_commands`         | `std_msgs/Float64MultiArray` | Controller → ros2_control     |
| `/robot1/robot_mode`             | `RobotModeCommand`           | Пользователь → GaitManager    |
| `/robot1/robot_behavior_command` | `RobotBehaviorCommand`       | Пользователь → GaitManager    |
| `/robot1/color/image_raw`        | `sensor_msgs/Image`          | Gazebo → YOLO детектор        |
| `/detections`                    | `DetectionArray`             | YOLO → visualizer             |
| `/detected_image`                | `sensor_msgs/Image`          | YOLO → RViz (с bbox)          |
| `/detection_markers`             | `visualization_msgs/MarkerArray` | visualizer → RViz          |

---

## Namespaces

По умолчанию `robot1`. При мультироботном запуске:

- `robot1/*` — первый робот
- `robot2/*` — второй робот
- и т.д.

---

## Связанные документы

- [Docker окружение](../src/docker/README.md)
- [Запуск симуляции](../src/gazebo_sim/README.md)
- [Навигация по waypoints](navigation.md)
- [YOLO object detection](yolo.md)
- [CI/CD](ci-cd.md)


---

# Контроллеры и одометрия: Rust (основной) и C++ (опция)

> Раздел ниже добавлен в рамках миграции контроллера на Rust
> (`feat/rust-migration`).

## Обзор

Робот (Unitree Go2) управляется контроллером ходьбы с 12 степенями свободы.
Проект содержит **две реализации контроллера**, которые используют одни и те же
топики и сообщения и потому взаимозаменяемы:

| Реализация | Пакет | Статус |
|---|---|---|
| **Rust** (основная) | `quadropted_controller_rust` | По умолчанию (`make gazebo`) |
| C++ (для сравнения) | `quadropted_controller_cpp` | `make gazebo-cpp` |

## Rust пакеты

```
src/quadropted_controller_rust/
├── Cargo.toml                     # workspace: quadropted-core, quadropted-nodes
├── quadropted-core/               # БЕЗ ROS-зависимостей
│   └── src/
│       ├── math/                  # rotx/roty/rotz/rotxyz, homogeneous transforms
│       ├── kinematics/            # forward.rs, inverse.rs (IK/FK)
│       ├── controllers/
│       │   ├── gait.rs            # базовый GaitController (фазы, контакты)
│       │   ├── crawl/             # gait.rs, stance.rs, swing.rs (CRAWL)
│       │   ├── trot/              # gait.rs, stance.rs, swing.rs (TROT)
│       │   ├── rest.rs            # REST
│       │   ├── stand.rs           # STAND
│       │   └── pid.rs
│       ├── odometry/
│       │   ├── state.rs           # OdometryState (скользящее окно, фильтр)
│       │   └── update.rs          # update_odometry, normalize_angle
│       └── state/                 # BehaviorState, Command
├── quadropted-nodes/              # ROS 2 узлы (rclrs)
│   └── src/bin/
│       ├── robot_controller_node.rs   # контроллер: REST/TROT/CRAWL/STAND + IK
│       └── odometry_node.rs           # Odometry Node (50 Гц)
```

Биндинги сообщений (ручные FFI-обёртки):
`geometry_msgs_rs`, `sensor_msgs_rs`, `std_msgs_rs`, `quadropted_msgs_rs`,
`nav_msgs_rs` (Odometry), `tf2_msgs_rs` (TFMessage).

## CRAWL: выравнивание с активным C++ рантайм-путём

Rust `CrawlGaitController::step` повторяет **активный C++ рантайм-путь**
(`quadropted_controller_cpp/src/nodes/robot_controller_node.cpp::step_crawl`),
а не библиотечный `CrawlGaitController::step` (C++ нода его не вызывает):

1. **Нулевая команда** → плавное возвращение к default stance (alpha = 0.1).
2. **Stance-фаза** → `CrawlStanceController::next_foot_location` с
   `move_sideways`/`move_left` из фазы (фазы 0 и 4).
3. **Swing-фаза** → `CrawlSwingController::next_foot_location` с жёстко
   зашитым `shifted_left = false` (как в C++ `crawl_swing.cpp`).
4. **`first_cycle_` никогда не сбрасывается** — C++ нода не вызывает
   `step()`, поэтому `is_first_cycle()` всегда `true` → `shift_factor = 1`.

Результат: траектории ног Rust и C++ **бит-в-бит идентичны**
(проверяется тестом `test_crawl_rust_matches_cpp_runtime_bit_exact`),
робот в CRAWL ходит без насыщения IK.

## Odometry Node

Rust `odometry_node.rs` — замена C++ `odometry_node.cpp`:

- **Подписки**: `joint_group_controller/commands` (Float64MultiArray, 12 углов),
  `foot_contact` (RobotFootContact), `imu` (sensor_msgs/Imu → yaw + ω_z),
  `robot_velocity` (RobotVelocity → fallback скорость).
- **Публикации**: `/robot1/odom` (nav_msgs/Odometry) на 50 Гц;
  TF (odom → base_link) через `tf2_msgs/TFMessage` при включённом флаге.
- **Алгоритм**: FK ног из углов суставов → смещение тела из движения
  контактирующих стоп → скользящее окно (по умолчанию 14 отсчётов) →
  интеграция с учётом yaw из IMU. Порт C++ `odometry_state.cpp` /
  `odometry_update.cpp` (расхождение < 1e-9 на тестовом маршруте 10 с).
- **Обработка ошибок**: при неверном числе углов/контактов — предупреждение,
  узел не падает; при отсутствии контактов — fallback на командную скорость.

## Топики (namespace `robot1`)

| Топик | Тип | Направление |
|---|---|---|
| `/robot1/robot_mode` | `quadropted_msgs/RobotModeCommand` | вход контроллера |
| `/robot1/robot_velocity` | `quadropted_msgs/RobotVelocity` | вход контроллера/одометрии |
| `/robot1/imu` (imu_plugin/out) | `sensor_msgs/Imu` | вход контроллера/одометрии |
| `/robot1/joint_group_controller/commands` | `std_msgs/Float64MultiArray` | выход контроллера / вход одометрии |
| `/robot1/foot_contact` | `quadropted_msgs/RobotFootContact` | выход контроллера / вход одометрии |
| `/robot1/odom` | `nav_msgs/Odometry` | выход одометрии (50 Гц) |
| `/robot1/tf` | `tf2_msgs/TFMessage` | TF odom → base_link |

## Запуск

```bash
make gazebo        # Rust контроллер + Rust Odometry (по умолчанию)
make gazebo-cpp    # C++ контроллер + C++ Odometry (для сравнения)
make crawl         # переключение в режим CRAWL
make test-rust     # все тесты Rust (юнит + кросс-валидация + интеграционные)
```

## Тестирование

- `cargo test --workspace` — юнит-тесты всех пакетов.
- `scripts/test_cross_validation.sh` — C++ unit + Rust unit + кросс-валидация
  формул (< 1e-10) + интеграционные тесты.
- Интеграционные (headless):
  - `test_crawl_no_saturation` — 30 с CRAWL (1800 тактов @ 60 Гц), углы не
    выходят за URDF-пределы более чем на 1% времени; Rust бит-в-бит = C++.
  - `test_odometry_cross_validation` — маршрут 10 с, расхождение < 1e-9.
