# Шпаргалка по Docker

Методичка 03: Docker для ROS2

---

## Базовые команды Docker

### Образы
```bash
docker images                    # Список образов
docker rmi image_name            # Удалить образ
docker image prune               # Удалить неиспользуемые образы
```

### Контейнеры
```bash
docker ps                        # Запущенные контейнеры
docker ps -a                     # Все контейнеры
docker stop container_name       # Остановить
docker start container_name      # Запустить
docker rm container_name         # Удалить
docker logs container_name       # Логи
docker exec -it container bash   # Войти в контейнер
```

---

## Мониторинг
```bash
docker stats                     # Ресурсы контейнеров
docker inspect container_name    # Подробная информация
```

---

## Docker Compose

### Основные команды
```bash
docker compose up -d             # Запустить в фоне
docker compose down              # Остановить и удалить
docker compose logs -f           # Логи в реальном времени
docker compose restart           # Перезапуск
docker compose ps                # Статус сервисов
```

### Сборка
```bash
docker compose build             # Собрать образы
docker compose build --no-cache  # Собрать без кэша
```

### Выполнение команд
```bash
docker compose exec simulator bash    # Войти в контейнер
docker compose exec simulator ros2 node list  # Выполнить команду
```

---

## Быстрые команды для проекта

### Запуск симуляции
```bash
cd src/docker
docker compose up -d
docker compose exec simulator bash
source /opt/ros/jazzy/setup.bash
source /root/ws/install/setup.bash
```

### Остановка
```bash
docker compose down
```

### Очистка
```bash
docker compose down
docker system prune -a
docker volume prune
```

---

## Связанные документы

- [Основная методичка](README.md)
- [Тест](quiz.md)

---

*Последнее обновление: Март 2026*
