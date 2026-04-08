# Шпаргалка по командам ROS2

Методичка 01: Базовые команды

---

## Системные команды

### Проверка версии
```bash
# Версия ROS2
ros2 --version

# Версия дистрибутива
echo $ROS_DISTRO
```

### Проверка окружения
```bash
# Проверка переменных окружения
env | grep ROS

# Проверка ROS_DOMAIN_ID
echo $ROS_DOMAIN_ID
```

---

## Управление узлами (Nodes)

### Список узлов
```bash
# Показать все активные узлы
ros2 node list

# Подробная информация об узле
ros2 node info /node_name
```

### Запуск узла
```bash
# Запустить узел из пакета
ros2 run package_name node_name

# Пример
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## Работа с топиками (Topics)

### Список топиков
```bash
# Показать все топики
ros2 topic list

# Показать только активные топики
ros2 topic list -a
```

### Информация о топике
```bash
# Тип сообщения
ros2 topic type /topic_name

# Подробная информация
ros2 topic info /topic_name

# Информация с деталями (издатели, подписчики)
ros2 topic info /topic_name --verbose
```

### Просмотр сообщений
```bash
# Подписаться на топик (бесконечно)
ros2 topic echo /topic_name

# Показать N сообщений
ros2 topic echo /topic_name -n 5

# Показать только одно сообщение
ros2 topic echo /topic_name --once
```

### Частота и задержка
```bash
# Частота публикации (Гц)
ros2 topic hz /topic_name

# Задержка доставки
ros2 topic delay /topic_name

# Пропускная способность
ros2 topic bw /topic_name
```

### Публикация сообщений
```bash
# Разовая публикация
ros2 topic pub /topic_name msg_type "{data}"

# Пример: команда скорости
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

# Постоянная публикация (10 раз в секунду)
ros2 topic pub /topic_name msg_type "{data}" -r 10
```

---

## Работа с сервисами (Services)

### Список сервисов
```bash
# Показать все сервисы
ros2 service list
```

### Информация о сервисе
```bash
# Тип сервиса
ros2 service type /service_name

# Подробная информация
ros2 service info /service_name
```

### Вызов сервиса
```bash
# Вызов сервиса с данными
ros2 service call /service_name srv_type "{request_data}"

# Пример
ros2 service call /robot/set_mode example_interfaces/srv/SetBool "{data: true}"
```

---

## Работа с пакетами (Packages)

### Поиск пакетов
```bash
# Список всех пакетов
ros2 pkg list

# Найти пакет по имени
ros2 pkg list | grep pattern

# Информация о пакете
ros2 pkg prefix package_name
```

### Создание пакета
```bash
# Создать Python пакет
ros2 pkg create --build-type ament_python package_name

# Создать C++ пакет
ros2 pkg create --build-type ament_cmake package_name

# Создать с зависимостями
ros2 pkg create --build-type ament_python package_name --dependencies rclpy std_msgs
```

### Исполняемые файлы пакета
```bash
# Список исполняемых файлов
ros2 pkg executables package_name

# Все исполняемые файлы всех пакетов
ros2 pkg executables
```

---

## Параметры (Parameters)

### Список параметров
```bash
# Список параметров узла
ros2 param list

# Получить значение параметра
ros2 param get /node_name param_name

# Установить значение параметра
ros2 param set /node_name param_name value
```

### Примеры
```bash
# Получить параметр
ros2 param get /robot_controller use_imu

# Установить параметр
ros2 param set /robot_controller use_imu true
```

---

## Launch (Запуск)

### Запуск launch файла
```bash
# Запустить launch файл
ros2 launch package_name launch_file.py

# Пример
ros2 launch gazebo_sim launch_sim.launch.py

# Запуск с аргументами
ros2 launch package_name launch_file.py arg_name:=value
```

---

## Интерфейсы сообщений

### Просмотр структуры
```bash
# Показать структуру сообщения
ros2 interface show msg_type

# Примеры
ros2 interface show geometry_msgs/msg/Twist
ros2 interface show sensor_msgs/msg/JointState
ros2 interface show nav_msgs/msg/Odometry
```

### Список типов
```bash
# Список всех типов сообщений
ros2 interface list
```

---

## Отладка и мониторинг

### Граф ROS2
```bash
# Запустить визуализацию графа
rqt_graph
```

### Логирование
```bash
# Просмотр логов узла
ros2 run package_name node_name --ros-args --log-level info

# Уровни логирования: debug, info, warn, error, fatal
```

### Проверка качества связи
```bash
# Проверка топика на наличие издателей
ros2 topic info /topic_name | grep Publishers

# Проверка топика на наличие подписчиков
ros2 topic info /topic_name | grep Subscribers
```

---

## Быстрые команды для проекта

### Запуск симуляции
```bash
# Перейти в директорию docker
cd src/docker

# Запустить контейнер
docker compose up -d

# Войти в контейнер
docker compose exec simulator bash

# Источник ROS2
source /opt/ros/jazzy/setup.bash
source /root/ws/install/setup.bash
```

### Управление роботом
```bash
# Переключение в режим STAND
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'STAND', robot_id: 1}"

# Переключение в режим REST
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'REST', robot_id: 1}"

# Переключение в режим TROT
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'TROT', robot_id: 1}"
```

### Мониторинг
```bash
# Частота топиков
ros2 topic hz /robot1/joint_states
ros2 topic hz /robot1/odom

# Просмотр топиков
ros2 topic echo /robot1/cmd_vel
ros2 topic echo /robot1/imu/data
```

---

## Полезные советы

### Автодополнение
```bash
# Включить автодополнение для bash
source /opt/ros/jazzy/share/ros2/setup.bash
```

### Алиасы (добавить в ~/.bashrc)
```bash
# Алиасы для частых команд
alias r2l='ros2 node list'
alias r2t='ros2 topic list'
alias r2h='ros2 topic hz'
alias r2e='ros2 topic echo'
alias r2p='ros2 topic pub'
```

### Очистка терминала
```bash
# Очистить экран и запустить команду
clear && ros2 topic list
```

---

## Связанные документы

- [Основная методичка](README.md)
- [Словарь терминов](glossary.md)
- [Тест для самопроверки](quiz.md)

---

*Последнее обновление: Март 2026*
