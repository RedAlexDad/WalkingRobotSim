# Методичка 05: Практические упражнения

Уровень сложности: средний
Время на выполнение: 3-4 часа
Предварительные требования: Методички 01-basics, 02-topics, 03-docker, 04-project-arch

---

## Цели этой методички

После выполнения вы сможете:

- Запускать симуляцию робота
- Управлять роботом в симуляции
- Создавать собственные узлы ROS2
- Отлаживать и мониторить систему

---

## Оглавление

1. Упражнение 1: Первый запуск
2. Упражнение 2: Переключение режимов
3. Упражнение 3: Телеоперация
4. Упражнение 4: Работа с топиками
5. Упражнение 5: Создание узла
6. Упражнение 6: Мониторинг системы

---

## Упражнение 1: Первый запуск

Цель: запустить симуляцию и убедиться, что всё работает.

### Шаг 1: Запуск контейнера

```bash
cd src/docker
docker compose up -d
```

Дождитесь запуска. Проверьте:

```bash
docker compose ps
```

Вы должны увидеть контейнер walking_robot_sim в состоянии running.

### Шаг 2: Вход в контейнер

```bash
docker compose exec simulator bash
```

### Шаг 3: Источник ROS2

```bash
source /opt/ros/jazzy/setup.bash
source /root/ws/install/setup.bash
```

### Шаг 4: Проверка узлов

```bash
ros2 node list
```

Вы должны увидеть несколько узлов, включая robot_controller и odometry.

### Критерии завершения

- Контейнер запущен (docker compose ps показывает running)
- ros2 node list показывает узлы
- Нет ошибок в логах (docker compose logs)

---

## Упражнение 2: Переключение режимов

Цель: переключать робота между режимами REST, STAND, TROT.

### Шаг 1: Режим STAND

```bash
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'STAND', robot_id: 1}"
```

Наблюдайте, как робот встаёт в Gazebo.

### Шаг 2: Режим TROT

```bash
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'TROT', robot_id: 1}"
```

Робот должен начать ходить рысью.

### Шаг 3: Режим REST

```bash
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'REST', robot_id: 1}"
```

Робот должен остановиться и вернуться в положение покоя.

### Шаг 4: Сервис поведения

```bash
# Команда "seсть"
ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand "{command: 'sit'}"

# Команда "встать"
ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand "{command: 'up'}"

# Команда "идти"
ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand "{command: 'walk'}"
```

### Критерии завершения

- Робот переключается между всеми 4 режимами
- Сервис поведения работает (sit, up, walk)
- Визуально видно изменения в Gazebo

---

## Упражнение 3: Телеоперация

Цель: управлять роботом с клавиатуры.

### Шаг 1: Запуск телеоперации

В новом терминале (в контейнере):

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

### Шаг 2: Управление

Используйте клавиши:
- I -- вперёд
- , -- назад
- J -- влево
- L -- вправо
- U -- поворот влево
- O -- поворот вправо

### Шаг 3: Наблюдение за одометрией

В другом терминале:

```bash
ros2 topic echo /robot1/odom --once
```

Отправляйте команды движения и наблюдайте, как меняется позиция в /robot1/odom.

### Критерии завершения

- Телеоперация подключена к /robot1/cmd_vel
- Робот двигается при нажатии клавиш
- /robot1/odom обновляется при движении

---

## Упражнение 4: Работа с топиками

Цель: научиться исследовать систему через топики.

### Шаг 1: Список топиков

```bash
ros2 topic list
ros2 topic list | wc -l
```

### Шаг 2: Фильтрация

```bash
# Найти топики с "joint"
ros2 topic list | grep joint

# Найти топики с "odom"
ros2 topic list | grep odom

# Найти топики конкретного робота
ros2 topic list | grep robot1
```

### Шаг 3: Частота топиков

```bash
ros2 topic hz /robot1/joint_states
ros2 topic hz /robot1/odom
```

joint_states должен быть около 60 Гц.

### Шаг 4: Просмотр сообщений

```bash
# Однометрия
ros2 topic echo /robot1/odom --once

# Состояние сочленений
ros2 topic echo /robot1/joint_states --once

# Данные IMU
ros2 topic echo /robot1/imu/data --once
```

### Шаг 5: Информация о топике

```bash
ros2 topic info /robot1/cmd_vel
ros2 topic info /robot1/cmd_vel --verbose
```

### Критерии завершения

- Вы можете найти и отфильтровать нужные топики
- Вы знаете частоту основных топиков
- Вы можете просмотреть структуру сообщений

---

## Упражнение 5: Создание узла

Цель: создать простой ROS2 узел, который публикует данные.

### Шаг 1: Создание пакета

В контейнере:

```bash
cd /root/ws/src
ros2 pkg create --build-type ament_python my_first_node --dependencies rclpy std_msgs
```

### Шаг 2: Создание узла-издателя

Создайте файл /root/ws/src/my_first_node/my_first_node/publisher.py:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SimplePublisher(Node):
    def __init__(self):
        super().__init__('simple_publisher')
        self.publisher_ = self.create_publisher(String, 'my_topic', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.count = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello from WalkingRobotSim! Count: {self.count}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
        self.count += 1

def main(args=None):
    rclpy.init(args=args)
    node = SimplePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Шаг 3: Регистрация точки входа

Откройте setup.py в пакете my_first_node и добавьте в entry_points:

```python
entry_points={
    'console_scripts': [
        'publisher = my_first_node.publisher:main',
    ],
},
```

### Шаг 4: Сборка

```bash
cd /root/ws
colcon build --packages-select my_first_node
source install/setup.bash
```

### Шаг 5: Запуск

```bash
ros2 run my_first_node publisher
```

### Шаг 6: Проверка

В другом терминале:

```bash
ros2 topic echo /my_topic
ros2 topic hz /my_topic
```

### Критерии завершения

- Пакет создан и собран без ошибок
- Узел запускается и публикует сообщения
- ros2 topic echo показывает сообщения
- ros2 topic hz показывает частоту около 1 Гц

---

## Упражнение 6: Мониторинг системы

Цель: научиться отслеживать состояние системы.

### Шаг 1: Граф ROS2

```bash
rqt_graph
```

Визуализация покажет все узлы и их связи через топики.

### Шаг 2: Ресурсы контейнера

В терминале хоста:

```bash
docker stats walking_robot_sim
```

Показывает использование CPU и памяти.

### Шаг 3: Логи узлов

```bash
# Логи конкретного узла
ros2 run quadropted_controller robot_controller_gazebo --ros-args --log-level info

# Логи контейнера
docker compose logs -f simulator
```

### Шаг 4: Частота всех топиков

```bash
# Проверьте основные топики
ros2 topic hz /robot1/joint_states
ros2 topic hz /robot1/odom
ros2 topic hz /robot1/imu/data
```

### Критерии завершения

- Вы можете открыть rqt_graph и увидеть граф
- Вы можете отслеживать ресурсы через docker stats
- Вы знаете, где смотреть логи
- Вы проверили частоту основных топиков

---

## Поздравляем

Вы завершили все упражнения! Теперь вы умеете:

- Разворачивать ROS2 проекты в Docker
- Запускать и управлять симуляцией робота
- Переключать режимы работы робота
- Управлять роботом с клавиатуры
- Работать с топиками ROS2
- Создавать собственные узлы ROS2
- Мониторить и отлаживать систему

---

## Дальнейшие шаги

- Измените параметры контроллера и наблюдайте эффект
- Добавьте новый режим работы робота
- Создайте узел-подписчик на ваш /my_topic
- Поэкспериментируйте с Nav2 навигацией

---

## Нужна помощь

- GitHub Issues: https://github.com/RedAlexDad/WalkingRobotSim/issues
- Документация ROS2: https://docs.ros.org/
- Документация Docker: https://docs.docker.com/

---

## Навигация

- [На главную](../README.md) -- Карта всех методичек
- [Методичка 04-project-arch](../04-project-arch/README.md) -- Архитектура проекта

---

*Последнее обновление: Март 2026*
