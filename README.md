# WalkingRobotSim

Симуляция шагающего робота в Gazebo Harmonic с ROS 2 Jazzy для автономной навигации и распознавания объектов. Проект для дипломной работы и курсов МГТУ им. Баумана.

## 📋 Описание

WalkingRobotSim - это комплексный симулятор шагающих роботов, разработанный для обучения и исследований в области робототехники. Проект предоставляет полнофункциональную среду для разработки и тестирования алгоритмов автономной навигации, компьютерного зрения и управления движением.

### 🤖 Поддерживаемые роботы

- **Unitree Go1** - четвероногий робот
- **Unitree Go2** - улучшенная версия четвероногого робота

### 🌟 Основные возможности

- **Физическая симуляция**: Реалистичная симуляция в Gazebo Harmonic с точными моделями роботов
- **Навигация**: SLAM и автономная навигация с использованием Nav2
- **Компьютерное зрение**: Распознавание объектов с помощью YOLO
- **Управление движением**: Реализация различных походок и режимов движения
- **Картографирование**: Создание 2D и 3D карт окружающей среды
- **Docker поддержка**: Легкое развертывание в контейнерах

Проект разрабатывается с консультациями Центра молодежной робототехники МГТУ (@robotics_bmstu).

## 🛠️ Установка

### 🐧 Вариант 1: Локальная установка (Ubuntu 22.04 + ROS 2 Jazzy)

1. Установите ROS 2 Jazzy:

   ```bash
   sudo apt update && sudo apt install curl gnupg lsb-release
   sudo curl -sSL https://repo.ros2.org/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
   sudo apt update
   sudo apt install ros-jazzy-desktop
   ```

2. Установите симулятор и дополнительные пакеты (для Gazebo Harmonic используйте `ros_gz`):

   ```bash
   # Для Gazebo Harmonic (ros_gz) и мостов ROS-GZ
   sudo apt install ros-jazzy-ros-gz ros-jazzy-ros-gz-plugins
   # Навигация и SLAM
   sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup
   sudo apt install ros-jazzy-slam-toolbox
   ```

3. Клонируйте репозиторий и установите зависимости:

   ```bash
   git clone https://github.com/<your-username>/WalkingRobotSim.git
   cd WalkingRobotSim
   ```

4. Соберите проект:
   ```bash
   colcon build
   source install/setup.bash
   ```

### 🐳 Вариант 2: Запуск через Docker (рекомендуется)

1. Установите Docker и Docker Compose:

   ```bash
   sudo apt install docker.io docker-compose
   sudo usermod -aG docker $USER
   ```

2. Соберите Docker-образ:

   ```bash
   ./docker-compose.sh build
   ```

   Или для пересборки без кэша:

   ```bash
   ./docker-compose.sh build --no-cache
   ```

3. Запустите контейнер:

   ```bash
   ./docker-compose.sh up
   ```

4. Для подключения к запущенному контейнеру:

   ```bash
   ./docker-compose.sh exec
   ```

5. Для остановки контейнера:
   ```bash
   ./docker-compose.sh down
   ```

### 🔄 Преимущества нового скрипта docker-compose.sh

Новый скрипт `docker-compose.sh` предоставляет следующие преимущества по сравнению со старыми скриптами:

- **Единый интерфейс**: Все операции с контейнером через один скрипт
- **Расширенные функции**: Добавлена команда `clean` для очистки неиспользуемых ресурсов Docker
- **Гибкость**: Поддержка опции `--no-cache` для пересборки без использования кэша
- **Улучшенный вывод**: Цветовая индикация и более информативные сообщения
- **Повышенная надежность**: Дополнительные проверки и обработка ошибок

## ▶️ Использование

### 🚀 Быстрый старт

1. Запустите симуляцию робота Go2:

   ```bash
   ros2 launch ros2_gazebo go2_run.launch.py
   ```

2. Запустите навигацию:

   ```bash
   ros2 launch ros2_navigation navigation2.launch.py
   ```

3. Запустите картографирование:

   ```bash
   ros2 launch ros2_cartography cartography.launch.py
   ```

4. Запустите распознавание объектов:
   ```bash
   ros2 launch yolo_bringup yolo.launch.py
   ```

### 📋 Распространенные команды

| Команда                                              | Описание                      |
| ---------------------------------------------------- | ----------------------------- |
| `ros2 launch ros2_gazebo go1_run.launch.py`          | Запуск симуляции Go1          |
| `ros2 launch ros2_gazebo go2_run.launch.py`          | Запуск симуляции Go2          |
| `ros2 launch ros2_cartography cartography.launch.py` | Запуск SLAM                   |
| `ros2 launch ros2_navigation navigation2.launch.py`  | Запуск навигации              |
| `ros2 launch yolo_bringup yolo.launch.py`            | Запуск распознавания объектов |

### 🎮 Управление роботом

1. Для управления с клавиатуры:

   ```bash
   ros2 run teleop_twist_keyboard teleop_twist_keyboard
   ```

2. Для запуска предопределенного контроллера:
   ```bash
   ros2 run unitree_guide2 junior_ctrl
   ```

### 🧭 Автономная навигация

Для использования автономной навигации необходимо выполнить следующую последовательность действий:

1. Запустите симуляцию робота:

   ```bash
   ros2 launch ros2_gazebo go1_run.launch.py
   ```

2. Запустите навигацию:

   ```bash
   ros2 launch ros2_navigation navigation.launch.py
   ```

3. Запустите контроллер робота:

   ```bash
   ros2 run unitree_guide2 junior_ctrl
   ```

4. Управление навигацией:
   - Переключите кнопку клавиатуры с `1` --> `2` (подождите, пока робот не встанет)
   - Затем нажмите `5`
   - В RVIz установите изначальную позицию робота с помощью `2D Pose Estimate`
   - В верхней панели Nav2 кликните в нужное место для автономной навигации

## 📁 Структура проекта

```
WalkingRobotSim/
├── src/
│   ├── go1_description/        # Модель и описание робота Go1
│   ├── go2_description/        # Модель и описание робота Go2
│   ├── ros2_gazebo/           # Launch-файлы и миры для Gazebo
│   ├── ros2_navigation/       # Пакеты навигации Nav2
│   ├── ros2_cartography/     # Пакеты картографирования
│   ├── ros2_yolo_recognition/ # Распознавание объектов YOLO
│   └── unitree_guide2/       # Контроллеры движения
├── worlds/                   # Сцены и миры для симуляции
├── launch/                  # Основные launch-файлы
├── Dockerfile               # Конфигурация Docker-образа
├── docker-compose.sh        # Улучшенный скрипт управления Docker Compose
└── docs/                   # Документация
    └── docker-compose-ru.md # Документация по использованию docker-compose.sh
```

## ⚙️ Требования к системе

### Минимальные требования

- **ОС**: Ubuntu 22.04 LTS
- **Процессор**: 4 ядра
- **ОЗУ**: 8 GB
- **Графика**: Совместимая с OpenGL 3.3

### Рекомендуемые требования

- **ОС**: Ubuntu 22.04 LTS
- **Процессор**: 8 ядер (Intel i7/AMD Ryzen 7 или лучше)
- **ОЗУ**: 16 GB
- **Графика**: Дискретная видеокарта с 4+ GB VRAM
- **Свободное место**: 20+ GB

### Зависимости

- ROS 2 Humble
- Gazebo Harmonic
- Navigation2
- SLAM Toolbox
- OpenCV
- PyTorch (для YOLO)

## 🤖 Модели роботов

### Unitree Go1

- 12 сервоприводов
- IMU (гироскоп, акселерометр)
- LiDAR (в симуляции)
- RGB камера (в симуляции)

### Unitree Go2

- Улучшенная версия Go1
- Более точные датчики
- Улучшенная модель для симуляции

## 🗺️ Навигация и картографирование

### SLAM (Simultaneous Localization and Mapping)

Проект поддерживает построение карт с помощью SLAM Toolbox:

```bash
ros2 launch ros2_cartography cartography.launch.py
```

### Аварийная навигация (Nav2)

Для автономной навигации используется Navigation2:

```bash
ros2 launch ros2_navigation navigation2.launch.py
```

### Поддерживаемые типы карт

- 2D occupancy grid maps
- 3D point cloud maps
- Costmaps для планирования пути

## 👁️ Компьютерное зрение

### YOLO Object Detection

Проект интегрирует YOLO для распознавания объектов:

```bash
ros2 launch yolo_bringup yolo.launch.py
```

### Поддерживаемые модели

- YOLOv5
- YOLOv8
- YOLOv11
- Custom models

### Возможности

- 2D обнаружение объектов
- 3D позиционирование (с depth-камерой)
- Трекинг объектов
- Распознавание классов из COCO dataset

## 🧪 Тестирование

### Локальное тестирование GitHub Actions

Перед выполнением `git push` рекомендуется протестировать workflows:

```bash
./test-workflows.sh
```

Этот скрипт проверит:

- Синтаксис YAML файлов
- Сборку Docker-образа
- Запуск контейнера

## 🆘 Решение проблем

### Распространенные ошибки

**Ошибка**: `Failed to initialize rosdep`
**Решение**:

```bash
sudo rosdep init
rosdep update
```

**Ошибка**: `Gazebo not found`
**Решение**: Убедитесь, что установлены пакеты Gazebo Harmonic:

```bash
# Для Gazebo Harmonic (ros_gz) установите ros_gz и плагины
sudo apt install ros-jazzy-ros-gz ros-jazzy-ros-gz-plugins
```

**Ошибка**: `Docker permission denied`
**Решение**: Добавьте пользователя в группу docker:

```bash
sudo usermod -aG docker $USER
# Перезагрузите сессию
```

### Диагностика

Для проверки состояния системы используйте:

```bash
ros2 node list
ros2 topic list
ros2 service list
```

## 📚 Документация

### Полезные ресурсы

- [ROS 2 Documentation](https://docs.ros.org/en/humble/)
- [Gazebo Documentation](https://gazebosim.org/docs/)
- [Navigation2 Documentation](https://navigation.ros.org/)
- [YOLO Documentation](https://docs.ultralytics.com/)

### Структура пакетов

Каждый пакет в `src/` содержит:

- `launch/` - Launch-файлы для запуска
- `config/` - Конфигурационные файлы
- `params/` - Параметры для узлов ROS
- `rviz/` - Конфигурации RViz
- `maps/` - Файлы карт (в navigation/cartography пакетах)

## 📄 Лицензия

Этот проект лицензирован по лицензии Apache 2.0 - подробности в файле [LICENSE](LICENSE).

## 🙏 Благодарности

- Центру молодежной робототехники МГТУ им. Н.Э. Баумана (@robotics_bmstu)
- Сообществу ROS 2
- Unitree Robotics за предоставление моделей роботов
