# Шпаргалка по топикам ROS2

Методичка 02: Топики и сообщения

---

## Основные команды

### Список топиков
```bash
ros2 topic list              # Все топики
ros2 topic list -a           # Все топики с деталями
ros2 topic list | wc -l      # Количество топиков
ros2 topic list | grep pattern  # Фильтрация по паттерну
```

### Информация о топике
```bash
ros2 topic type /topic_name       # Тип сообщения
ros2 topic info /topic_name       # Издатели и подписчики
ros2 topic info /topic_name --verbose  # Подробная информация
```

### Просмотр сообщений
```bash
ros2 topic echo /topic_name       # Бесконечный просмотр
ros2 topic echo /topic_name --once  # Одно сообщение
ros2 topic echo /topic_name -n 5  # N сообщений
```

### Частота и задержка
```bash
ros2 topic hz /topic_name     # Частота публикации (Гц)
ros2 topic delay /topic_name  # Задержка доставки
ros2 topic bw /topic_name     # Пропускная способность
```

### Публикация
```bash
# Разовая
ros2 topic pub /topic_name msg_type "{data}"

# Постоянная (10 Гц)
ros2 topic pub /topic_name msg_type "{data}" -r 10
```

---

## Типы сообщений

### Просмотр структуры
```bash
ros2 interface show geometry_msgs/msg/Twist
ros2 interface show sensor_msgs/msg/JointState
ros2 interface show nav_msgs/msg/Odometry
ros2 interface show sensor_msgs/msg/Imu
```

### Список всех типов
```bash
ros2 interface list
ros2 interface list | grep Twist
```

---

## Топики проекта WalkingRobotSim

### Основные
- /robot1/cmd_vel -- команды скорости (geometry_msgs/msg/Twist)
- /robot1/robot_mode -- режим робота (quadropted_msgs/msg/RobotModeCommand)
- /robot1/robot_velocity -- скорость робота (quadropted_msgs/msg/RobotVelocity)
- /robot1/joint_states -- состояния сочленений (sensor_msgs/msg/JointState)
- /robot1/odom -- одометрия (nav_msgs/msg/Odometry)
- /robot1/imu/data -- данные IMU (sensor_msgs/msg/Imu)
- /robot1/foot_contact -- контакты стоп (quadropted_msgs/msg/RobotFootContact)
- /clock -- время симуляции (rosgraph_msgs/msg/Clock)

---

## Полезные команды

### Проверка работы топика
```bash
# Есть ли издатели
ros2 topic info /robot1/cmd_vel | grep Publishers

# Есть ли подписчики
ros2 topic info /robot1/cmd_vel | grep Subscribers
```

### Мониторинг частоты
```bash
ros2 topic hz /robot1/joint_states
ros2 topic hz /robot1/odom
```

---

## Связанные документы

- [Основная методичка](README.md)
- [Тест](quiz.md)

---

*Последнее обновление: Март 2026*
