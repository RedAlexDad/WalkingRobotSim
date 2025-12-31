# 🚀 Быстрый старт Walking Robot Simulation

## ⚡ 5 минут до запуска симуляции

### 1. Сборка и запуск
```bash
./manage.sh build && ./manage.sh up
```

### 2. Запуск симуляции
```bash
./manage.sh gazebo
```

### 3. Управление роботом
```bash
./manage.sh teleop
```

---

## 🤖 Работа внутри контейнера

### Вход в контейнер
```bash
./manage.sh shell
```

### Запуск симуляции в контейнере
```bash
sim          # Алиас для запуска Gazebo
teleop       # Алиас для управления
topics       # Список топиков
nodes        # Список узлов
```

---

## 🔧 Основные команды

| Команда | Описание |
|---------|----------|
| `./manage.sh build` | Сборка образа |
| `./manage.sh up` | Запуск контейнера |
| `./manage.sh down` | Остановка контейнера |
| `./manage.sh gazebo` | Запуск симуляции |
| `./manage.sh teleop` | Управление роботом |
| `./manage.sh shell` | Вход в контейнер |
| `./manage.sh status` | Статус контейнера |

---

## 🚨 Если что-то не работает

### Симуляция не запускается
```bash
./manage.sh down && ./manage.sh up && ./manage.sh gazebo
```

### ROS команды не работают
```bash
./manage.sh exec "ros2 topic list"
```

### Полная переустановка
```bash
./manage.sh clean && ./manage.sh build && ./manage.sh up
```

---

## 📚 Подробная документация

Смотрите полный `README.md` для детальной информации.
