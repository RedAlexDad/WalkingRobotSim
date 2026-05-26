# Elevation Cost → Nav2 Costmap: Bridge Integration

## Goal
Интегрировать слой стоимости (`cost`) из elevation mapping в Nav2 costmap через bridge-ноду.

## Constraints & Preferences
- Bridge-нода — минимальный ROS2 Python узел: подписка на GridMap, извлечение слоя `cost`, публикация `nav_msgs/OccupancyGrid`.
- Топик bridge-ноды добавляется через `nav2_costmap_2d::StaticLayer` в `nav2_params.yaml` для глобальной и локальной costmap.
- Не ломать существующую функциональность.
- Bridge-node подход выбран вместо `grid_map_costmap_2d` плагина или модификации traversability.

## Progress

### Done
- Созданы плагины `surface_gradient.py`, `roughness.py`, `cost_function.py`; обновлены `plugin_config.yaml`, `go2_lidar3d.yaml`, `go2_elevation.rviz`.
- Закоммичено: `1ca5068` (`feat: добавить плагины для уклона, шероховатости и стоимости проходимости`).
- Проанализирован `nav2_params.yaml` — слоёв elevation/traversability/cost не было, только `static_layer` + `voxel_layer`/`obstacle_layer` + `inflation_layer`.
- Написана bridge-нода `scripts/elevation_to_costmap_node.py` — подписка на `/elevation_mapping_node/elevation_map`, извлечение слоя `cost`, декодирование через `decode_multiarray_to_rows_cols`, маппинг cost [0,1] → OccupancyGrid [0,100] (≤0.3→0, ≥0.5→100, интерполяция между, NaN→-1), публикация на `/elevation_costmap`.
- Написан launch-файл `launch/elevation_to_costmap.launch.py`.
- Обновлён `CMakeLists.txt` — добавлен `scripts/elevation_to_costmap_node.py` в `install(PROGRAMS ...)`, добавлен `nav_msgs` в `set(dependencies ...)`.
- Обновлён `package.xml` — добавлен `<depend>nav_msgs</depend>`.
- Обновлён `src/gazebo_sim/config/nav2_params.yaml` — добавлен слой `elevation_costmap_layer` (`nav2_costmap_2d::StaticLayer`, topic `/elevation_costmap`, `enabled: true`) в **plugins** глобальной и локальной costmap.
- Обновлён `compose.yml` — добавлены volume mounts для `elevation_to_costmap_node.py` и launch-файла в `x-el-volumes`; bridge-нода запускается в `el_command` (`python3 /elevation_to_costmap_node.py &`).
- Проверена работоспособность: синтаксис Python файлов OK, encode/decode roundtrip OK, YAML структура корректна, cost→occupancy mapping работает ожидаемо (NaN→-1, ≤0.3→0, ≥0.5→100, interpolation→1-99).

### In Progress
- (none)

### Blocked
- Сборка через `colcon build` на хосте невозможна из-за отсутствия `grid_map_msgs`. Сборка только через `make deploy` (Docker).

## Key Decisions
- **Bridge-node подход** — проще и быстрее, чем `grid_map_costmap_2d` (требует установки пакета) или модификация traversability pipeline.
- **StaticLayer** — плагин Nav2, принимающий `nav_msgs/OccupancyGrid`; подходит для карты стоимости проходимости.
- **Топик**: `/elevation_costmap` — однозначно, следует конвенции `grid_map_costmap_2d`.
- **Cost → OccupancyGrid**: cost float32 [0,1] → int8 [0,100]; пороги 0.3/0.5.
- **Размещение ноды**: в пакете `elevation_mapping_cupy` как standalone-скрипт + launch-файл, переиспользуемый между конфигами роботов.
- **Декодирование GridMap**: `decode_multiarray_to_rows_cols` уже возвращает row-major numpy (rows, cols); flatten `order="C"` даёт корректный row-major data для OccupancyGrid. **Транспонирование не требуется**.
- **Docker deployment**: bridge-нода монтируется в контейнер elevation через volume mount и запускается как фоновый процесс в `el_command`.

## Next Steps
1. `make deploy` — сборка образа и запуск контейнера.
2. Поднять elevation mapping: `docker compose --profile cpu up -d` (или `--profile elevation`).
3. Проверить топик: `ros2 topic echo /elevation_costmap`.
4. Проверить, что Nav2 строит маршрут, избегая зон с высокой стоимостью (низкой проходимостью).

## Critical Context
- GridMap публикуется в Eigen column-major; `decode_multiarray_to_rows_cols` из `gridmap_utils.py` корректно преобразует в row-major (rows, cols).
- Bridge-нода использует QoS по умолчанию (RELIABLE + VOLATILE) для подписки и публикации. StaticLayer с `map_subscribe_transient_local: true` подписывается TRANSIENT_LOCAL — эти QoS совместимы.
- Слой `cost` доступен в GridMap топике после того, как отработали плагины `slope` → `roughness` → `cost` в цепочке `plugin_config.yaml`.
- Для тестирования без GPU можно использовать `docker compose --profile cpu up -d`.

## Relevant Files

| Файл | Описание |
|------|----------|
| `elevation_mapping_cupy/.../scripts/elevation_to_costmap_node.py` | Bridge-нода (новый) |
| `elevation_mapping_cupy/.../launch/elevation_to_costmap.launch.py` | Launch-файл bridge-ноды (новый) |
| `elevation_mapping_cupy/.../package.xml` | Добавлен `nav_msgs` |
| `elevation_mapping_cupy/.../CMakeLists.txt` | Добавлен `nav_msgs` + install |
| `src/gazebo_sim/config/nav2_params.yaml` | elevation_costmap_layer в local/global |
| `compose.yml` | Volume mounts + bridge в el_command |
| `elevation_mapping_cupy/.../gridmap_utils.py` | decode/encode функций |
| `elevation_mapping_cupy/.../plugins/cost_function.py` | Источник слоя `cost` |
| `elevation_mapping_cupy/config/setups/go2/go2_lidar3d.yaml` | Публикуемые слои |
| `elevation_mapping_cupy/config/core/plugin_config.yaml` | Цепочка плагинов |
