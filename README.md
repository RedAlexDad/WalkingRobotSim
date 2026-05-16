# Walking Robot Simulator

Полноценный симулятор четвероногого робота на базе ROS 2 Jazzy с Gazebo Sim,
Docker-контейнеризацией, Nav2 навигацией и CI/CD пайплайном.

Возможности:
- Физическая симуляция в Gazebo Sim с динамикой четырёхногого робота
- Две реализации контроллера ходьбы: **Python** и **C++** (53.5x быстрее)
- [Навигация по waypoints](docs/navigation.md) через Nav2 + кастомный RViz инструмент
- Одометрия на основе кинематики ног, EKF фильтрация с IMU
- Мультироботная симуляция с изолированными namespace
- Docker образ с 6-stage кэшируемой сборкой

---

## Содержание

- [Архитектура проекта](docs/architecture.md)
- [Быстрый старт](#быстрый-старт)
- [Управление симуляцией](#управление-симуляцией)
- [Waypoint навигация](docs/navigation.md)
- [Режимы работы робота](#режимы-работы-робота)
- [Python vs C++](#python-vs-c)
- [CI/CD](docs/ci-cd.md)
- [Технические детали](#технические-детали)
- [Документация](#документация)
- [Благодарности](#благодарности)

---

## Архитектура проекта

[Полное описание архитектуры](docs/architecture.md)

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
├── docs/                        # Документация
├── reports/                     # Отчёты и анализ
└── .github/workflows/           # GitHub Actions CI/CD
```

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

# Сборка + запуск контейнера
make deploy

# Python контроллер (основной режим)
make gazebo-py

# C++ контроллер (производительный режим)
make gazebo-cpp
```

[Docker окружение](src/docker/README.md)
[Запуск симуляции](src/gazebo_sim/README.md)

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
| `make teleop` | Управление с клавиатуры |

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

[Подробнее о мультироботном запуске](src/gazebo_sim/README.md)

---

## Waypoint навигация

[Полное описание](docs/navigation.md)

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

[Сравнение реализации gait в Python и C++](reports/gait-switch-comparison.md)

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

[Полный бенчмарк и отчёт](reports/benchmark-python-cpp.md)
[Отчёт об оптимизации](reports/performance-optimization-report.md)
[Результаты кросс-валидации](reports/python_vs-cpp-cross-validation.md)

---

## CI/CD

[Полное описание](docs/ci-cd.md)

Два workflow GitHub Actions:

| Workflow | Описание | Время |
|----------|----------|-------|
| **CI** | Docker build, линтинг (Python/C++/YAML), C++ unit тесты | 5-10 мин |
| **Simulation Test** | Интеграционные тесты в контейнере | 15-20 мин |

Локальные проверки:
```bash
make ci-lint       # Линтинг всех языков
make ci-test-cpp   # C++ unit тесты
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
- **Навигация:** Nav2
- **Контроллеры:** ros2_control (JointGroupPositionController)
- **Локализация:** AMCL, EKF (robot_localization)

### Теги версий

- [v.0.0.1](https://github.com/RedAlexDad/WalkingRobotSim/releases/tag/v.0.0.1) — Первая стабильная версия: C++ контроллер, trot gait, кросс-валидация
- [v.0.0.2](https://github.com/RedAlexDad/WalkingRobotSim/releases/tag/v.0.0.2) — Waypoint навигация, YAML конфиги, GetWaypoints сервис, исправлен circular import одометрии

---

## Документация

### docs/ — документация

| Файл | О чём |
|------|-------|
| [architecture.md](docs/architecture.md) | Архитектура проекта, топики, пакеты |
| [navigation.md](docs/navigation.md) | Waypoint навигация, инструменты, форматы |
| [ci-cd.md](docs/ci-cd.md) | CI/CD пайплайн, GitHub Actions |

### reports/ — отчёты и анализ

| Файл | О чём |
|------|-------|
| [waypoint-executor-fix.md](reports/waypoint-executor-fix.md) | Разработка waypoint навигации, 9 итераций |
| [gait-switch-comparison.md](reports/gait-switch-comparison.md) | Сравнение gait Python vs C++ |
| [benchmark-python-cpp.md](reports/benchmark-python-cpp.md) | Бенчмарк 53.5x ускорение |
| [performance-optimization-report.md](reports/performance-optimization-report.md) | Оптимизация производительности C++ |
| [python_vs-cpp-cross-validation.md](reports/python_vs-cpp-cross-validation.md) | Кросс-валидация, 12/12 тестов |
| [python-odometry-drift-plan.md](reports/python-odometry-drift-plan.md) | План устранения дрифта одометрии |

### Внутренние пакеты

- [Docker окружение](src/docker/README.md)
- [Запуск симуляции](src/gazebo_sim/README.md)

---

## Благодарности

Проект основан на работе:

- **mike4192** — [SpotMicro](https://github.com/mike4192/spotMicro) (кинематика четвероногих)
- **Unitree Robotics** — [A1 ROS](https://github.com/unitreerobotics/a1_ros)
- **lnotspotl** — алгоритмы ходьбы и оптимизация
- **anujjain-dev** — [unitree-go2-ros2](https://github.com/anujjain-dev/unitree-go2-ros2) (адаптация под ROS 2 Jazzy)

### Лицензия

MIT License — [LICENSE](LICENSE)
