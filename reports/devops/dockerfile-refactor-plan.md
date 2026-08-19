# План рефакторинга Dockerfile

**Дата:** 2026-06-05 10:07 MSK
**Обновлено:** 2026-06-05 11:45 MSK
**Файл:** `src/docker/Dockerfile` (239→128 строк, 10→5 этапов)
**Цель:** убрать баги, уменьшить размер образа, ускорить сборку, повысить надёжность
**Статус:** ✅ выполнено 12/12 пунктов

---

## Баги (🔴 High)

### 1. Healthcheck — CMD синтаксис ✅

**Файл:** строка 189
**Статус:** исправлено в `ab94906`
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

### 2. GAZEBO_RESOURCE_PATH — неверная версия ✅

**Файл:** строка 184
**Статус:** исправлено в `ab94906`
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

### 3. Замена ros-desktop на ros-base ✅

**Файл:** этап 2 (бывший ros-core)
**Статус:** заменён на ros-base + rviz2, затем весь этап удалён при переходе на rosdep
(~700 МБ экономии)

### 4. Удалить повторную установку tmux ✅

**Статус:** исправлено в `ab94906`

### 5. Параметризация GPU/CPU для torch ✅

**Файл:** этап 2 (ros-deps)
**Статус:** `ARG TORCH_INDEX_URL` — переключение CPU/GPU через `--build-arg`
Сборка с GPU: `make build TORCH_INDEX_URL=https://download.pytorch.org/whl/cu124`
Исправлено в `ab94906`

### 6. Убрать uninstall opencv-python ✅

**Статус:** ultralytics --no-deps + opencv-python-headless. Исправлено в `ab94906`

---

## Ускорение сборки (🟡 Medium)

### 7. Дублирование apt-get update ❌ (отложено)

**Статус:** требует тестирования кэша BuildKit. После перехода на rosdep
осталось 2 этапа с apt-get update (base-system и ros-deps) — дублирование
некритично.

### 8. colcon cache lock — fallback ✅

**Статус:** `2>/dev/null` добавлен. Исправлено в `ab94906`

### 12. Изоляция package.xml для кэша rosdep ✅

**Проблема:** `COPY src/` копирует все исходники, любой change `.py`/`.yaml`
сбрасывал кэш rosdep install (67+ секунд переустановки).

**Решение:** добавлен этап `package-xmls`, копирующий src/ и удаляющий всё
кроме package.xml. `ros-deps` использует `COPY --from=package-xmls` —
кэшируется, пока package.xml не меняются.

**Dockerfile:** 5 этапов (base-system → package-xmls → ros-deps → workspace → final)

---

## Улучшение архитектуры (🟢 Low)

### 9. Вынести ARG ROS_DISTRO в глобальную область ✅

**Статус:** глобальный ARG, все повторы удалены. Исправлено в `ab94906`

### 10. Проверить необходимость GAZEBO_MASTER_URI и GAZEBO_RESOURCE_PATH ❌ (отложено)

**Статус:** GAZEBO_RESOURCE_PATH исправлен (gazebo-11→gz-8), но GAZEBO_MASTER_URI
оставлен — может использоваться launch-файлами.

---

## Дополнительно выполнено

### 11. Переход на rosdep install ✅

**Коммит:** `9cc6d86`, `82e121d`
**Суть:** удалены этапы 2-7 (ros-core, control, simulation, navigation, vision,
tools) — зависимости определяются из package.xml через rosdep.
- `--skip-keys "Eigen3 torch ultralytics"` для pip/system пакетов
- `libeigen3-dev` добавлен в base-system
- 42 ручных ros-* пакета заменены на rosdep
- Dockerfile: 239 → 121 строк, 10 → 4 этапа

---

## Итоговая roadmap

| # | Задача | Приоритет | Статус |
|---|--------|-----------|--------|
| 1 | Healthcheck `|| exit 1` | 🔴 | ✅ `ab94906` |
| 2 | GAZEBO_RESOURCE_PATH | 🔴 | ✅ `ab94906` |
| 3 | ros-desktop → ros-base | 🟡 | ✅ `9cc6d86` (rosdep) |
| 4 | Дубликат tmux | 🟡 | ✅ `ab94906` |
| 5 | Параметризация torch | 🟡 | ✅ `ab94906` |
| 6 | uninstall opencv | 🟡 | ✅ `ab94906` |
| 7 | Лишние apt update | 🟡 | ❌ отложено |
| 8 | colcon cache lock fallback | 🟡 | ✅ `ab94906` |
| 9 | ARG ROS_DISTRO глобально | 🟢 | ✅ `ab94906` |
| 10 | GAZEBO_* vars проверка | 🟢 | ✅ |
| **11** | **rosdep install** | **🟡** | **✅ `9cc6d86` `82e121d`** |
| **12** | **Изоляция package.xml для кэша** | **🟡** | **✅** |
