# План рефакторинга Dockerfile

**Дата:** 2026-06-05 10:07 MSK
**Файл:** `src/docker/Dockerfile` (234 строки, 10 этапов)
**Цель:** убрать баги, уменьшить размер образа, ускорить сборку, повысить надёжность

---

## Баги (🔴 High)

### 1. Healthcheck — CMD синтаксис

**Файл:** строка 230
**Проблема:** `|| exit 1` находится снаружи кавычек CMD, поэтому healthcheck
всегда завершается успешно (0), независимо от результата `ros2 node list`.

```dockerfile
# Текущий (не работает):
CMD bash -c 'source ... && ros2 node list' || exit 1

# Должно быть:
CMD bash -c 'source ... && ros2 node list || exit 1'
```

**Эффект:** при падении ROS контейнер не перезапускается, оркестратор
не видит проблему.
**Сложность:** 1/5 (одна строка)
**Приоритет:** 🔴 сделать сейчас

### 2. GAZEBO_RESOURCE_PATH — неверная версия

**Файл:** строка 222
**Проблема:** Jazzy поставляется с Gazebo Harmonic (gz-8), а указан
`gazebo-11` (Ignition Gazebo из более старых ROS).

```dockerfile
# Текущий:
GAZEBO_RESOURCE_PATH=/usr/share/gazebo-11

# Должно быть для Harmonic:
GAZEBO_RESOURCE_PATH=/usr/share/gz/gazebo-8
```

**Эффект:** переменная бесполезна, ресурсы Gazebo (миры, модели)
могут не находиться.
**Сложность:** 1/5
**Приоритет:** 🔴 сделать сейчас

---

## Оптимизация размера (🟡 Medium)

### 3. Замена ros-desktop на ros-base

**Файл:** строка 39 (этап 2, ros-core)
**Проблема:** `ros-jazzy-desktop` — это мета-пакет, который тянет ~700 МБ
зависимостей: RViz, rqt, визуализаторы, rttest, примеры и т.д.
Большая часть не нужна в контейнере для симуляции.

```dockerfile
# Текущий:
ros-${ROS_DISTRO}-desktop

# Предлагается:
ros-${ROS_DISTRO}-ros-base
```

Отдельно доставить только то, что реально используется:
- `ros-${ROS_DISTRO}-rviz2` — если нужен RViz в контейнере
- `ros-${ROS_DISTRO}-rqt-gui` — если нужен rqt

**Эффект:** ~500-700 МБ экономии на финальном образе
**Сложность:** 2/5 (проверить, не сломается ли сборка других пакетов)
**Приоритет:** 🟡 после багов

### 4. Удалить повторную установку tmux

**Файл:** строки 20 и 154
**Проблема:** `tmux` устанавливается дважды — в base-system и ros-tools

```dockerfile
# Удалить из ros-tools (строка 154):
tmux
```

**Эффект:** лишняя операция в CI, хотя apt/cache её кэширует
**Сложность:** 1/5
**Приоритет:** 🟡 сделать сейчас

### 5. Параметризация GPU/CPU для torch

**Файл:** строки 176-180 (этап 8, python-deps)
**Проблема:** torch всегда ставится CPU-only. Если у хоста есть NVIDIA GPU,
пользователь не может переключиться на CUDA без правки Dockerfile.

```dockerfile
# Текущий (жёстко CPU):
pip3 install torch --index-url https://download.pytorch.org/whl/cpu

# Предлагается:
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip3 install torch --index-url ${TORCH_INDEX_URL} \
    && pip3 install ultralytics --no-deps \
    && pip3 install opencv-python-headless \
    && pip3 install 'numpy<2'
```

Сборка с GPU:
```bash
make build TORCH_INDEX_URL=https://download.pytorch.org/whl/cu124
```

**Эффект:** гибкость выбора CPU/GPU без дублирования Dockerfile
**Сложность:** 2/5
**Приоритет:** 🟡 после багов

### 6. Убрать uninstall opencv-python

**Файл:** строки 178-180
**Проблема:** ultralytics тянет opencv-python, потом он удаляется,
потом снова фиксируется numpy. Три лишних pip-операции.

```dockerfile
# Текущий:
pip3 install ... ultralytics \
    && pip3 uninstall -y opencv-python \
    && pip3 install 'numpy<2'

# Предлагается:
pip3 install ultralytics --no-deps
pip3 install opencv-python-headless 'numpy<2'
```

**Эффект:** минус 2 pip-операции, прозрачнее
**Сложность:** 1/5
**Приоритет:** 🟡 сделать сейчас

---

## Ускорение сборки (🟡 Medium)

### 7. Дублирование apt-get update

**Файл:** этапы 1-7
**Проблема:** каждый этап запускает `apt-get update`, хотя apt-кэш
уже прогрет через `--mount=type=cache,target=/var/lib/apt`.

При использовании BuildKit кэш `/var/lib/apt` сохраняется между
этапами, поэтому повторный `apt-get update` в дочерних этапах
избыточен — список пакетов уже актуален.

```dockerfile
# Можно убрать apt-get update во всех этапах, кроме base-system
RUN apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-navigation2 \
    && rm -rf /var/lib/apt/lists/*
```

**Эффект:** минус ~3-5 секунд на каждом этапе сборки
**Сложность:** 2/5 (нужно проверить, что кэш действительно маунтится)
**Приоритет:** 🟡 опционально

### 8. colcon cache lock — fallback

**Файл:** строка 194
**Проблема:** `colcon cache lock` — команда плагина `ruffsl/colcon-cache`.
Если плагин не установится (ошибка сети, версия), вся сборка упадёт.

```dockerfile
# Текущий:
RUN colcon cache lock && colcon build --symlink-install --mixin ccache

# Предлагается:
RUN colcon cache lock 2>/dev/null; colcon build --symlink-install --mixin ccache
```

**Эффект:** сборка не падает при ошибке плагина
**Сложность:** 1/5
**Приоритет:** 🟡 сделать сейчас

---

## Улучшение архитектуры (🟢 Low)

### 9. Вынести ARG ROS_DISTRO в глобальную область

**Файл:** повторяется в 8 этапах (строки 7, 32, 57, 79, 96, 113, 136, 201)
**Проблема:** копипаста. ARG, объявленный перед первым FROM, доступен
во всех этапах до первого переопределения.

```dockerfile
# Глобальный ARG (один раз, перед первым FROM):
ARG ROS_DISTRO=jazzy

# Во всех дочерних этапах ARG не нужен — кроме финального, если он
# используется после FROM:
FROM workspace AS final
ARG ROS_DISTRO  # только если используется в этом этапе
```

**Эффект:** минус 7 строк, единая точка изменения версии ROS
**Сложность:** 1/5
**Приоритет:** 🟢 когда будет время

### 10. Проверить необходимость GAZEBO_MASTER_URI и GAZEBO_RESOURCE_PATH

**Файл:** строки 224-225
**Проблема:** эти переменные специфичны для Gazebo Classic.
Harmonic их не использует — там своя система топиков.

```dockerfile
# Для Gazebo Harmonic эти переменные не нужны:
# ENV GAZEBO_MASTER_URI=http://localhost:11345
# ENV GAZEBO_RESOURCE_PATH=/usr/share/gz/gazebo-8
```

Оставить только если есть обратная совместимость с классическим Gazebo.
**Эффект:** чистота окружения
**Сложность:** 1/5 (нужно проверить launch-файлы)
**Приоритет:** 🟢 проверить при тестировании

---

## Итоговая roadmap

| # | Задача | Приоритет | Сложность | Влияние |
|---|--------|-----------|-----------|---------|
| 1 | Healthcheck `|| exit 1` | 🔴 | 1/5 | Баг |
| 2 | GAZEBO_RESOURCE_PATH=gz-8 | 🔴 | 1/5 | Баг |
| 4 | Удалить дубликат tmux | 🟡 | 1/5 | Порядок |
| 6 | Убрать uninstall opencv | 🟡 | 1/5 | Скорость |
| 8 | colcon cache lock fallback | 🟡 | 1/5 | Надёжность |
| 3 | ros-desktop → ros-base | 🟡 | 2/5 | -700 МБ |
| 5 | Параметризация torch | 🟡 | 2/5 | Гибкость |
| 7 | Убрать лишние apt update | 🟡 | 2/5 | Скорость |
| 9 | ARG ROS_DISTRO глобально | 🟢 | 1/5 | Чистота |
| 10 | GAZEBO_* vars проверка | 🟢 | 1/5 | Чистота |
