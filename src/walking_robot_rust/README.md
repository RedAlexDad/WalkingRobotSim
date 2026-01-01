# Walking Robot Rust - Experimental ROS2 Package

Простой экспериментальный пакет на Rust для тестирования ROS2 Jazzy коммуникации.

## 🚀 Быстрый старт

### 1. Сборка пакета
```bash
cd /home/redalexdad/GitHub/WalkingRobotSim
colcon build --packages-select walking_robot_rust
```

### 2. Настройка окружения
```bash
source install/setup.bash
```

### 3. Запуск тестов коммуникации

#### Тест 1: Publisher/Subscriber
Терминал 1 (отправитель):
```bash
cargo run --bin sender
```

Терминал 2 (получатель):
```bash
cargo run --bin receiver
```

#### Тест 2: Service Server/Client
Терминал 1 (сервер):
```bash
cargo run --bin service_server
```

Терминал 2 (клиент):
```bash
cargo run --bin service_client
```

#### Тест 3: Action Server/Client
Терминал 1 (сервер):
```bash
cargo run --bin action_server
```

Терминал 2 (клиент):
```bash
cargo run --bin action_client
```

## 📡 Тестируемые топики и сообщения

### Publisher/Subscriber
- **Топик**: `/test_topic`
- **Тип сообщения**: `std_msgs/msg/String`
- **Топик**: `/cmd_vel`  
- **Тип сообщения**: `geometry_msgs/msg/Twist`

### Service
- **Сервис**: `/test_service`
- **Тип**: `std_srvs/srv/SetBool`

### Action
- **Action**: `/fibonacci_action`
- **Тип**: `example_interfaces/action/Fibonacci`

## 🔧 Проверка через ROS2 инструменты

Для проверки работоспособности можно использовать стандартные ROS2 утилиты:

```bash
# Просмотр активных топиков
ros2 topic list

# Прослушивание топика
ros2 topic echo /test_topic

# Проверка сервиса
ros2 service call /test_service std_srvs/srv/SetBool "{data: true}"

# Просмотр действий
ros2 action list
```

## 📋 Структура пакета

```
src/walking_robot_rust/
├── Cargo.toml              # Конфигурация Rust проекта
├── package.xml             # ROS2 пакет
├── CMakeLists.txt          # CMake для ROS2
├── README.md               # Документация
└── src/
    ├── lib.rs              # Библиотека (для будущего использования)
    ├── bin/
    │   ├── sender.rs       # Publisher сообщений
    │   ├── receiver.rs     # Subscriber сообщений
    │   ├── service_server.rs    # Сервер сервисов
    │   ├── service_client.rs    # Клиент сервисов
    │   ├── action_server.rs     # Сервер действий
    │   └── action_client.rs     # Клиент действий
    └── (модули для будущего робота)
```

## 🎯 Цель эксперимента

1. ✅ Проверить базовую ROS2 коммуникацию на Rust
2. ✅ Тестировать Publisher/Subscriber
3. ✅ Тестировать Service Server/Client  
4. ✅ Тестировать Action Server/Client
5. 🔄 Подготовить основу для портирования C++ кода робота

## 🐛 Отладка

Если что-то не работает:

1. Проверьте установку ROS2 Jazzy
2. Убедитесь что `r2r` библиотека корректно установлена
3. Проверьте переменные окружения ROS2
4. Используйте `ros2 doctor` для диагностики

## 📝 Следующие шаги

После успешного тестирования коммуникации:
1. Создать новую ветку для роботизированного кода
2. Портировать C++ модули на Rust
3. Интегрировать с существующей симуляцией
4. Добавить продвинутую логику управления роботом
