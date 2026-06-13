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
