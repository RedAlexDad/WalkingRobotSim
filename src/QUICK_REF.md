# 🎯 QUICK REFERENCE - Шпаргалка

## ⚡ ПЕРВЫЙ ЗАПУСК

```bash
cd ~/GitHub/WalkingRobotSim/src

# 1. Обновить compose.yml (исправить ошибку)
cp compose_fixed.yml docker/compose.yml

# 2. Дать права
chmod +x manage.sh setup.sh

# 3. Setup
bash setup.sh

# 4. Собрать (15-30 мин)
./manage.sh build

# 5. Запустить
./manage.sh up

# 6. Проверить
./manage.sh status
```

---

## 📋 ГЛАВНЫЕ КОМАНДЫ

| Команда | Что делает | Когда использовать |
|---------|-----------|-------------------|
| `./manage.sh up` | Запустить контейнер | Первый запуск дня |
| `./manage.sh down` | Остановить полностью | Конец работы |
| `./manage.sh shell` | Bash в контейнере | Работать внутри |
| `./manage.sh logs` | Смотреть логи | Отладка проблем |
| `./manage.sh status` | Проверить статус | Убедиться, что работает |
| `./manage.sh rebuild` | Пересобрать образ | После изменения кода |
| `./manage.sh stats` | CPU/Memory | Мониторить ресурсы |

---

## 🔥 ТИПИЧНЫЕ СЦЕНАРИИ

### Сценарий 1: Утро - начало работы
```bash
./manage.sh up
./manage.sh status
./manage.sh logs
# Смотрим, запустилось ли...
```

### Сценарий 2: Изменил код - нужна пересборка
```bash
# Отредактировали src/gazebo_sim/src/*.py

./manage.sh rebuild
# Ждем 30-60 сек

./manage.sh shell
ros2 launch gazebo_sim launch.py
```

### Сценарий 3: Что-то не работает
```bash
# Смотрим логи
./manage.sh logs | grep ERROR

# Проверяем ресурсы
./manage.sh stats

# Перезапускаем
./manage.sh restart

# Проверяем детали
./manage.sh inspect
```

### Сценарий 4: Конец дня - остановка
```bash
./manage.sh pull-logs     # Сохранить логи
./manage.sh down          # Остановить
./manage.sh clean         # Очистить ненужное
```

---

## 🐛 БЫСТРОЕ РЕШЕНИЕ ПРОБЛЕМ

| Проблема | Решение | Команда |
|----------|---------|---------|
| Контейнер не запускается | Пересобрать | `./manage.sh rebuild` |
| Health check failing | Перезапустить | `./manage.sh restart` |
| Нет доступа к GUI (X11) | Дать доступ | `xhost +local:root` |
| Медленная сборка | Очистить кэш | `docker builder prune -a` |
| Контейнер ест много памяти | Проверить | `./manage.sh stats` |
| Логи не видны | Смотреть файл | `./manage.sh pull-logs` |

---

## 📊 ИНФОРМАЦИОННЫЕ КОМАНДЫ

```bash
# Статус контейнера
./manage.sh ps
./manage.sh status
./manage.sh inspect

# Логи и мониторинг
./manage.sh logs          # Live logs (Ctrl+C выход)
./manage.sh stats         # CPU/Memory (Ctrl+C выход)
./manage.sh pull-logs     # Сохранить в файл

# Справка
./manage.sh --help
```

---

## 🔧 УПРАВЛЯЮЩИЕ КОМАНДЫ

```bash
# Старт/стоп
./manage.sh up            # Запустить
./manage.sh start         # Запустить (если уже был)
./manage.sh stop          # Остановить (не удалять)
./manage.sh restart       # Перезапустить
./manage.sh down          # Остановить и удалить

# Сборка
./manage.sh build         # Собрать (с кэшем)
./manage.sh rebuild       # Собрать без кэша

# Очистка
./manage.sh clean         # Удалить старые образы/volumes
```

---

## 🐚 ВНУТРИ КОНТЕЙНЕРА

```bash
# Вход
./manage.sh shell

# Внутри (bash):
source /opt/ros/jazzy/setup.bash
source /root/ws/install/setup.bash

# ROS команды
ros2 node list
ros2 topic list
ros2 service list

# Запуск симуляции
ros2 launch gazebo_sim launch.py use_sim_time:=true

# Выход
exit
```

---

## 💾 ФАЙЛЫ ДЛЯ КОПИРОВАНИЯ

Эти 4 файла нужно скопировать в ваш проект:

```bash
# В docker/:
docker/compose.yml      ← Исправленный (restart вместо restart_policy)
docker/Dockerfile       ← 6-stage оптимизированный

# В корень:
./manage.sh             ← Управляющий скрипт
./.dockerignore         ← Исключить файлы из build
```

---

## ⚙️ ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ

### Включить BuildKit для еще большего ускорения

```bash
export DOCKER_BUILDKIT=1
./manage.sh build
```

### Изменить лимиты ресурсов

```bash
# В docker/compose.yml найти:
# deploy:
#   resources:
#     limits:
#       cpus: "4"        ← Измените тут
#       memory: 8G       ← И тут
```

### Добавить свои переменные окружения

```bash
# В .env (будет создан setup.sh):
ROBOT_TYPE=Go2
ROS_DISTRO=jazzy
```

### Изменить порты или volumes

```bash
# В docker/compose.yml секция "volumes" и "ports"
# Перезапустить после изменения:
./manage.sh restart
```

---

## 📈 PERFORMANCE

### Первый build: 15-30 минут
```
Stage 1-3: Устанавливают базу (долго)
Stage 4:   Собирают ваш код
Stage 5-6: Создают финальный образ
```

### Следующие builds: 30-60 секунд
```
Stage 1-3: ✓ CACHED (0 сек)
Stage 4:   Собирается (30 сек)
Stage 5-6: ✓ CACHED (0 сек)
```

### Измените только код: 30-60 сек
```
./manage.sh rebuild
# Только Stage 4 пересобирается!
```

---

## ✅ ЧЕКЛИСТ

- [ ] Скопировал compose_fixed.yml → docker/compose.yml
- [ ] Скопировал manage.sh, setup.sh, .dockerignore
- [ ] Дал права: `chmod +x manage.sh setup.sh`
- [ ] Запустил setup.sh
- [ ] Собрал образ: `./manage.sh build`
- [ ] Запустил: `./manage.sh up`
- [ ] Проверил статус: `./manage.sh status` (должно быть HEALTHY)
- [ ] Готово! 🎉

---

## 🆘 HELP

```bash
# Справка по скрипту
./manage.sh --help

# Ошибка в конфигурации? Проверить:
docker compose -f docker/compose.yml config

# Посмотреть размер образа:
docker images | grep walking_robot_sim

# Сохранить логи перед удалением:
./manage.sh pull-logs

# Полная очистка (ОСТОРОЖНО!):
docker system prune -a -f
```

---

**Все готово! Начните с `./manage.sh up` 🚀**
