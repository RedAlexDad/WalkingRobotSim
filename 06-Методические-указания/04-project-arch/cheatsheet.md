# Шпаргалка по архитектуре проекта

Методичка 04: Справочник по WalkingRobotSim

---

## Пакеты проекта

### docker
- Dockerfile -- 10-этапная сборка
- compose.yml -- контейнер с GUI, host network, privileged
- manage.sh -- скрипт управления

### gazebo_sim
- launch/ -- launch-файлы (gazebo_multi_nav2_world.launch.py)
- config/ -- nav2_params.yaml, ekf.yaml, robots.yaml
- world/ -- cafe.world
- maps/ -- карты навигации

### quadropted_controller
- robot_controller_gazebo.py -- главный узел (60 Гц, инициализация в TROT)
- QuadrupedOdometryNode.py -- одометрия по контакту стоп (50 Гц, маркеры RViz)
- cmd_vel_pub.py -- Twist -> RobotVelocity адаптер
- RobotController/ -- контроллеры походки
- InverseKinematics/ -- обратная кинематика
- ForwardKinematics/ -- прямая кинематика

### quadropted_msgs
- msg/ -- 4 кастомных сообщения
- srv/ -- 1 сервис

### go1_description / go2_description
- URDF/Xacro модели роботов

---

## Режимы работы робота

### REST
- Покой, робот неподвижен
- PID компенсация крена/тангажа (kp=0.75, ki=2.29, kd=0.0)

### TROT
- Рысь, диагональные пары ног
- 4 фазы цикла
- X: до 0.035 м/с, Y: до 0.012 м/с, Yaw: до 0.5 рад/с
- AutoRest: автоматический отдых при нулевой скорости
- IMU PID: kp=0.15, ki=0.02, kd=0.002

### CRAWL
- Ползание, последовательные ноги
- 8 фаз цикла
- Боковое смещение тела: 0.06 м
- X: до 0.011 м/с, Yaw: до 0.15 рад/с

### STAND
- Стойка, вращение на месте
- Линейная: до 0.035 м/с, Угловая: до 0.1 рад/с

---

## Основные топики

- /robot1/cmd_vel -- команды скорости (geometry_msgs/msg/Twist)
- /robot1/robot_mode -- режим робота (quadropted_msgs/msg/RobotModeCommand)
- /robot1/robot_velocity -- скорость (quadropted_msgs/msg/RobotVelocity)
- /robot1/joint_states -- состояния сочленений (sensor_msgs/msg/JointState)
- /robot1/odom -- одометрия (nav_msgs/msg/Odometry)
- /robot1/imu/data -- данные IMU (sensor_msgs/msg/Imu)
- /robot1/foot_contact -- контакты стоп (quadropted_msgs/msg/RobotFootContact)
- /robot1/foot_markers -- маркеры стоп (visualization_msgs/msg/MarkerArray)

---

## Управление движением

### Переключение режима
```bash
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'TROT', robot_id: 1}"
```

### Сервис поведения
```bash
ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand "{command: 'walk'}"
```

---

## Граф ROS2

```
Teleop/Nav2 -> /cmd_vel -> RobotVelocityHandler -> /robot_velocity -> RobotController
/robot_mode --------------------------------------------------------> RobotController
RobotController -> Joint Angles -> /joint_group_controller/commands -> Gazebo
Joint angles -> FK -> OdometryNode -> /odom + TF + markers -> EKF -> Nav2
Foot contacts <- TrotGaitController
```

---

## Связанные документы

- [Основная методичка](README.md)
- [Тест](quiz.md)

---

*Последнее обновление: Март 2026*
