# Отчет о проблемах и исправлениях

## 1. Проблема: costmap не получает карту (StaticLayer)

### Симптом
map_server загружает карту, но StaticLayer в costmap не получает её.
Costmap отображается размером 200×200 @ 0.1м (дефолт), а не размером загруженной карты.

### Коренная причина
В `localization_launch.py` и `navigation_launch.py` используется:
```python
configured_params = RewrittenYaml(
    source_file=params_file,
    root_key=namespace,    # "robot1"
    ...
)
```

Когда `namespace="robot1"`, `RewrittenYaml` оборачивает весь YAML под
ключ `robot1`, т.к. в `nav2_params.yaml` нет такого ключа верхнего
уровня. В результате все узлы nav2 получают YAML вида:
```yaml
robot1:
  local_costmap:
    local_costmap:
      ros__parameters:
        static_layer:
          map_topic: "/robot1/map"
          ...
```

Узлы (controller_server, planner_server, ...) не находят свои
параметры на корневом уровне и используют значения по умолчанию:
- `map_topic: "/map"` (а не `/robot1/map`)
- `resolution: 0.1` (а не 0.05)

StaticLayer подписывается на абсолютный топик `/map`, а map_server
публикует на `/robot1/map` (из-за `PushRosNamespace`). **MISMATCH**.

### Исправление
**`localization_launch.py`**: `root_key=namespace` → `root_key=""`,
добавлен `ParameterFile`, `yaml_filename` как отдельный параметр.

**`navigation_launch.py`**: `root_key=namespace` → `root_key=""`,
добавлен `ParameterFile`.

---

## 2. Проблема: скрученные суставы в симуляции

### Симптом
Визуальные суставы выглядят "повёрнутыми" — ноги скручены.

### Предполагаемая причина
Файлы `.dae` имеют внутренний поворот модели на +90° по оси X.
В URDF visual элементы не имеют `rpy`, collision имеют
`rpy="1.570796 0 0"`. Значения `joints[0-2]: -0.0000 0.8615 -1.8826`
(thigh=+0.86 rad, calf=-1.88 rad) указывают на:
- Неправильную интерпретацию joint_states из Gazebo
- Или отсутствие компенсации поворота mesh в visual origin

### Статус
Требуется диагностика внутри контейнера:
- Проверить joint_state_broadcaster и актуальные joint_states
- Сравнить с URDF лимитами суставов

---

## 3. Дополнительные замечания

### `navigation_launch.py`
- `params_file` default_value указывает на несуществующий путь
  `"params/nav2_params.yaml"` (должен быть `"config/"`)
- `map_subscribe_transient_local` передаётся из bringup, но
  не объявлен и не используется

### `bringup_launch.py`
- `slam_launch.py` не существует
- `map_server` аргумент от родительского launch не пробрасывается

### `gazebo_multi_nav2_cpp.launch.py`
- Есть дублирующий закомментированный `map_server`
  с `cambridge.yaml` (строки 83-109)
