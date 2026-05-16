# Walking Robot Simulator

Полноценный симулятор четвероногого робота на базе ROS 2 Jazzy с Gazebo Sim,
Docker-контейнеризацией, Nav2 навигацией и CI/CD пайплайном.

Возможности:
- Физическая симуляция в Gazebo Sim с динамикой четырёхногого робота
- Две реализации контроллера ходьбы: **Python** и **C++** (53.5x быстрее)
- Навигация по waypoints через Nav2 + кастомный RViz инструмент
- Одометрия на основе кинематики ног, EKF фильтрация с IMU
- Мультироботная симуляция с изолированными namespace
- Docker образ с 6-stage кэшируемой сборкой

---

## Содержание

- [Архитектура проекта](#архитектура-проекта)
- [Быстрый старт](#быстрый-старт)
- [Управление симуляцией](#управление-симуляцией)
- [Waypoint навигация](#waypoint-навигация)
- [Режимы работы робота](#режимы-работы-робота)
- [Python vs C++](#python-vs-c)
- [CI/CD и тестирование](#cicd-и-тестирование)
- [Технические детали](#технические-детали)
- [Документация](#документация)
- [Благодарности](#благодарности)

---

## Архитектура проекта

```
WalkingRobotSim/
├── Makefile                     # Полное управление: сборка, запуск, навигация
├── src/
│   ├── docker/                  # Docker конфигурация (compose.yml, Dockerfile)
│   ├── gazebo_sim/              # Launch файлы, миры Gazebo, waypoints, SDF
│   ├── go1_description/         # URDF описание робота Unitree Go1
│   ├── go2_description/         # URDF описание робота Unitree Go2
│   ├── quadropted_controller/   # Python контроллер (RobotController, одометрия)
│   ├── quadropted_controller_cpp/ # C++ контроллер (53.5x ускорение)
│   ├── quadropted_msgs/         # ROS 2 сообщения (Waypoint, RobotVelocity и др.)
│   ├── rviz_waypoint_tool/      # Кастомный RViz инструмент для waypoints
│   └── tests/                   # Интеграционные тесты Python vs C++
├── docs/                        # Документация и отчёты
└── .github/workflows/           # GitHub Actions CI/CD
```

[Детальная архитектура C++ пакета](docs/performance-optimization-report.md)
[Структура Docker сборки](src/docker/README.md)

---

## Быстрый старт

### Требования

- Docker 20.10+ с BuildKit
- Docker Compose v2
- Linux с X11 (для GUI симуляции)
- 8GB+ RAM, 4+ CPU cores

### Запуск симуляции

```bash
# Клонирование
git clone https://github.com/RedAlexDad/WalkingRobotSim.git
cd WalkingRobotSim

# Сборка и запуск контейнера
make deploy

# Python контроллер (основной режим)
make gazebo-py

# C++ контроллер (производительный режим)
make gazebo-cpp
```

[Полное руководство по запуску](src/docker/README.md)

---

## Управление симуляцией

### Makefile

Вся работа с симулятором — через `make`. Основные цели:

| Команда | Описание |
|---------|----------|
| `make deploy` | Сборка образа + запуск контейнера |
| `make up` | Запуск остановленного контейнера |
| `make down` | Остановка контейнера |
| `make shell` | Вход в bash контейнера |
| `make logs` | Логи контейнера |
| `make gazebo` | Запуск симуляции (дефолтный контроллер) |
| `make gazebo-py` | Запуск с Python контроллером |
| `make gazebo-cpp` | Запуск с C++ контроллером |
| `make teleop` | Управление с клавиатуры (`teleop_twist_keyboard`) |

Полный список целей:
```bash
make help
```

### Переключение моделей роботов

Робот определяется в launch файле через URDF пакет:
- `go2_description` — Unitree Go2 (по умолчанию)
- `go1_description` — Unitree Go1

Настройка в `src/gazebo_sim/launch/`.

### Мультироботная симуляция

Поддерживается одновременная работа нескольких роботов. Каждый имеет собственный namespace и Nav2. Настройка в `robot.config` параметрах launch файла.

[Настройка мультироботной симуляции](src/gazebo_sim/README.md)

---

## Waypoint навигация

Система навигации позволяет расставлять точки в RViz через WaypointTool и запускать маршрут.

### Makefile цели для waypoints

| Команда | Описание |
|---------|----------|
| `make waypoint-start` | Загрузить waypoints и начать навигацию |
| `make waypoint-navigate` | Начать/продолжить навигацию |
| `make waypoint-stop` | Остановить навигацию (с сохранением прогресса) |
| `make waypoint-resume` | Продолжить с прерванного waypoint |
| `make waypoint-clear` | Очистить все waypoints |
| `make waypoint-load FILE=test` | Загрузить waypoints из YAML/JSON файла |
| `make waypoint-get` | Показать текущие waypoints |

### Формат waypoints

Waypoints хранятся в YAML (с комментариями) или JSON:
```yaml
# config/waypoints/default.yaml
waypoints:
  - point: {x: 1.5, y: 1.0, z: 0.0}
    yaw: 0.0
  - point: {x: -0.5, y: -2.0, z: 0.0}
    yaw: 1.57
```

### Архитектура

- `waypoint_collector.py` — сбор и управление waypoints, сервис `/get_waypoints`
- `rviz_waypoint_tool/` — кастомный RViz инструмент для расстановки точек
- Nav2 `waypoint_follower` — асинхронный ActionServer FollowWaypoints

[Полный отчёт разработки waypoint-навигации](docs/waypoint-executor-fix.md)
[Краткий отчёт](docs/waypoint-collector-fix-report.md)

---

## Режимы работы робота

Робот имеет 4 режима движения:

| Режим | Описание |
|-------|----------|
| REST | Положение стоя, робот не двигается |
| STAND | Повороты на месте, подготовка к ходьбе |
| TROT | Рысь — базовый режим ходьбы |
| CRAWL | Ползком — медленное движение с опорой на 3 ноги |

### Переключение режимов

```bash
# Через топик
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'TROT', robot_id: 1}"

# Через Makefile
make trot
make rest
make crawl
make stand
```

### Управление движением

```bash
# Через клавиатуру
make teleop

# Через сервис поведения
ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand "{command: 'walk'}"
```

Команды сервиса поведения:
- `walk` — встать (REST) и перейти в TROT
- `up` — встать (REST), не двигаться
- `sit` — сесть (STAND)

[Сравнение реализации gait в Python и C++](docs/gait-switch-comparison.md)

---

## Python vs C++

Контроллер реализован на двух языках:

| Характеристика | Python | C++ |
|----------------|--------|-----|
| Время полного цикла | 0.148 ms | 0.003 ms |
| Ускорение | 1x | **53.5x** |
| Unit тесты | 34 | 27 |
| Кросс-валидация | — | 12/12 совпадений с Python |

Ключевые компоненты C++ пакета:
- TrotGaitController, CrawlGaitController, RestController, StandController
- Forward/Inverse Kinematics с Eigen3
- Одометрия с O(1) скользящим средним
- PID контроллер

[Полный бенчмарк и отчёт](docs/benchmark-python-cpp.md)
[Отчёт об оптимизации](docs/performance-optimization-report.md)
[Результаты кросс-валидации](docs/python_vs-cpp-cross-validation.md)

---

## CI/CD и тестирование

### GitHub Actions

Два workflow:
- **CI** — сборка Docker, линтинг Python/C++/YAML, C++ unit тесты
- **Simulation test** — интеграционные тесты в Gazebo, проверка топиков

Триггеры: push в `main`/`jazzy`, PR в `main`/`jazzy`.

[Детали CI/CD пайплайна](docs/ci-cd-improvement-plan.md)

### Локальное тестирование

```bash
# Полный цикл
./test-workflows.sh test

# Unit тесты
make test-correctness   # Python old vs new (34 теста)
make test-cpp           # C++ gtest (27 тестов)
make test-cross         # Python vs C++ кросс-тест (12 тестов)

# Бенчмарк
make benchmark          # Сводная таблица Python vs C++

# CI проверки
make ci-lint            # Линтинг всех языков
make ci-test-cpp        # C++ unit тесты
```

---

## Технические детали

### Docker образ

- **Базовый образ:** `osrf/ros:jazzy-desktop`
- **Размер:** 5-6 GB
- **6-stage сборка:** зависимости ROS, симуляция, навигация, Python, финальный
- **Кэш первого уровня:** 30-60 секунд при повторной сборке

[Docker конфигурация](src/docker/README.md)

### ROS 2 компоненты

- **Версия:** Jazzy (совместимость с Humble)
- **DDS:** CycloneDDS
- **Симулятор:** Gazebo Sim 8
- **Навигация:** Nav2 (controller_server, planner_server, bt_navigator, waypoint_follower)
- **Контроллеры:** ros2_control (JointGroupPositionController)
- **Локализация:** AMCL, EKF (robot_localization)

### Теги версий

- [v.0.0.1](https://github.com/RedAlexDad/WalkingRobotSim/releases/tag/v.0.0.1) — Первая стабильная версия: C++ контроллер, trot gait, кросс-валидация
- [v.0.0.2](https://github.com/RedAlexDad/WalkingRobotSim/releases/tag/v.0.0.2) — Waypoint навигация, YAML конфиги, GetWaypoints сервис, исправлен circular import одометрии

---

## Документация

### Отчёты и анализ

- [Разработка waypoint навигации](docs/waypoint-executor-fix.md) — полный процесс, 9 итераций
- [Сравнение gait Python vs C++](docs/gait-switch-comparison.md)
- [Бенчмарк Python vs C++](docs/benchmark-python-cpp.md) — 53.5x ускорение
- [Отчёт об оптимизации производительности](docs/performance-optimization-report.md)
- [Кросс-валидация Python vs C++](docs/python_vs-cpp-cross-validation.md) — 12/12 тестов
- [План устранения дрифта одометрии](docs/python-odometry-drift-plan.md)

### Внутренние руководства

- [`gazebo_sim/README.md`](src/gazebo_sim/README.md) — детали launch файлов и конфигурации
- [`src/docker/QUICK_START.md`](src/docker/README.md) — Docker гайд
- [`docs/rebuild-vs-restart.md`](docs/rebuild-vs-restart.md) — когда пересобирать vs перезапускать

### Внешние ссылки

- [ROS 2 Jazzy Documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Sim](http://gazebosim.org/)
- [Nav2](https://navigation.ros.org/)
- [Unitree Robotics](https://www.unitree.com/)

---

## Благодарности

Проект основан на работе:

- **mike4192** — [SpotMicro](https://github.com/mike4192/spotMicro) (кинематика четвероногих)
- **Unitree Robotics** — [A1 ROS](https://github.com/unitreerobotics/a1_ros)
- **lnotspotl** — алгоритмы ходьбы и оптимизация
- **anujjain-dev** — [unitree-go2-ros2](https://github.com/anujjain-dev/unitree-go2-ros2) (адаптация под ROS 2 Jazzy)

### Лицензия

MIT License — [LICENSE](LICENSE)
