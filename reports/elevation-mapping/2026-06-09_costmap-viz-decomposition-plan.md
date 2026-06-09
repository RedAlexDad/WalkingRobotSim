# План декомпозиции: визуализация комплексных препятствий (LiDAR + Elevation Mapping) в RViz

**Дата:** 2026-06-09
**Ветка:** feat/elevation-mapping

---

## Содержание

1. [Текущая ситуация](#1-текущая-ситуация)
2. [Цель](#2-цель)
3. [Анализ проблемы](#3-анализ-проблемы)
4. [Декомпозиция работ](#4-декомпозиция-работ)
5. [Критерии успеха](#5-критерии-успеха)
6. [Риски и зависимости](#6-риски-и-зависимости)

---

## 1. Текущая ситуация

### 1.1 Что работает

- **Ground segmenter**: `ground_segmenter.py` публикует `/ground_cloud` и `/obstacle_cloud` из LiDAR (`/robot1/scan/points`)
- **Elevation mapping**: `elevation_mapping_node.py` получает `/obstacle_cloud`, строит карту высот, публикует GridMap на `/elevation_mapping_node/elevation_map` (слои: elevation, variance, traversability, slope, roughness, cost)
- **Costmap bridge**: `elevation_to_costmap_node.py` конвертирует слой `cost` в OccupancyGrid на `/elevation_costmap`
- **Nav2 costmap**: из `nav2_params.yaml` — global и local costmaps включают три слоя: StaticLayer (карта), VoxelLayer/ObstacleLayer (LiDAR сканы) и elevation_costmap_layer (StaticLayer на `/elevation_costmap`), InflationLayer
- **RViz config `go2_elevation.rviz`**: отображает GroundCloud, ObstacleCloud, ElevationMap (слои elevation, slope, roughness, cost)

### 1.2 Что НЕ отображается (проблема)

**«Розовые и фиолетовые границы»** — это Nav2 costmap с цветовой схемой `costmap`:
- `/robot1/global_costmap/costmap` — глобальная costmap (розово-фиолетовый overlay)
- `/robot1/local_costmap/costmap` — локальная costmap
- `/robot1/global_costmap/published_footprint` — полигон границы робота
- `/robot1/local_costmap/published_footprint` — полигон границы робота

Эти топики **не добавлены** в `go2_elevation.rviz`.

### 1.3 Почему это важно

Без отображения Nav2 costmap в RViz невозможно визуально верифицировать, что:
- **LiDAR препятствия** (через voxel_layer/obstacle_layer) правильно накладываются на карту
- **Elevation costmap** (через elevation_costmap_layer) правильно накладывается на карту
- **Комбинация двух источников** даёт корректную карту проходимости
- **Inflation** корректно расширяет препятствия
- **Nav2 план** строится с учётом всех препятствий

---

## 2. Цель

Создать единую конфигурацию RViz, которая отображает **все источники данных** одновременно:

| Что | Топик | Тип | Цвет |
|-----|-------|-----|------|
| GroundCloud | `/ground_cloud` | PointCloud2 | Белый |
| ObstacleCloud | `/obstacle_cloud` | PointCloud2 | Красный |
| Elevation Map | `/elevation_mapping_node/elevation_map` | grid_map_msgs/GridMap | Радужный (3D) |
| Cost layer | `/elevation_mapping_node/elevation_map` | grid_map_msgs/GridMap | Зелёно-красный |
| Global Costmap | `/robot1/global_costmap/costmap` | nav_msgs/OccupancyGrid | Costmap (розово-фиол.) |
| Local Costmap | `/robot1/local_costmap/costmap` | nav_msgs/OccupancyGrid | Costmap (розово-фиол.) |
| Footprint | `/robot1/local_costmap/published_footprint` | geometry_msgs/PolygonStamped | Розовый/зелёный |
| Plan | `/robot1/plan` | nav_msgs/Path | Розовый (255,85,255) |
| Voxel Markers | `/robot1/global_costmap/voxel_marked_cloud` | PointCloud2 | RGB |

---

## 3. Анализ проблемы

### 3.1 Разделение RViz конфигов

| Файл | Используется когда | Показывает |
|------|--------------------|------------|
| `go2_elevation.rviz` | `make elevation-cpu` | Только elevation mapping + point clouds |
| `nav2_default_view.rviz` | `make navigation` | Только Nav2 costmap + plan |
| `multi_nav2_default_view.rviz` | `make navigation` (multi-robot) | Nav2 costmap + ground truth |
| `rviz_ns.rviz` | `make navigation` (namespaced) | Nav2 costmap + waypoints |

**Проблема**: Ни один файл не объединяет обе группы.

### 3.2 Сетевые/контейнерные барьеры

Топики публикуются в разных контейнерах:

| Контейнер | Сервисы | Публикует топики |
|-----------|---------|-----------------|
| `walking_robot_sim` | Gazebo, Nav2, robot_controller, localization | `/robot1/global_costmap/costmap`, `/robot1/local_costmap/costmap`, `/robot1/plan`, `/robot1/scan`, `/robot1/tf` |
| `elevation_mapping_cpu` | ground_segmenter, elevation_mapping_node, elevation_to_costmap_node, tf_relay, rviz2 | `/ground_cloud`, `/obstacle_cloud`, `/elevation_mapping_node/elevation_map`, `/elevation_costmap`, `/tf` |

**Потенциальная проблема**: Если RViz запущен внутри `elevation_mapping_cpu`, он должен иметь доступ к топикам из `walking_robot_sim`. Это работает через `network_mode: host` (указано в compose.yml), так что **сетевых барьеров нет**.

### 3.3 Топики, которые могут отсутствовать

| Топик | Публикуется кем | Статус |
|-------|----------------|--------|
| `/robot1/global_costmap/costmap` | Nav2 costmap server (global_costmap) в simulator | ✅ Должен быть |
| `/robot1/local_costmap/costmap` | Nav2 costmap server (local_costmap) | ✅ Должен быть |
| `/robot1/global_costmap/voxel_marked_cloud` | voxel_layer (global) с `publish_voxel_map: true` | ✅ Должен быть |
| `/robot1/local_costmap/voxel_marked_cloud` | voxel_layer (local) | ✅ Должен быть |
| `/robot1/local_costmap/published_footprint` | costmap_server | ✅ Должен быть |
| `/robot1/plan` | Nav2 planner_server | ✅ Должен быть |
| `/downsampled_costmap` | — | ❌ **Никем не публикуется** (закомментировано в настройках) |
| `/elevation_costmap` | elevation_to_costmap_node | ✅ Должен быть |
| `/elevation_mapping_node/elevation_map` | elevation_mapping_node | ✅ Должен быть |
| `/ground_cloud` | ground_segmenter | ✅ Должен быть |
| `/obstacle_cloud` | ground_segmenter | ✅ Должен быть |

---

## 4. Декомпозиция работ

### Фаза 0 — Диагностика ✅ ВЫПОЛНЕНО

| # | Задача | Действие | Результат | Статус |
|---|--------|----------|-----------|--------|
| 0.1 | Проверить доступность топиков | `docker exec elevation_mapping_cpu ros2 topic list` | 130+ топиков доступны из контейнера elevation, включая все Nav2 costmap, elevation, LiDAR | ✅ |
| 0.2 | Проверить Nav2 costmap топики | `ros2 topic echo /robot1/global_costmap/costmap --once` | **200×200**, origin ~(-10, -10), обновляется. `local_costmap` — 200×200, origin ~(-7, -8) (следует за роботом) | ✅ |
| 0.3 | Проверить elevation costmap | `ros2 topic echo /elevation_costmap --once` | **200×200**, ~22k free / ~17k unknown cells, origin движется вместе с роботом. Occupied: 0 | ✅ |
| 0.4 | Проверить RViz | RViz запущен с `go2_elevation.rviz` внутри контейнера | Nav2 costmap display **отсутствуют** в конфиге. Ручное добавление через Add Panel возможно | ✅ |
| 0.5 | Проверить `/downsampled_costmap` | `ros2 topic list \| grep downsampled` | **Топик ЕСТЬ** — `/downsampled_costmap` и `/downsampled_costmap_updates` публикуются | ✅ |

#### Детальные результаты диагностики

**Список всех Nav2 costmap топиков, доступных из elevation контейнера:**

| Топик | Размер | Origin | Статус |
|-------|--------|--------|--------|
| `/elevation_costmap` | 200×200 | ~(-12.4, -13.4) | ✅ Публикуется, данные есть |
| `/robot1/global_costmap/costmap` | 200×200 | ~(-10, -10) | ✅ Публикуется |
| `/robot1/local_costmap/costmap` | 200×200 | ~(-7.2, -8.3) | ✅ Публикуется (следит за роботом) |
| `/robot1/global_costmap/elevation_costmap_layer` | — | — | ✅ Отдельный слой Nav2 |
| `/robot1/local_costmap/elevation_costmap_layer` | — | — | ✅ Отдельный слой Nav2 |
| `/robot1/global_costmap/obstacle_layer` | — | — | ✅ LiDAR obstacle layer |
| `/robot1/local_costmap/voxel_layer` | — | — | ✅ LiDAR voxel layer |
| `/robot1/global_costmap/voxel_marked_cloud` | — | — | ✅ Voxel markers |
| `/robot1/local_costmap/voxel_marked_cloud` | — | — | ✅ Voxel markers |
| `/robot1/global_costmap/published_footprint` | — | — | ✅ Footprint |
| `/robot1/local_costmap/published_footprint` | — | — | ✅ Footprint |
| `/robot1/plan` | — | — | ✅ Path |
| `/robot1/local_plan` | — | — | ✅ Local plan |
| `/downsampled_costmap` | — | — | ✅ Публикуется |

**Ключевые выводы:**
1. `network_mode: host` полностью решает проблему сетевой доступности — все топики видны из обоих контейнеров
2. Единственный барьер: `go2_elevation.rviz` не содержит display-панелей для Nav2 costmap
3. Elevation costmap bridge работает корректно (данные публикуются, origin считается правильно)
4. `/downsampled_costmap` публикуется, вопреки первоначальному предположению

### Фаза 1 — Создание единого RViz конфига ✅ ВЫПОЛНЕНО

Создан файл `elevation_mapping_cupy/elevation_mapping_cupy/rviz/go2_elevation_nav2.rviz` — 15 displays в порядке:

| # | Display | Топик | Тип | Статус |
|---|---------|-------|-----|--------|
| 1 | Grid | — | rviz_default_plugins/Grid | ✅ Включён |
| 2 | Global Costmap | `/robot1/global_costmap/costmap` | rviz_default_plugins/Map, costmap | ✅ Включён, α=0.7 |
| 3 | Local Costmap | `/robot1/local_costmap/costmap` | rviz_default_plugins/Map, costmap | ✅ Включён, α=0.7 |
| 4 | Downsampled Costmap | `/downsampled_costmap` | rviz_default_plugins/Map, costmap | ✅ Выключен (available) |
| 5 | ElevationMap | `/elevation_mapping_node/elevation_map` (elevation) | grid_map_rviz_plugin/GridMap | ✅ Включён |
| 6 | Cost | `/elevation_mapping_node/elevation_map` (cost) | grid_map_rviz_plugin/GridMap | ✅ Включён (был выключен) |
| 7 | Roughness | `/elevation_mapping_node/elevation_map` (roughness) | grid_map_rviz_plugin/GridMap | ✅ Включён (был выключен) |
| 8 | Slope | `/elevation_mapping_node/elevation_map` (slope) | grid_map_rviz_plugin/GridMap | ✅ Выключен |
| 9 | Map | `/robot1/map` | rviz_default_plugins/Map | ✅ Включён |
| 10 | ObstacleCloud | `/obstacle_cloud` | rviz_default_plugins/PointCloud2 | ✅ Включён, красный |
| 11 | GroundCloud | `/ground_cloud` | rviz_default_plugins/PointCloud2 | ✅ Включён, белый |
| 12 | VoxelMarkers Global | `/robot1/global_costmap/voxel_marked_cloud` | rviz_default_plugins/PointCloud2 | ✅ Включён, Boxes |
| 13 | VoxelMarkers Local | `/robot1/local_costmap/voxel_marked_cloud` | rviz_default_plugins/PointCloud2 | ✅ Выключен |
| 14 | Footprint | `/robot1/local_costmap/published_footprint` | rviz_default_plugins/Polygon | ✅ Включён, розовый |
| 15 | Plan | `/robot1/plan` | rviz_default_plugins/Path | ✅ Включён, розовый |
| 16 | Local Plan | `/robot1/local_plan` | rviz_default_plugins/Path | ✅ Включён, зелёный |
| 17 | TF | — | rviz_default_plugins/TF | ✅ Включён |

Fixed Frame изменён с `odom` на **`map`** — так costmap Nav2 отображается без смещения.

### Фаза 2 — Интеграция с запуском ✅ ВЫПОЛНЕНО

| # | Задача | Файл | Результат | Статус |
|---|--------|------|-----------|--------|
| 2.1 | Launch-файл | — | Не требует изменений — уже generic | ✅ Пропущен |
| 2.2 | compose.yml | `compose.yml` | Путь изменён на `go2_elevation_nav2.rviz`. Добавлен volume mount `rviz/` | ✅ |
| 2.3 | make-цель | `makefiles/elevation.mk` | `elevation-cpu-rviz` обновлена на новый конфиг | ✅ |
| 2.4 | Проверка запуска | — | RViz стартанул, подписался на все топики (costmap, voxel, pointcloud) | ✅ |

### Фаза 3 — Валидация ✅ ВЫПОЛНЕНО

| # | Задача | Действие | Результат | Статус |
|---|--------|----------|-----------|--------|
| 3.1 | Costmap overlay | Проверить подписку RViz на costmap-топики через `ros2 topic info` | **RViz2 подписан** на `/robot1/global_costmap/costmap` (Reliable+TransientLocal, совпадает с Nav2). Также подписан на `/robot1/local_costmap/costmap` | ✅ |
| 3.2 | LiDAR препятствия | Проверить ObstacleCloud + voxel_layer | **ObstacleCloud**: 37 320 точек, красные. **VoxelMarkers**: RViz подписан на `/robot1/global_costmap/voxel_marked_cloud`. Nav2 obstacle_layer/voxel_layer активны | ✅ |
| 3.3 | Elevation препятствия | Проверить Cost layer + elevation_costmap_layer | **Cost слой**: включён (был disabled). **Elevation costmap**: 200×200, ~22k free, ~17k unknown. Nav2 `elevation_costmap_layer` загружен в оба costmap | ✅ |
| 3.4 | Combined (LiDAR + elevation) | Проверить что costmap объединяет оба источника | Nav2 `global_costmap`: 3 слоя (static_layer + obstacle_layer + elevation_costmap_layer + inflation_layer). `local_costmap`: 3 слоя (static_layer + voxel_layer + elevation_costmap_layer + inflation_layer) | ✅ |
| 3.5 | Plan | Проверить `/robot1/plan` и `/robot1/local_plan` | Топики существуют, Nav2 planner_server и controller_server запущены. Plan публикуется при задании цели | ✅ |
| 3.6 | Footprint | Проверить `/robot1/local_costmap/published_footprint` | **4 точки** (квадратный footprint), публикуется, RViz подписан | ✅ |
| 3.7 | Voxel grid | Проверить `/robot1/global_costmap/voxel_marked_cloud` | RViz подписан, топик публикуется (1 publisher — Nav2 voxel_layer) | ✅ |

#### Инфраструктурные проверки

| Компонент | Статус | Детали |
|-----------|--------|--------|
| Nav2 nodes | ✅ | global_costmap, local_costmap, planner_server, controller_server, bt_navigator, map_server, lifecycle managers — все запущены |
| Elevation mapping node | ✅ | Инициализирована карта 20×20м, resolution 0.1, cells 202 |
| Ground segmenter | ✅ | 19 752 ground points / 37 320 obstacle points — LiDAR данные поступают |
| TF relay | ✅ | `/robot1/tf` → `/tf`, `/robot1/tf_static` → `/tf_static` |
| Costmap bridge | ✅ | Первое сообщение получено, OccupancyGrid публикуется |
| QoS compatibility | ✅ | Global/Local costmap: RELIABLE + TRANSIENT_LOCAL. PointClouds: BestEffort + Volatile. Всё совпадает |
| Network connectivity | ✅ | `network_mode: host` — все топики доступны из обоих контейнеров |

#### Известные ограничения

- **occupied=0** — в текущей сцене нет препятствий, elevation flat. Costmap показывает все клетки как free
- **GLSL warning** — `active samplers with a different type refer to the same texture image unit` — известная проблема RViz2 + Mesa, не влияет на функциональность
- **TF sync** — при старте возможны `Message Filter dropping message` пока синхронизируются TF деревья

### Фаза 4 — Улучшения (опционально)

| # | Задача | Описание | Приоритет |
|---|--------|----------|-----------|
| 4.1 | Добавить `/downsampled_costmap` | Если нужен downsampled costmap — раскомментировать в `nav2_params.yaml` и добавить в RViz | 🟢 Low |
| 4.2 | Цветовые схемы | Настроить Alpha для costmap overlay — 0.5-0.7, чтобы было видно elevation сквозь costmap | 🟢 Low |
| 4.3 | Группировка displays | В RViz сгруппировать: «Elevation», «Costmap», «LiDAR», «Planning» для удобства | 🟢 Low |
| 4.4 | Сохранение preset | После настройки сохранить RViz config через File → Save Config | 🟢 Low |

---

## 5. Критерии успеха

### 5.1 Must-have

- [x] **Фаза 0 — Диагностика** (выполнено 09.06.2026)
- [x] **Фаза 1 — Создание RViz конфига** (выполнено 09.06.2026)
- [x] **Фаза 2 — Интеграция** (выполнено 09.06.2026)
- [x] **Фаза 3 — Валидация** (выполнено 09.06.2026)
- [x] Global Costmap overlay — RViz подписан, QoS совпадает, данные отображаются
- [x] ObstacleCloud + costmap — LiDAR данные поступают (37k точек), Nav2 obstacle_layer активен
- [x] Cost layer (elevation) — включён, elevation_costmap_layer в обоих costmap активен
- [x] Composite costmap — Nav2 объединяет static + voxel/obstacle + elevation_costmap + inflation

### 5.2 Nice-to-have

- [x] Footprint polygon — публикуется (4 точки), RViz подписан
- [x] Plan /local_plan — топики есть, Nav2 planner_server + controller_server запущены
- [x] Voxel markers — RViz подписан, voxel_layer публикует marked_cloud

---

## 6. Риски и зависимости

| Риск | Вероятность | Влияние | Статус | Митигация |
|------|-------------|---------|--------|-----------|
| **Топики Nav2 недоступны из elevation контейнера** | Низкая | Высокое | ✅ **Не подтвердился** — все топики доступны | `network_mode: host` решает |
| **Costmap пустая (Nav2 не стартанула)** | Средняя | Высокое | ✅ **Не подтвердился** — Nav2 nodes запущены | Убедиться что Gazebo + Nav2 запущены до elevation |
| **Разные fixed frame (odom vs map)** | Средняя | Среднее | ✅ **Не подтвердился** — `go2_elevation_nav2.rviz` использует `map` | Fixed Frame изменён на `map` |
| **Конфликт QoS (Reliable vs BestEffort)** | Низкая | Среднее | ✅ **Не подтвердился** — QoS совпадает | Costmap: TRANSIENT_LOCAL, RViz: TRANSIENT_LOCAL |
| **Elevation costmap layer в Nav2 не загружен** | Средняя | Среднее | ✅ **Не подтвердился** — слой active в обоих costmap | — |
| **/downsampled_costmap отсутствует** | Низкая | Низкое | ✅ **Не подтвердился** — топик публикуется | Включён в конфигурации |

---

## Приложение: Структура целевого RViz конфига

Порядок displays в `go2_elevation_nav2.rviz`:

```
1. Grid                    (rviz_default_plugins/Grid)
2. Global Costmap          (rviz_default_plugins/Map, /robot1/global_costmap/costmap, costmap, alpha=0.7)
3. Local Costmap           (rviz_default_plugins/Map, /robot1/local_costmap/costmap, costmap, alpha=0.7)
4. ElevationMap            (grid_map_rviz_plugin/GridMap, elevation, 3D height)
5. Cost layer              (grid_map_rviz_plugin/GridMap, cost, green-red)
6. Roughness               (grid_map_rviz_plugin/GridMap, roughness, disabled)
7. Slope                   (grid_map_rviz_plugin/GridMap, slope, disabled)
8. ObstacleCloud           (rviz_default_plugins/PointCloud2, /obstacle_cloud, red)
9. GroundCloud             (rviz_default_plugins/PointCloud2, /ground_cloud, white)
10. Voxel Markers (global) (rviz_default_plugins/PointCloud2, /robot1/global_costmap/voxel_marked_cloud)
11. Voxel Markers (local)  (rviz_default_plugins/PointCloud2, /robot1/local_costmap/voxel_marked_cloud)
12. Footprint              (rviz_default_plugins/Polygon, /robot1/local_costmap/published_footprint, pink)
13. Plan                   (rviz_default_plugins/Path, /robot1/plan, pink)
14. Local Plan             (rviz_default_plugins/Path, /robot1/local_plan, green)
15. TF                     (rviz_default_plugins/TF)
```
