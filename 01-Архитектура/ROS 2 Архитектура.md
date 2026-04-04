# ROS 2 Архитектура

## Узлы (Nodes)

### RobotControllerNode
- **Файл:** `src/quadropted_controller/scripts/robot_controller_gazebo.py`
- **Описание:** Главный узел управления роботом. Создаёт экземпляр `Robot` (конечный автомат), вычисляет обратную кинематику и публикует углы сочленений.
- **Параметры:**
  - `verbose` (bool) — подробный лог
  - `robot_id` (int) — идентификатор робота
- **Частота:** 60 Гц (timer)
- **Геометрия:** body=[0.3762, 0.0935], legs=[0.0, 0.0955, 0.213, 0.213]

### QuadrupedOdometryNode (DogOdometry)
- **Файл:** `src/quadropted_controller/scripts/QuadrupedOdometryNode.py`
- **Описание:** Оценка одометрии по контакту стоп + FK. Публикует `nav_msgs/Odometry` и TF transform.
- **Параметры:** `verbose`, `publish_rate`, `has_imu_heading`, `enable_odom_tf`, `base_frame_id`, `odom_frame_id`, `is_gazebo`, `clock_topic`
- **Фильтр:** Скользящее среднее (window=14) для сглаживания смещений

### cmd_vel_handler
- **Файл:** `src/quadropted_controller/scripts/cmd_vel_pub.py`
- **Описание:** Мост между стандартным `geometry_msgs/Twist` и кастомным `RobotVelocity`. Применяет экспоненциальное масштабирование и лимиты скорости.

## Топики (Topics)

### Входящие (подписки)

| Топик | Тип | Узел | Описание |
|---|---|---|---|
| `/robot_mode` | `RobotModeCommand` | RobotControllerNode | Переключение режимов |
| `/robot_velocity` | `RobotVelocity` | RobotControllerNode, OdometryNode | Команда скорости |
| `/joint_group_controller/commands` | `Float64MultiArray` | OdometryNode | Углы сочленений (для FK) |
| `/foot_contact` | `RobotFootContact` | OdometryNode | Состояния контакта стоп |
| `/imu_plugin/out` | `sensor_msgs/Imu` | OdometryNode | Данные IMU |
| `/clock` | `rosgraph_msgs/Clock` | OdometryNode | Время Gazebo |

### Исходящие (публикации)

| Топик | Тип | Узел | Описание |
|---|---|---|---|
| `joint_group_controller/commands` | `Float64MultiArray` | RobotControllerNode | 12 углов сочленений |
| `odom` | `nav_msgs/Odometry` | OdometryNode | Оценка положения |
| `foot_contact` | `RobotFootContact` | TrotGaitController | Контакты стоп |
| `controller_velocity` | `geometry_msgs/Twist` | TrotGaitController | Скорость для контроллера |
| `foot_markers` | `visualization_msgs/MarkerArray` | OdometryNode | Визуализация стоп в RViz |
| `/tf` | `tf2_msgs/TFMessage` | OdometryNode | odom → base transform |

## Сервисы (Services)

| Сервис | Тип | Описание |
|---|---|---|
| `/robot_behavior_command` | `RobotBehaviorCommand` | Команды sit/up/walk |

## Launch-файлы

### launch_python.launch.py
Топ-левел launch. Запускает Gazebo мир, через 6 секунд запускает мультироботную систему.

### gazebo_multi_nav2_world.launch.py
Оркестрация мультиробота:
1. Читает роботов из `robots.yaml`
2. Для каждого робота:
   - `robot_state_publisher` (URDF)
   - GZ bridge (ROS ↔ Gazebo)
   - Joint state publisher
   - ros2_control controller manager
   - RobotControllerNode
   - QuadrupedOdometryNode
   - Nav2 stack
   - EKF (robot_localization)

## Поток данных

```
Teleop/Nav2 → /cmd_vel → cmd_vel_handler → /robot_velocity
                                                    ↓
/robot_mode → RobotControllerNode → Joint Angles → /joint_group_controller/commands
                                                              ↓
                                          Joint angles → FK → OdometryNode → /odom
                                                              ↓
                                          Foot contacts ← TrotGaitController
```
