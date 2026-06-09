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

### Фаза 0 — Диагностика (проверить текущее состояние)

| # | Задача | Действие | Ожидаемый результат |
|---|--------|----------|---------------------|
| 0.1 | Проверить доступность топиков | Запустить `make elevation-cpu` + `make navigation`, затем `docker exec elevation_mapping_cpu ros2 topic list` | Список всех доступных топиков |
| 0.2 | Проверить Nav2 costmap топики | `ros2 topic echo /robot1/global_costmap/costmap --once` | Есть данные, не пустой |
| 0.3 | Проверить elevation costmap | `ros2 topic echo /elevation_costmap --once` | Есть данные, не пустой |
| 0.4 | Проверить RViz логи | Запустить RViz, открыть Panel → Add → `nav2_msgs/OccupancyGrid` на `/robot1/global_costmap/costmap` | Costmap отображается |
| 0.5 | Проверить `/downsampled_costmap` | `ros2 topic list \| grep downsampled` | Топика нет — ожидаемо |

### Фаза 1 — Создание единого RViz конфига

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 1.1 | Создать `go2_elevation_nav2.rviz` | `elevation_mapping_cupy/elevation_mapping_cupy/rviz/go2_elevation_nav2.rviz` | Скопировать `go2_elevation.rviz` как основу | 🔴 High |
| 1.2 | Добавить Global Costmap display | `go2_elevation_nav2.rviz` | `rviz_default_plugins/Map`, топик `/robot1/global_costmap/costmap`, Color Scheme: `costmap`, Alpha: 0.7 | 🔴 High |
| 1.3 | Добавить Local Costmap display | `go2_elevation_nav2.rviz` | `rviz_default_plugins/Map`, топик `/robot1/local_costmap/costmap`, Color Scheme: `costmap`, Alpha: 0.7 | 🔴 High |
| 1.4 | Добавить Footprint display | `go2_elevation_nav2.rviz` | `rviz_default_plugins/Polygon`, топик `/robot1/local_costmap/published_footprint`, Color: 255;85;255 (розовый) | 🟡 Medium |
| 1.5 | Добавить Path display | `go2_elevation_nav2.rviz` | `rviz_default_plugins/Path`, топик `/robot1/plan`, Color: 255;85;255 (розовый), Pose Style: None, Line Width: 0.1 | 🟡 Medium |
| 1.6 | Добавить Local Plan display | `go2_elevation_nav2.rviz` | `rviz_default_plugins/Path`, топик `/robot1/local_plan`, Color: 0;255;0 (зелёный) | 🟢 Low |
| 1.7 | Добавить Voxel Markers (global) | `go2_elevation_nav2.rviz` | `rviz_default_plugins/PointCloud2`, топик `/robot1/global_costmap/voxel_marked_cloud`, Style: Boxes, Size: 0.05 | 🟡 Medium |
| 1.8 | Добавить Voxel Markers (local) | `go2_elevation_nav2.rviz` | `rviz_default_plugins/PointCloud2`, топик `/robot1/local_costmap/voxel_marked_cloud`, Style: Boxes, Size: 0.05 | 🟢 Low |
| 1.9 | Включить Cost GridMap display | `go2_elevation_nav2.rviz` | Поменять `Enabled: false` → `true` для существующего Cost-слоя (строки 233-258) | 🔴 High |
| 1.10 | Включить Roughness display | `go2_elevation_nav2.rviz` | Поменять `Enabled: false` → `true` для Roughness | 🟢 Low |
| 1.11 | Настроить порядок отображения | `go2_elevation_nav2.rviz` | 1. Grid → 2. GlobalCostmap → 3. LocalCostmap → 4. ElevationMap → 5. Cost → 6. ObstacleCloud → 7. GroundCloud → 8. Voxel → 9. Footprint → 10. Path → 11. TF | 🟡 Medium |

### Фаза 2 — Интеграция с запуском

| # | Задача | Файл | Описание | Приоритет |
|---|--------|------|----------|-----------|
| 2.1 | Изменить launch-файл для нового RViz config | `elevation_mapping_cupy/elevation_mapping_cupy/launch/elevation_mapping.launch.py` | Добавить аргумент выбора RViz config (`go2_elevation.rviz` по умолчанию, `go2_elevation_nav2.rviz` — опционально) | 🔴 High |
| 2.2 | Изменить compose.yml | `compose.yml` | В команде `elevation_mapping_cpu` вместо `go2_elevation.rviz` указать `go2_elevation_nav2.rviz` | 🔴 High |
| 2.3 | Добавить make-цель `elevation-viz` | `makefiles/elevation.mk` | Запуск только RViz с новым конфигом внутри запущенного контейнера (аналог `elevation-rviz`) | 🟢 Low |
| 2.4 | Проверить запуск `make elevation-cpu` | — | RViz открывается с новым конфигом, все топики доступны | 🔴 High |

### Фаза 3 — Валидация (проверить, что всё корректно отображается)

| # | Задача | Действие | Ожидаемый результат | Приоритет |
|---|--------|----------|---------------------|-----------|
| 3.1 | Визуальная проверка costmap overlay | В RViz: включить GlobalCostmap и ElevationMap одновременно | Costmap (розово-фиолетовый) накладывается поверх elevation map, совпадают границы | 🔴 High |
| 3.2 | Проверка LiDAR препятствий | Разместить препятствие перед роботом | Красные точки ObstacleCloud → розовые пиксели на costmap → фиолетовая граница после inflation | 🔴 High |
| 3.3 | Проверка elevation препятствий | Разместить препятствие на неровной поверхности | Cost слой (зелёно-красный) → розовые пиксели на costmap | 🔴 High |
| 3.4 | Проверка combined (LiDAR + elevation) | Препятствие, видимое и в LiDAR, и в elevation | Costmap показывает ОДИН контур, а не два раздельных | 🔴 High |
| 3.5 | Проверка плана | `make navigation`, задать цель Nav2 | Розовый путь (`/robot1/plan`) обходит препятствия | 🟡 Medium |
| 3.6 | Проверка footprint | Движение робота | Розовый полигон (`published_footprint`) совпадает с положением робота | 🟡 Medium |
| 3.7 | Проверка voxel_grid | Наличие препятствий | Серые/цветные кубики в местах препятствий | 🟢 Low |

### Фаза 4 — Улучшения (опционально)

| # | Задача | Описание | Приоритет |
|---|--------|----------|-----------|
| 4.1 | Добавить `/downsampled_costmap` | Если нужен downsampled costmap — раскомментировать в `nav2_params.yaml` и добавить в RViz | 🟢 Low |
| 4.2 | Цветовые схемы | Настроить Alpha для costmap overlay — 0.5-0.7, чтобы было видно elevation сквозь costmap | 🟢 Low |
| 4.3 | Группировка displays | В RViz сгруппировать: «Elevation», «Costmap», «LiDAR», «Planning» для удобства | 🟢 Low |
| 4.4 | Сохранение preset | После настройки сохранить RViz config через File → Save Config | 🟢 Low |

---

## 5. Критерии успеха

### 5.1 Must-have (Фаза 1 + 2)

- [ ] При `make elevation-cpu` RViz отображает **все** перечисленные display одновременно
- [ ] Global Costmap overlay (розово-фиолетовый) виден поверх Elevation Map
- [ ] ObstacleCloud (красные точки) совпадает с розовыми пикселями на costmap
- [ ] Cost layer (зелёно-красный GridMap) коррелирует с costmap
- [ ] Composite costmap (LiDAR + elevation) отображается как единая карта

### 5.2 Nice-to-have (Фаза 3)

- [ ] Footprint polygon отображается при движении робота
- [ ] Plan /local_plan отображаются при задании цели Nav2
- [ ] Voxel markers отображаются

---

## 6. Риски и зависимости

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| **Топики Nav2 недоступны из elevation контейнера** | Низкая | Высокое | `network_mode: host` решает; проверить `ros2 topic list` в фазе 0 |
| **Costmap пустая (Nav2 не стартанула)** | Средняя | Высокое | Убедиться что `make navigation` запущен до `make elevation-cpu` |
| **Разные fixed frame (odom vs map)** | Средняя | Среднее | `go2_elevation.rviz` использует `odom`, Nav2 топики — `map`. RViz автоматически преобразует через TF |
| **Конфликт QoS (Reliable vs BestEffort)** | Низкая | Среднее | Costmap публикуется с TRANSIENT_LOCAL, RViz Map display должен читать `Reliable + TransientLocal` |
| **Elevation costmap layer в Nav2 не загружен** | Средняя | Среднее | Проверить логи Nav2: `ros2 node list | grep costmap` |

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
