# Анализ проблемы: Nav2 costmap static_layer теряет карту

**Дата:** 2026-06-05 13:25 MSK
**Версия Nav2:** ros-jazzy-nav2-costmap-2d 1.3.11
**Ветка:** feat/elevation-mapping

---

## Симптом

- `make gazebo` — запускается, робот ходит
- В RViz видна карта (191×447, cafe_world)
- `make waypoint-start` — `success=True`, но робот никуда не идёт
- В логах: `Can't update static costmap layer, no map received`

---

## Хронология изменений, затронувших Nav2

### 🔵 Коммит 9c1eb44 — ПОСЛЕДНЯЯ РАБОЧАЯ ВЕРСИЯ

**Изменения:**
- `nav2_params.yaml` — добавлен `elevation_costmap_layer` в local/global costmap
- `localization_launch.py` — `root_key=namespace`, `RewrittenYaml` напрямую
- `navigation_launch.py` — `root_key=namespace`, `RewrittenYaml` напрямую
- `gazebo_multi_nav2_cpp.launch.py` — обёртка для multi-robot

**Статус:** Nav2 работал: карта загружалась, статик слой инициализировался,
планировщик строил пути.

---

### 🔴 Коммит 3954127 — ПЕРВОЕ НАРУШЕНИЕ

**Проблема:** map_server падал с `yaml_filename not initialized`

**Исправление:** `root_key=namespace` → `root_key=''` в launch-файлах

**Побочный эффект:** параметры перестали правильно заворачиваться под namespace.
Например, `local_costmap.local_costmap.ros__parameters.static_layer.map_topic`
не находился, т.к. YAML теперь не имел namespace-префикса.

**Заодно изменено:**
- Явно добавлен `map_topic: "/robot1/map"` в static_layer (YAML)
- Добавлен `Y_pose` в robots.yaml
- Раскомментирован `-Y` в спавне робота

---

### 🔴 Коммит 9ba09c3 — ВТОРОЕ НАРУШЕНИЕ

**Проблема:** попытка причесать launch-файлы под стандарт nav2_bringup

**Изменения:**
- `RewrittenYaml` обёрнут в `ParameterFile(..., allow_substs=True)`
- `root_key` оставлен как `namespace`
- `SetParameter('use_sim_time', use_sim_time)` на группе
- `yaml_filename` как отдельный параметр Node

**Побочный эффект:** static_layer перестал инициализироваться полностью.
Пропало сообщение `Using plugin "static_layer"` из логов.
Costmap создавался, но ни один плагин не конфигурировался.

---

### 🟡 Коммит 07e61ee — НЕУДАЧНАЯ ПОПЫТКА

**Проблема:** `map_subscribe_transient_local` не подставлялся в YAML

**Изменение:** добавлен `map_subscribe_transient_local` в `param_substitutions`

**Эффект:** не помогло — проблема была не в этом параметре.

---

### 🔵 Коммит faa7ec3 — ПОЛНЫЙ ОТКАТ

**Решение:** `git checkout 9c1eb44 -- src/gazebo_sim/`

**Откачены файлы:**
- `config/nav2_params.yaml` — убраны явные `map_topic`, убран `Y_pose`
- `config/robots.yaml` — убран `Y_pose`
- `launch/gazebo_multi_nav2_cpp.launch.py` — закомментирован `-Y`
- `launch/nav2/localization_launch.py` — возвращён `root_key=namespace`
- `launch/nav2/navigation_launch.py` — возвращён `root_key=namespace`

---

## Текущее состояние (после отката)

### ✅ Что работает
- map_server загружает карту (191×447, 0.05 м/пикс)
- static_layer инициализируется: сообщения `Using plugin "static_layer"`, `Subscribing to the map topic (/robot1/map) with transient local durability`, `Initialized plugin "static_layer"`
- Карта получена: `StaticLayer: Resizing static layer to 191 X 447 at 0.050000 m/pix`
- DWB critic'ы работают: RotateToGoal, Oscillation, BaseObstacle, GoalAlign, PathAlign, PathDist, GoalDist
- Робот ходит (TROT контроллер активен)
- joint_state_broadcaster и joint_group_controller загружены

### ❌ Что не работает
- После lifecycle активации (configure → activate) costmap теряет карту
- `clear_entirely` (вызывается через initial pose) окончательно сбрасывает карту
- Планировщик не может построить путь: `Costmap timed out waiting for update`

### Детальная последовательность из логов

```
[1780654697.619] Using plugin "static_layer"
[1780654697.629] Subscribing to the map topic (/robot1/map) with transient local durability
[1780654697.633] Initialized plugin "static_layer"
[1780654697.664] StaticLayer: Resizing static layer to 191 X 447 at 0.050000 m/pix  ← КАРТА ПОЛУЧЕНА
...
[1780654697.928] Activating
[1780654697.928] Checking transform
[1780654697.928] Timed out waiting for transform from base_link to odom  ← ~5 сек ожидания tf
[1780654702.428] start  ← transform готов
[1780654704.429] Can't update static costmap layer, no map received  ← КАРТА ПОТЕРЯНА
```

---

## Диагноз

**StaticLayer получает карту во время `on_configure`, но после `on_activate`**
**и subsequent `updateMap()` вызовов, карта считается отсутствующей.**

Это происходит потому, что `has_map_` флаг сбрасывается или буфер карты
очищается во время перехода lifecycle из `configured` в `active`.

Вероятные причины (версия Nav2 1.3.11):

1. **rolling_window** в local_costmap — при активации rolling_window сбрасывает
   costmap, и static_layer теряет ссылку на буфер карты
2. **clear_entirely** — вызывается через service или initial pose, сбрасывает
   `has_map_` без возможности восстановления
3. **map_subscribe_transient_local** — установлен, но subscriber после очистки
   не получает latched-сообщение от map_server повторно

Для global_costmap (у которой `rolling_window: false` и `track_unknown_space: true`)
проблема идентична — значит, rolling_window не единственная причина.

---

## Возможные решения

| # | Решение | Сложность | Надёжность |
|---|---------|-----------|-----------|
| 1 | **map_republisher** — node,每隔 5 сек перепубликует карту | Средняя | Высокая |
| 2 | **Отключить clear_entirely** — убрать вызовы из waypoint_collector | Низкая | Средняя |
| 3 | **Перейти на Nav2 Rolling** — более новая версия, где баг может быть исправлен | Высокая | Средняя |
| 4 | **Использовать map_server с keep_last** — настроить QoS на HISTORY_KEEP_LAST | Средняя | Средняя |

---

## Git log изменённых файлов Nav2

```log
faa7ec3 fix: откатить src/gazebo_sim до версии 9c1eb44
07e61ee fix: добавить map_subscribe_transient_local в navigation_launch
9ba09c3 fix: переписать launch-файлы по стандарту nav2_bringup
3954127 fix: исправить настройки multi-robot nav2 и конфигурацию elevation
9c1eb44 feat: добавить умный деплой и elevation_costmap_layer в global_costmap
126bc8a feat(costmap): добавить invert_cost для корректной интерпретации elevation costmap
```

Все последующие изменения (Dockerfile, rosdep, package-xmls) не затрагивали
файлы Nav2 и не влияли на его работу.
