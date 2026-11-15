# Docker окружение

Контейнеризация симулятора на базе ROS 2 Jazzy. Единый образ для всех компонентов: Gazebo Sim, Nav2, контроллеры, RViz.

---

## Требования к хосту

- Docker 20.10+ с BuildKit
- Docker Compose v2 (`docker compose`, не `docker-compose`)
- Linux с X11 (для GUI симуляции, Gazebo, RViz)
- NVIDIA GPU + nvidia-container-toolkit (опционально, для ускорения)

---

## Сборка и запуск

```bash
# Сборка + запуск
make deploy

# Только сборка
make build

# Только запуск (контейнер уже собран)
make up

# Сборка без кэша (первая сборка или при проблемах с кэшем)
make deploy-no-cache
```

---

## Структура Dockerfile

Многостадийная сборка (6 этапов) с кэшированием:

| Stage | Назначение | Кэш |
|-------|------------|-----|
| `base-system` | ROS Jazzy + системные пакеты | Стабильный |
| `ros-deps` | ROS зависимости через rosdep | Редко меняется |
| `sim` | Gazebo Sim | Стабильный |
| `navigation` | Nav2 + AMCL + waypoint_follower | Стабильный |
| `python` | Python контроллер + зависимости | Часто |
| `final` | Финальный образ | Всегда |

При повторной сборке кэш первого уровня даёт 30-60 секунд вместо полной сборки.

---

## Устранение проблем с кэшем

Ошибка `cache_from` при Docker Compose v2:

```
ERROR: failed to configure registry cache importer: pull access denied
```

Решение — сборка без кэша:
```bash
make deploy-no-cache
```

В текущей версии `compose.yml` секция `cache_from` удалена, Docker использует локальный кэш.

---

## Кэш образа и восстановление после `docker purge`

Свежий образ автоматически сохраняется в `images/` (каталог в `.gitignore`,
в Docker-контекст не попадает — см. корневой `.dockerignore`):

```bash
make build          # сборка; после успеха обновит images/walking_robot_sim-latest-<arch>.tar.zst
make image-save     # сохранить образ вручную (пропустит, если образ не менялся)
make image-load     # восстановить из images/ после docker purge
make image-pull     # скачать из GitHub Packages и сохранить в images/ (следующий раз — без сети)
make image-restore  # есть архив → image-load, нет → image-pull (и кэширование в images/)
```

`make image-pull` после скачивания сразу вызывает `image-save`, поэтому повторно
качать из GHCR не придётся: достаточно `make image-load`/`make image-restore`.
Автосохранение можно отключить: `make build SAVE_IMAGE=0`.
Публикация в GHCR — workflow `.github/workflows/docker-image.yml`.

---

## Основные команды

```bash
# Вход в контейнер
make shell

# Логи
make logs

# Остановка
make down

# Полный сброс (очистить контейнер полностью)
make clean     # docker system prune -af + удаление образов
```

---

## X11 и GUI

Для работы Gazebo и RViz требуется X11:

```bash
# Автоматически настраивается в make up
xhost +local:root

# Если нет DISPLAY
export DISPLAY=:0
```

---

## Файлы конфигурации

- `Dockerfile` — многостадийная сборка образа
- `compose.yml` — сервис simulator + монтирование томов
- `.env` — переменные окружения (USER_ID, GROUP_ID, и т.д.)
- `dockerignore` — исключения для контекста сборки
- `.colconignore` — игнорирование директорий colcon

---

## Разработка внутри контейнера

Все исходники монтируются через volumes, редактировать можно на хосте:

```
~/GitHub/WalkingRobotSim/  →  /workspace/src/
```

После изменений внутри контейнера:
```bash
colcon build --symlink-install
source install/setup.bash
```

---

## Зависимости хоста

Для GPU ускорения (опционально):
- [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

Для X11 (обязательно):
- x11-utils, xauth

---

## Ссылки

- [compose.yml](compose.yml) — конфигурация сервиса
- [Dockerfile](Dockerfile) — многостадийная сборка
