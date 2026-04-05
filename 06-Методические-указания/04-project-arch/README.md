# Методичка 04: Архитектура проекта WalkingRobotSim

Уровень сложности: средний
Время на изучение: 2-3 часа
Предварительные требования: Методички 01-basics, 02-topics, 03-docker

---

## Цели этой методички

После изучения вы сможете:

- Понимать структуру проекта WalkingRobotSim
- Знать назначение каждого пакета
- Понимать, как компоненты взаимодействуют друг с другом
- Управлять режимами работы робота

---

## Оглавление

1. Структура проекта
2. Описание пакетов
3. Как робот управляется
4. Режимы работы робота
5. Поток данных
6. Именование
7. FAQ

---

## 1. Структура проекта

```
WalkingRobotSim/
  src/
    docker/                   # Docker инфраструктура
      Dockerfile              # 10-этапная сборка
      compose.yml             # Docker Compose
    gazebo_sim/               # Пакет симуляции
      launch/                 # Launch-файлы
      config/                 # Конфигурации (Nav2, EKF, robots)
      world/                  # Gazebo миры
      maps/                   # Карты навигации
      rviz/                   # RViz конфигурации
      models/                 # Gazebo модели
    quadropted_controller/    # Пакет управления (Python)
      scripts/
        robot_controller_gazebo.py     # Главный узел
        QuadrupedOdometryNode.py       # Узел одометрии
        cmd_vel_pub.py                 # Twist -> RobotVelocity
        RobotController/               # Контроллеры
          RobotController.py           # Главный контроллер
          GaitController.py            # Базовый класс походки
          TrotGaitController.py        # Рысь
          CrawlGaitController.py       # Ползание
          StandController.py           # Стойка
          RestController.py            # Покой
          PIDController.py             # PID компенсация
        ForwardKinematics/             # Прямая кинематика
        InverseKinematics/             # Обратная кинематика
        RoboticsUtilities/             # Трансформации
    quadropted_msgs/          # Кастомные сообщения/сервисы
      msg/                    # 4 сообщения
      srv/                    # 1 сервис
    go1_description/          # Модель Unitree Go1
    go2_description/          # Модель Unitree Go2
```

---

## 2. Описание пакетов

### docker

Инфраструктура контейнеризации. 10-этапная Docker сборка с кэшированием слоёв (APT, pip, ccache). compose.yml настраивает GUI passthrough (X11), host network, privileged mode.

### gazebo_sim

Оркестрация симуляции. Launch-файлы запускают Gazebo мир, спавнят роботов, запускают Nav2 стек для каждого робота.

### quadropted_controller

Основной пакет управления на Python. Содержит:

- RobotControllerNode -- главный узел (60 Гц)
- QuadrupedOdometryNode -- оценка положения по контакту стоп
- RobotController -- конечный автомат режимов
- Gait Controllers -- Trot, Crawl, Stand, Rest
- Inverse/Forward Kinematics -- расчёт углов и позиций стоп
- PID Controller -- компенсация крена/тангажа

### quadropted_msgs

Кастомные ROS интерфейсы:

- RobotModeCommand -- переключение режимов (REST/TROT/CRAWL/STAND)
- RobotVelocity -- команда скорости с robot_id
- RobotFootContact -- состояния контакта стоп
- RobotGaitCommand -- команда походки
- RobotBehaviorCommand -- сервис sit/up/walk

### go1_description / go2_description

URDF/Xacro модели роботов Unitree Go1 и Go2 с физическими свойствами и визуальными мешами.

---

## 3. Как робот управляется

### Конечный автомат

RobotController -- это конечный автомат с 4 состояниями:

- REST -- покой, робот неподвижен
- TROT -- ходьба рысью (диагональные пары ног)
- CRAWL -- ползание (последовательное движение ног)
- STAND -- стойка (вращение на месте)

### Цикл управления

1. RobotControllerNode работает на частоте 60 Гц
2. На каждом такте вызывается текущий контроллер
3. Контроллер вычисляет позиции стоп (3x4 матрица)
4. Обратная кинематика преобразует позиции стоп в 12 углов сочленений
5. Углы публикуются в joint_group_controller/commands
6. Gazebo применяет углы к модели робота

### Обратная кинематика

Для каждой ноги вычисляются 3 угла:
- hip (abduction/adduction) -- вращение вокруг Z
- thigh (pitch) -- вращение вокруг Y
- calf (pitch) -- вращение вокруг Y

Алгоритм использует теорему косинусов для вычисления углов по позиции стопы.

### Одометрия

QuadrupedOdometryNode оценивает положение робота:
1. FK вычисляет позиции всех 4 стоп по 12 углам
2. Определяются стопы на земле (из foot_contact)
3. Смещения стоп на земле усредняются (скользящее окно 14)
4. Усреднённые смещения интегрируются в глобальную позицию
5. Курс берётся из IMU (yaw из кватерниона)

---

## 4. Режимы работы робота

### REST

Робот в покое. Все ноги в позиции default_stance. PID компенсация крена/тангажа активна.

### TROT

Ходьба рысью. Диагональные пары ног двигаются синхронно:
- Фаза 1: FL + RR в переносе
- Фаза 2: FR + RL в переносе
- 4 фазы цикла
- Скорость X: до 0.035 м/с
- Скорость Y: до 0.012 м/с
- Yaw: до 0.5 рад/с

### CRAWL

Ползание. Ноги двигаются последовательно:
- 8 фаз цикла
- Каждая нога поднимается по очереди
- Скорость X: до 0.011 м/с
- Yaw: до 0.15 рад/с

### STAND

Стойка. Робот стоит, может вращаться на месте:
- Позиции стоп фиксированы
- Команды скорости интегрируются в положение тела
- Максимальная линейная скорость: 0.035 м/с
- Максимальная угловая скорость: 0.1 рад/с

---

## 5. Поток данных

```
Teleop/Nav2 --/cmd_vel--> cmd_vel_handler --/robot_velocity--> RobotController
                                                                        |
/robot_mode ----------------------------------------------------------->|
                                                                        v
RobotController --> Joint Angles --> /joint_group_controller/commands
                                              |
                                    Joint angles --> FK --> OdometryNode --> /odom
                                              |
                                    Foot contacts <-- TrotGaitController
                                              |
                                    EKF (odom + IMU) --> Nav2
```

---

## 6. Именование

### Топики

Каждый робот работает в своём namespace:

- /robot1/cmd_vel
- /robot1/robot_mode
- /robot1/odom
- /robot1/joint_states

### Сообщения

Кастомные сообщения содержат robot_id для мультироботной системы:

- RobotModeCommand: mode + robot_id
- RobotVelocity: robot_id + cmd_vel

---

## 7. FAQ

### Где хранятся логи?

В контейнере: /root/ws/logs/
На хосте: src/docker/logs/gazebo/

### Как изменить параметры контроллера?

Параметры контроллеров заданы в коде Python файлов. Например, лимиты скорости в TrotGaitController.py.

### Можно ли добавить нового робота?

Да. Добавьте запись в src/gazebo_sim/config/robots.yaml с именем и координатами спавна.

### Как изменить высоту робота в режиме STAND?

Измените default_height в RobotController.py или подайте команду с нужной высотой через RobotVelocity.

### Что делать, если робот падает?

- Проверьте, что Gazebo запущен корректно
- Убедитесь, что контроллер работает: ros2 node list | grep controller
- Проверьте частоту топиков: ros2 topic hz /robot1/joint_states (должна быть около 60 Гц)

---

## Что дальше

Вы изучили архитектуру проекта. Следующие шаги:

1. Закрепите материал -- перечитайте сложные моменты
2. Переходите к методичке 05-exercises -- выполняйте практические упражнения
3. Экспериментируйте -- изменяйте параметры и наблюдайте

---

## Связанные документы

- [На главную](../README.md) -- Карта всех методичек
- [Методичка 03-docker](../03-docker/README.md) -- Docker для ROS2
- [Методичка 05-exercises](../05-exercises/README.md) -- Практические упражнения

---

*Последнее обновление: Март 2026*
