# 🤖 Walking Robot Simulator

Полноценный симулятор ходячих роботов на базе ROS 2 Jazzy с Docker-контейнеризацией и CI/CD pipeline.

---

## 🚀 Быстрый старт

### Требования
- Docker 20.10+ с BuildKit
- Docker Compose
- 8GB+ RAM, 4+ CPU cores
- Linux (рекомендуется Ubuntu 22.04+)

### Установка и запуск

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/RedAlexDad/WalkingRobotSim.git
cd WalkingRobotSim

# 2. Сделайте скрипт исполняемым
chmod +x test-workflows.sh

# 3. Соберите Docker образ (15-30 минут первый раз)
cd src/docker
docker compose build

# 4. Запустите симулятор
docker compose up -d

# 5. Проверьте статус
docker compose ps
```

---

## 🏗️ Архитектура проекта

### Структура директорий
```
WalkingRobotSim/
├── src/                          # Исходный код
│   ├── docker/                   # Docker конфигурация
│   │   ├── compose.yml           # Основной compose файл
│   │   ├── compose.multistage.yml # Multistage конфигурация
│   │   └── Dockerfile            # 6-stage сборка
│   ├── gazebo_sim/               # Симулятор Gazebo
│   ├── go1_description/          # Описание робота Go1
│   ├── go2_description/          # Описание робота Go2
│   └── ...                       # Другие ROS пакеты
├── .github/workflows/            # GitHub Actions CI/CD
│   └── ci.yml                    # Автоматизированное тестирование
├── test-workflows.sh             # Локальное тестирование
└── README.md                     # Этот файл
```

### Docker Multi-stage Build
- **Stage 1:** Базовый образ с системными зависимостями
- **Stage 2:** ROS Core пакеты  
- **Stage 3:** ROS Control и Simulation
- **Stage 4:** ROS Navigation и Vision
- **Stage 5:** Python зависимости и инструменты
- **Stage 6:** Финальный production-ready образ

---

## 🎮 Управление симулятором

### Основные команды
```bash
# Запуск симулятора
cd src/docker
docker compose up -d

# Остановка
docker compose down

# Просмотр логов
docker compose logs -f

# Вход в контейнер
docker compose exec simulator bash

# Пересборка образа
docker compose build --no-cache

# Проверка здоровья контейнера
docker compose ps
```

### Управление роботом

#### Режимы работы робота
Робот поддерживает несколько режимов:

- **REST** – Положение по умолчанию, робот не может двигаться
- **STAND** – Режим, в котором робот может вращаться на месте  
- **TROT** – Режим ходьбы

Робот работает с 12 степенями свободы. Для включения вращения переключите режим в "STAND":

```bash
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'STAND', robot_id: 1}"
```

После переключения режимов управляйте роботом с помощью команд скорости:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

#### Изменение поведения робота
Робот может садиться и вставать с помощью сервиса `robot_behavior_command`:

```bash
ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand "{command: 'walk'}"
```

Возможные команды:
- `walk` – Робот встает (REST) и может ходить (TROT)
- `up` – Робот встает (REST) и блокирует движение
- `sit` – Робот садится (STAND)

#### Мультироботная симуляция
Репозиторий поддерживает одновременную работу нескольких роботов. У каждого робота есть доступ к Nav2. В файле robot.config добавьте namespace робота и координаты спавна в мире.

#### Переключение моделей роботов
Можно переключаться между моделями роботов (go2, go1) в файле gazebo_multi_nav2_world.launch.py:
- Для go2: используйте "go2_description"  
- Для go1: используйте "go1_description"

---

## 🔧 Локальное тестирование

Используйте `test-workflows.sh` для локального тестирования перед пушем:

```bash
# Полный цикл тестирования
./test-workflows.sh test

# Только сборка
./test-workflows.sh build

# Очистка ресурсов
./test-workflows.sh clean

# Справка
./test-workflows.sh help
```

### Что проверяет скрипт:
- ✅ Наличие Docker и Docker Compose
- ✅ Синтаксис YAML файлов
- ✅ Структуру проекта
- ✅ Сборку Docker образа
- ✅ Запуск и здоровье контейнера
- ✅ ROS 2 функциональность

---

## 🔄 CI/CD Pipeline

Автоматизированное тестирование в GitHub Actions включает:

### Job: docker-build
- Сборка Docker образа
- Базовый тест контейнера

### Job: simulation-test
- Запуск полной симуляции
- Проверка ROS узлов
- Вывод всех доступных топиков
- Тест teleop функциональности
- Проверка данных с лидара
- Тест стабильности робота

### Триггеры
- Push в ветки: `main`, `jazzy`
- Pull Request в ветки: `main`, `jazzy`

---

## 🤖 Поддерживаемые роботы

### Unitree Go1
- Четырехногий робот средней размерности
- Полная модель URDF
- Настроенные контроллеры

### Unitree Go2  
- Улучшенная версия Go1
- Оптимизированная динамика
- Расширенная сенсорика

---

## 📊 Технические характеристики

### Docker образ
- **Базовый образ:** `osrf/ros:jazzy-desktop`
- **Размер:** 5-6 GB
- **Сборка с кэшем:** 30-60 секунд
- **Первая сборка:** 15-30 минут

### Системные требования
- **CPU:** 4+ cores (рекомендуется 8)
- **RAM:** 8GB+ (рекомендуется 16GB)
- **Storage:** 20GB+ свободного места
- **GPU:** Опционально для визуализации

### ROS 2 компоненты
- **Версия:** Jazzy (совместим с Humble)
- **DDS:** CycloneDDS
- **Симулятор:** Gazebo 11
- **Навигация:** Nav2
- **Контроллеры:** ros2_control

---

## 🐛 Troubleshooting

### Проблемы с Docker
```bash
# Очистка Docker
docker system prune -a

# Пересборка без кэша
docker compose build --no-cache

# Проверка статуса
docker compose ps
```

### Проблемы с ROS
```bash
# Проверка переменных окружения
env | grep ROS

# Перезапуск DDS
export RMW_IMPLEMENTATION=rmw_cyclonedx_cpp

# Диагностика узлов
ros2 doctor
```

### Проблемы с GUI
```bash
# Настройка DISPLAY
export DISPLAY=:0
xhost +local:root

# Перезапуск с GUI
docker compose down
docker compose up -d
```

---

## 📈 Мониторинг и отладка

### Просмотр логов
```bash
# Логи контейнера
docker compose logs -f simulator

# Логи ROS
docker compose exec simulator tail -f /root/ws/logs/*.log
```

### Мониторинг ресурсов
```bash
# Статистика Docker
docker stats

# Использование памяти
docker compose exec simulator free -h

# Загрузка CPU
docker compose exec simulator top
```

### Отладка сборки
```bash
# Детальный вывод сборки
docker compose build --progress=plain

# Проверка слоев
docker history walking_robot_sim:latest
```

---

## 🤝 Вклад в проект

### Ветки разработки
- `main` - стабильная версия
- `jazzy` - разработка под ROS 2 Jazzy
- `humble` - поддержка ROS 2 Humble (ограничена)

### Процесс внесения изменений
1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Протестируйте локально: `./test-workflows.sh test`
5. Создайте Pull Request

---

## 📚 Документация

### Внутренние ресурсы
- [`src/INSTRUCTIONS.md`](src/INSTRUCTIONS.md) - Детальные инструкции
- [`src/QUICK_REF.md`](src/QUICK_REF.md) - Быстрые команды
- [`src/docker/QUICK_START.md`](src/docker/QUICK_START.md) - Docker гайд

### Внешние ресурсы
- [ROS 2 Documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Simulator](http://gazebosim.org/)
- [Unitree Robots](https://www.unitree.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## � Благодарности и Credits

Этот проект стал возможен благодаря работе и вкладу следующих авторов и проектов:

### Основные источники вдохновения и кода
- **mike4192** - [SpotMicro](https://github.com/mike4192/spotMicro) - Кинематика и управление четырехногими роботами
- **Unitree Robotics** - [A1 ROS](https://github.com/unitreerobotics/a1_ros) - Официальная поддержка роботов Unitree
- **QUADRUPED ROBOTICS** - [Quadruped](https://quadruped.de) - Алгоритмы ходьбы и навигации
- **lnotspotl** - [GitHub](https://github.com/lnotspotl) - Оптимизация и улучшения симуляции
- **anujjain-dev** - [Unitree-go2 ROS2](https://github.com/anujjain-dev/unitree-go2-ros2) - Адаптация под ROS 2 Jazzy

### Использованные технологии
- **ROS 2 Jazzy** - Робототехническая middleware
- **Gazebo Sim** - Физический симулятор
- **Nav2** - Стек навигации
- **Docker** - Контейнеризация

### Особая благодарность
Сообществу разработчиков робототехники за открытые исходные коды, документацию и постоянную поддержку в развитии четырехногой робототехники.

---

## �📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

---

## 👥 Автор

- **RedAlexDad** - Основная разработка и архитектура

---

## 📞 Поддержка

### Связь
- **GitHub Issues:** [Сообщить о проблеме](https://github.com/RedAlexDad/WalkingRobotSim/issues)
- **Discussions:** [Вопросы и обсуждения](https://github.com/RedAlexDad/WalkingRobotSim/discussions)

### Быстрая помощь
```bash
# Проверить всё ли работает
./test-workflows.sh test

# Получить справку
./test-workflows.sh help
```