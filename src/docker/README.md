# Walking Robot Simulation Manager

## 📋 Обзор

Простая и надежная Docker конфигурация для запуска симуляции Walking Robot с использованием ROS 2 Jazzy и Gazebo Harmonic.

## 🎯 Технологии

- **🤖 ROS 2 Jazzy** - Последняя LTS версия ROS
- **🌍 Gazebo Harmonic** - Современный симулятор роботов
- **🐳 Docker + Docker Compose** - Контейнеризация и оркестрация
- **📦 Простая архитектура** - Одностадийный Dockerfile для надежности

## 🚀 Быстрый старт

### 1. Сборка и запуск
```bash
./manage.sh build    # Сборка Docker образа
./manage.sh up        # Запуск контейнера
```

### 2. Запуск симуляции
```bash
./manage.sh gazebo    # Запуск Gazebo с роботом
./manage.sh teleop    # Управление роботом
```

### 3. Работа с контейнером
```bash
./manage.sh shell     # Вход в контейнер с настроенным ROS
./manage.sh exec "ros2 topic list"  # Выполнение ROS команд
```

## 📁 Структура файлов

```
docker/
├── Dockerfile              # Основной Dockerfile (ROS Jazzy)
├── compose.yml             # Docker Compose конфигурация
├── manage.sh               # Менеджер управления
├── README.md               # Этот файл
├── Dockerfile.multistage   # Старый многостадийный (архив)
├── compose.multistage.yml  # Старый многостадийный (архив)
└── manage.multistage.sh    # Старый менеджер (архив)
```

## 🛠️ Основные команды

### Управление контейнером
```bash
./manage.sh build       # Сборка Docker образа
./manage.sh up          # Запуск контейнера
./manage.sh down        # Остановка контейнера
./manage.sh restart     # Перезапуск контейнера
./manage.sh status      # Статус контейнера
./manage.sh clean       # Полная очистка Docker
```

### Работа с симуляцией
```bash
./manage.sh gazebo      # Запуск Gazebo симуляции
./manage.sh teleop      # Управление роботом
./manage.sh logs        # Просмотр логов
./manage.sh logs-save   # Сохранение логов в файл
```

### Работа с контейнером
```bash
./manage.sh shell       # Вход в shell (с настроенным ROS)
./manage.sh exec "cmd"  # Выполнение команды в контейнере
./manage.sh backup      # Создание бэкапа данных
```

## 🤖 Работа внутри контейнера

### Автоматически настроенные алиасы
При входе в контейнер (`./manage.sh shell`) доступны следующие алиасы:

```bash
sim          # Запуск Gazebo симуляции
teleop       # Управление роботом
topics       # Список ROS топиков
nodes        # Список ROS узлов
help         # Справка по командам
```

### Полные команды (если алиасы не работают)
```bash
ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
ros2 topic list
ros2 node list
```

### Автоматическая настройка окружения
При входе в контейнер автоматически выполняется:
- `source /opt/ros/jazzy/setup.bash` - Настройка ROS Jazzy
- `source /root/ws/install/setup.bash` - Настройка workspace
- Настройка удобного prompt с индикатором `(ROS Jazzy)`

## 📊 Мониторинг и отладка

### Проверка статуса
```bash
./manage.sh status      # Статус контейнера и ресурсы
./manage.sh logs        # Логи в реальном времени
./manage.sh logs-save   # Сохранение логов в файл
```

### Диагностика
```bash
./manage.sh exec "ros2 node list"           # Список активных узлов
./manage.sh exec "ros2 topic list"           # Список топиков
./manage.sh exec "ros2 doctor"               # Диагностика ROS
./manage.sh exec "ros2 run gazebo_sim gazebo_sim --help"  # Помощь по пакету
```

## 🔧 Конфигурация

### Dockerfile особенности
- **Одностадийная архитектура** - простота и надежность
- **Кэширование apt-get** - ускорение пересборки
- **Health check** - автоматическая проверка работоспособности
- **Метаданные** - информация о версии и описании

### Compose.yml особенности
- **network_mode: host** - прямая сетевая коммуникация
- **Volumes** - разделение логов и данных
- **Health check** - мониторинг состояния контейнера
- **Restart policy** - автоматический перезапуск

### Переменные окружения
- `ROS_DISTRO=jazzy` - Версия ROS
- `WORKSPACE_DIR=/root/ws` - Рабочая директория
- `ROS_LOG_DIR=/root/ws/logs` - Директория логов
- `GAZEBO_RESOURCE_PATH` - Пути к ресурсам Gazebo
- `GZ_SIM_RESOURCE_PATH` - Пути к моделям

## 🚨 Устранение неисправностей

### Проблема: Контейнер не запускается
```bash
# Проверка Docker
docker --version
docker-compose --version

# Очистка и пересборка
./manage.sh clean
./manage.sh build
./manage.sh up
```

### Проблема: ROS команды не работают
```bash
# Проверка настройки ROS
./manage.sh exec "echo $ROS_DISTRO"
./manage.sh exec "which ros2"

# Проверка workspace
./manage.sh exec "ls -la /root/ws/install"
./manage.sh exec "source /root/ws/install/setup.bash && ros2 node list"
```

### Проблема: Симуляция не запускается
```bash
# Проверка launch файлов
./manage.sh exec "find /root/ws/install -name '*.launch.py'"

# Запуск с отладкой
./manage.sh exec "ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true --verbose"
```

### Проблема: Алиасы не работают
```bash
# Используйте полные команды
./manage.sh exec "ros2 launch gazebo_sim launch.py use_sim_time:=true gui:=true"

# Или войдите в контейнер
./manage.sh shell
# И используйте алиасы там
```

## 📦 Резервное копирование

### Создание бэкапа
```bash
./manage.sh backup      # Автоматическое создание бэкапа
```

### Ручное резервирование
```bash
# Экспорт контейнера
docker export walking_robot_sim > walking_robot_backup.tar

# Копирование данных
docker cp walking_robot_sim:/root/ws/logs ./logs_backup/
```

## 🔄 Обновление и обслуживание

### Обновление образов
```bash
# Полная пересборка без кэша
docker compose build --no-cache

# Обновление пакетов в контейнере
./manage.sh exec "apt update && apt upgrade -y"
```

### Очистка системы
```bash
# Очистка Docker
./manage.sh clean

# Очистка неиспользуемых ресурсов
docker system prune -a
docker volume prune
```

## 📈 Производительность

### Оптимизация сборки
- Используйте кэширование apt-get
- Переиспользуйте слои Docker
- Используйте `cache_from` в compose.yml

### Мониторинг ресурсов
```bash
# Использование ресурсов
./manage.sh status

# Детальная статистика
docker stats walking_robot_sim
```

## 🤝 Поддержка

### Полезные ресурсы
- [ROS 2 Jazzy Documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Harmonic Documentation](https://gazebosim.org/docs/harmonic/)
- [Docker Documentation](https://docs.docker.com/)

### Сообщество
- GitHub Issues: [WalkingRobotSim](https://github.com/RedAlexDad/WalkingRobotSim/issues)
- ROS Discourse: [https://discourse.ros.org/](https://discourse.ros.org/)

## 📝 История изменений

### v3.0 - Текущая версия
- ✅ Переход на простую архитектуру
- ✅ Поддержка только ROS Jazzy + Gazebo Harmonic
- ✅ Автоматическая настройка ROS в контейнере
- ✅ Удобные алиасы для запуска симуляции
- ✅ Улучшенный менеджер управления

### Предыдущие версии
- v2.x - Многостадийная архитектура (сохранена в архивных файлах)
- v1.x - Базовая конфигурация

## 🎯 Лучшие практики

1. **Всегда используйте `./manage.sh`** для управления контейнером
2. **Проверяйте статус** перед запуском симуляции
3. **Используйте алиасы** для быстрой работы
4. **Создавайте бэкапы** перед важными изменениями
5. **Следите за ресурсами** при длительной работе

---

**Разработано для Walking Robot Simulation**  
**Технологический стек: ROS 2 Jazzy + Gazebo Harmonic + Docker**  
**Версия: 3.0**  
**Последнее обновление: 2026-01-01**
