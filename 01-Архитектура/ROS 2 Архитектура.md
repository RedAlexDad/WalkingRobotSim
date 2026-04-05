# ROS 2 Архитектура

## Узлы (Nodes)

### RobotControllerNode
- **Файл:** `src/quadropted_controller/scripts/robot_controller_gazebo.py`
- **Описание:** Главный узел управления роботом. Создаёт экземпляр `Robot` (конечный автомат), вычисляет обратную кинематику и публикует углы сочленений.
- **Параметры:**
  - `verbose` (bool, default: False) -- подробный лог
  - `robot_id` (int, default: 1) -- идентификатор робота
- **Частота:** 60 Гц (timer)
- **Геометрия:** body=[0.3762, 0.0935], legs=[0.0, 0.0955, 0.213, 0.213]
- **Инициализация:** По умолчанию режим TROT (не REST)

### QuadrupedOdometryNode (DogOdometry)
- **Файл:** `src/quadropted_controller/scripts/QuadrupedOdometryNode.py`
- **Описание:** Оценка одометрии по контакту стоп + FK. Публикует `nav_msgs/Odometry`, TF transform и маркеры стоп для RViz.
- **Параметры:**
  - `verbose` (bool, default: False)
  - `publish_rate` (int, default: 50)
  - `has_imu_heading` (bool, default: True)
  - `enable_odom_tf` (bool, default: True)
  - `base_frame_id` (string, default: 'base')
  - `odom_frame_id` (string, default: 'odom')
  - `is_gazebo` (bool, default: True)
  - `clock_topic` (string, default: '/clock')
- **Фильтр:** Скользящее среднее (window=14) для сглаживания смещений
- **QoS:** Reliable для одометрии, Best Effort для foot_contact
- **Маркеры:** visualization_msgs/MarkerArray для визуализации позиций стоп в RViz

### RobotVelocityHandler
- **Файл:** `src/quadropted_controller/scripts/cmd_vel_pub.py`
- **Описание:** Мост между стандартным `geometry_msgs/Twist` и кастомным `RobotVelocity`. Применяет экспоненциальное масштабирование и лимиты скорости.
- **Лимиты:** linear.x до 0.035, linear.y до 0.012, angular.z до 1.0
- **robot_id:** 1 (хардкод)
- **Таймер движения:** отслеживает начало/конец ненулевой скорости, логирует elapsed time

## Топики (Topics)

### Входящие (подписки)

- `robot_mode` (RobotModeCommand) -- RobotControllerNode -- Reliable
- `robot_velocity` (RobotVelocity) -- RobotControllerNode, OdometryNode -- Reliable
- `joint_group_controller/commands` (Float64MultiArray) -- OdometryNode -- Reliable
- `foot_contact` (RobotFootContact) -- OdometryNode -- Best Effort
- `imu_plugin/out` (sensor_msgs/Imu) -- OdometryNode -- Reliable
- `clock` (rosgraph_msgs/Clock) -- OdometryNode -- Reliable
- `cmd_vel` (geometry_msgs/Twist) -- RobotVelocityHandler -- Reliable

### Исходящие (публикации)

- `joint_group_controller/commands` (Float64MultiArray) -- RobotControllerNode -- 12 углов сочленений
- `odom` (nav_msgs/Odometry) -- OdometryNode -- оценка положения
- `foot_contact` (RobotFootContact) -- TrotGaitController -- контакты стоп
- `controller_velocity` (geometry_msgs/Twist) -- TrotGaitController -- скорость для контроллера
- `foot_markers` (visualization_msgs/MarkerArray) -- OdometryNode -- визуализация стоп в RViz
- `/tf` (tf2_msgs/TFMessage) -- OdometryNode -- odom → base transform

## Сервисы (Services)

- `robot_behavior_command` (RobotBehaviorCommand) -- команды sit/up/walk

## Поток данных

```
Teleop/Nav2 --/cmd_vel--> RobotVelocityHandler --/robot_velocity--> RobotController
                                                                            |
/robot_mode --------------------------------------------------------------->|
                                                                            v
RobotController --> Joint Angles --> /joint_group_controller/commands
                                              |
                                    Joint angles --> FK --> OdometryNode --> /odom + TF + markers
                                              |
                                    Foot contacts <-- TrotGaitController
                                              |
                                    EKF (odom + IMU) --> Nav2
```

## Цикл управления

1. Timer 60 Гц вызывает `control_loop()`
2. `robot.run()` -- текущий контроллер вычисляет позиции стоп
3. `robot.change_controller()` -- обработка событий переключения
4. IK преобразует позиции стоп в 12 углов сочленений
5. Углы публикуются в `joint_group_controller/commands`
