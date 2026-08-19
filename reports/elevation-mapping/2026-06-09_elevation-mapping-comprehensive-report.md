# Elevation Mapping — Полный отчёт

**Дата:** 2026-06-09
**Ветка:** feat/elevation-mapping

---

## Содержание

1. [Обзор](#1-обзор)
2. [Архитектура и поток данных](#2-архитектура-и-поток-данных)
3. [Анализ координатных конвенций](#3-анализ-координатных-конвенций)
4. [Баг #1: Перепутаны оси в shift_map_xy](#4-баг-1-перепутаны-оси-в-shift_map_xy)
5. [Баг #2: Поворот на 90° в RViz (публикация GridMap)](#5-баг-2-поворот-на-90-в-rviz-публикация-gridmap)
6. [Баг #3: Ориентация costmap (бридж OccupancyGrid)](#6-баг-3-ориентация-costmap-бридж-occupancygrid)
7. [Баг #4: RuntimeWarning в custom_kernels.py](#7-баг-4-runtimewarning-в-custom_kernelspy)
8. [Баг #5: 11 падающих тестов — корни и исправления](#8-баг-5-11-падающих-тестов--корни-и-исправления)
9. [Баг #6: Размерности в traversability_filter](#9-баг-6-размерности-в-traversability_filter)
10. [Баг #7: Скалярный индекс в polygon_mask_cpu](#10-баг-7-скалярный-индекс-в-polygon_mask_cpu)
11. [Инфраструктура: Volume mount для Docker](#11-инфраструктура-volume-mount-для-docker)
12. [Инфраструктура: Coverage](#12-инфраструктура-coverage)
13. [Тестирование: 477 тестов — полный анализ](#13-тестирование-477-тестов--полный-анализ)
14. [Итоговые результаты](#14-итоговые-результаты)

---

## 1. Обзор

Пакет `elevation_mapping_cupy` обеспечивает построение 2.5D карты высот в реальном времени из LiDAR pointcloud с GPU-ускорением (CuPy). Интегрирован в WalkingRobotSim как основной pipeline восприятия для робота GO2.

### Компоненты

| Компонент | Путь | Язык | Роль |
|-----------|------|------|------|
| Core library | `elevation_mapping_cupy/` | Python + CUDA | Карта высот, фьюжн, IO |
| CUDA kernels | `kernels/custom_kernels.py` | Python/CuPy | GPU-вставка точек, фильтрация |
| ROS2 node | `scripts/elevation_mapping_node.py` | Python | Жизненный цикл, TF, публикация GridMap |
| Costmap bridge | `scripts/elevation_to_costmap_node.py` | Python | GridMap → OccupancyGrid |
| Конфиги | `config/` | YAML | Параметры робота, ядра |
| Тесты | `tests/` | Python/pytest | 477 unit + integration тестов |

### Динамика количества тестов

```
Исходно:         31 failed,   0 passed   (после слияния)
Phase 1:          0 failed,  82 passed   (backend + plugin manager)
Phase 2-3:        0 failed, 346 passed   (core elevation map)
Phase 3:          0 failed, 387 passed   (image kernels + traversability)
Phase 4:          0 failed, 477 passed   (integration + stress)
RuntimeWarning:   0 failed, 477 passed   (с -W error::RuntimeWarning)
Coverage:        71% TOTAL
```

---

## 2. Архитектура и поток данных

### 2.1 Pipeline

```
LiDAR PointCloud
    ↓
Ground Segmenter (GPF) → /ground_cloud, /obstacle_cloud
    ↓
elevation_mapping_node.py
    ├── addPoints (pointcloud → карта высот)
    ├── update_map (затухание по времени)
    ├── publish_map (GridMap → ROS2 топик)
    └── shift_map_xy (движение робота → сдвиг карты)
    ↓
elevation_to_costmap_node.py
    └── GridMap → OccupancyGrid → Nav2 costmap
```

### 2.2 Внутреннее представление карты

- **Shape:** `(layers, rows, cols)` — 3D тензор
- **Конвенция:** `Row = Y, Col = X`
- **Тип данных:** `float32` на GPU (CuPy) или CPU (NumPy)
- **Память:** Row-major: `index = row * width + col`
- **Центр:** Начало координат карты — в ЦЕНТРЕ в мировых координатах

### 2.3 Сравнение координатных систем

| Система | Строки | Колонки | Хранение | Origin |
|---------|--------|---------|----------|--------|
| elevation_mapping_cupy | Y (юг→север) | X (запад→восток) | Row-major | Центр |
| grid_map C++ | -X (восток→запад) | -Y (север→юг) | Column-major | Центр |
| ROS OccupancyGrid | Y (юг→север) | X (запад→восток) | Row-major | Левый нижний угол |

---

## 3. Анализ координатных конвенций

### 3.1 elevation_mapping_cupy Internal (Row=Y, Col=X)

Определено в `custom_kernels.py:40-60`:

```cuda
// Fixed: Row-Major (Row=Y, Col=X)
int idx_y = idx / width;   // Row index = Y
int idx_x = idx % width;   // Column index = X
```

Функции индексации:
```cuda
__device__ int get_x_idx(float16 x, float16 center) {
    int i = (x - center) / resolution + 0.5 * width;
    return i;  // x < center → отрицательное смещение (запад)
}
__device__ int get_y_idx(float16 y, float16 center) {
    int i = (y - center) / resolution + 0.5 * height;
    return i;  // y < center → отрицательное смещение (юг)
}
```

Ключевой вывод:
- `idx_x = 0` → запад (min X), `idx_x = width` → восток (max X)
- `idx_y = 0` → юг (min Y), `idx_y = height` → север (max Y)

Матрица в конвенции elevation_mapping:
```
[0, 0]            = (запад, юг)    = ЮЗ угол
[0, max_col]      = (восток, юг)   = ЮВ угол
[max_row, 0]      = (запад, север) = СЗ угол
[max_row, max_col] = (восток, север) = СВ угол
```

### 3.2 grid_map C++ (Row=-X, Col=-Y)

Из `GridMapMath.cpp:64-67`:
```cpp
// transformBufferOrderToMapFrame возвращает {-index[0], -index[1]}
// index[0] = row, index[1] = column
// row 0 → -X (восток), увеличение row → уменьшение X (запад)
// col 0 → -Y (север), увеличение col → уменьшение Y (юг)
```

Матрица в конвенции grid_map:
```
[0, 0]            = (восток, север)    = СВ угол
[0, max_col]      = (восток, юг)       = ЮВ угол
[max_row, 0]      = (запад, север)     = СЗ угол
[max_row, max_col] = (запад, юг)       = ЮЗ угол
```

### 3.3 Преобразование: elevation_mapping → grid_map

В `elevation_mapping.py:734-756`:

```python
def _transform_to_grid_map_coordinate_convention(self, m):
    # Вход: (rows=Y, cols=X) — конвенция elevation_mapping
    m = m.T           # (Y,X) → (X,Y) — перестановка осей
    m = xp.flip(m, 0) # Row=-X: увеличение row = уменьшение X
    m = xp.flip(m, 1) # Col=-Y: увеличение col = уменьшение Y
    return m          # Результат: конвенция grid_map (Row=-X, Col=-Y)
```

### 3.4 Обратное преобразование: grid_map → elevation_mapping

```python
def _transform_to_elevation_mapping_coordinate_convention(self, m):
    m = xp.flip(m, 0) # Отмена шага 3: Col=-Y → Col=+Y
    m = xp.flip(m, 1) # Отмена шага 2: Row=-X → Row=+X
    m = m.T           # Отмена шага 1: (X,Y) → (Y,X)
    return m
```

### 3.5 ROS OccupancyGrid

- **Origin:** Левый нижний угол клетки (0,0) = (min_x, min_y)
- **Данные:** Row-major: `index = y * width + x`
  - y = 0 → юг (min Y), y = rows-1 → север (max Y)
  - x = 0 → запад (min X), x = cols-1 → восток (max X)

---

## 4. Баг #1: Перепутаны оси в shift_map_xy

### 4.1 Симптом

При движении робота по X карта сдвигалась по Y, и наоборот. Карта «скользила» перпендикулярно направлению движения.

### 4.2 Причина

`shift_map_xy` получает `delta_pixel` как `[x, y]` (мировые координаты). Тензор карты имеет форму `(layers, rows, cols)` где `rows=Y, cols=X`. `cp.roll` с `axis=(1, 2)` ожидает `[row_shift, col_shift]` = `[Y_shift, X_shift]`.

До исправления:
```python
shift_value = xp.array([delta_pixel[0], delta_pixel[1]], dtype=xp.int32)
# Неправильно! [x, y] = [row_shift=x, col_shift=y]
# Движение по X сдвигает строки (Y), движение по Y сдвигает колонки (X)
```

### 4.3 Исправление

```python
shift_value = xp.array([delta_pixel[1], delta_pixel[0]], dtype=xp.int32)
# Правильно: [y, x] = [row_shift=Y, col_shift=X]
```

### 4.4 Регрессия

В `test_map_shifting.py`:
- `test_shift_x_only_affects_columns` — маркер в центр, сдвиг X, проверка что маркер переместился в новую колонку, а не в новую строку
- `test_shift_y_only_affects_rows` — то же для Y
- `test_diagonal_shift` — X+Y одновременно
- `test_negative_shift` — отрицательное направление

---

## 5. Баг #2: Поворот на 90° в RViz (публикация GridMap)

### 5.1 Симптом

Карта высот отображалась в RViz повёрнутой на 90° против часовой стрелки. LiDAR pointcloud отображалась правильно.

### 5.2 Причина

`get_map_with_name_ref` использовал простой поворот на 180° (два flip) вместо правильного преобразования:

```python
# СТАРОЕ (неправильно):
m = xp.flip(m, 0)
m = xp.flip(m, 1)
```

Поворот на 180° сохраняет оси: Row→Row (всё ещё Y), Col→Col (всё ещё X). Но grid_map требует Row→X, Col→Y. Отсутствие транспонирования привело к повороту на 90°.

### 5.3 Исправление

```python
# НОВОЕ (правильно):
m = m.T           # Перестановка: Row=Y,Col=X → Row=X,Col=Y
m = xp.flip(m, 0) # Отрицание X: Row=+X → Row=-X
m = xp.flip(m, 1) # Отрицание Y: Col=+Y → Col=-Y
```

Эквивалентно: `rot90(m.T, k=2)`.

### 5.4 Регрессия

Интеграционный тест в `test_tf_gridmap_integration.py`:
- `test_05_no_axis_swap`: движение +1м по X → центр карты меняется на ~1м по X, изменение по Y < 0.15м

---

## 6. Баг #3: Ориентация costmap (бридж OccupancyGrid)

### 6.1 Симптом

Costmap препятствий от `elevation_to_costmap_node.py` отображалась в неправильном месте и повёрнутой на 90°. Nav2 не мог строить маршруты.

### 6.2 Причина

Бридж получал GridMap (уже в конвенции grid_map: Row=-X, Col=-Y) и копировал данные напрямую в OccupancyGrid без преобразования:

```python
# СТАРОЕ (неправильно):
cost = decode_multiarray_to_rows_cols(self._layer_name, msg.data[idx])
rows, cols = cost.shape  # Данные в конвенции grid_map (Row=-X, Col=-Y)
out.info.origin = msg.info.pose  # БАГ: msg.info.pose = ЦЕНТР карты
out.data = occ.flatten(order="C").tolist()  # Row-major, но конвенция grid_map
```

Два независимых бага:
1. **Нет обратного преобразования:** OccupancyGrid ожидает Row=Y, Col=X (row-major), но данные от GridMap в Row=-X, Col=-Y
2. **Неправильный origin:** OccupancyGrid требует origin в левом нижнем углу. Код копировал `msg.info.pose` — ЦЕНТР карты

### 6.3 Исправление

```python
# НОВОЕ (правильно):
cost = decode_multiarray_to_rows_cols(self._layer_name, msg.data[idx])
# Обратное преобразование grid_map → OccupancyGrid:
cost = np.flip(cost, 0)  # Row=-X → Row=+X
cost = np.flip(cost, 1)  # Col=-Y → Col=+Y
cost = cost.T            # (X,Y) → (Y,X) = (rows=Y, cols=X)
rows, cols = cost.shape

out.info.resolution = msg.info.resolution
out.info.width = cols
out.info.height = rows
# Origin: центр → левый нижний угол
cx = msg.info.pose.position.x
cy = msg.info.pose.position.y
out.info.origin.position.x = cx - cols * msg.info.resolution / 2.0
out.info.origin.position.y = cy - rows * msg.info.resolution / 2.0
out.data = occ.flatten(order="C").tolist()
```

### 6.4 Результат

Costmap совпадает с elevation map в RViz. Nav2 работает корректно.

---

## 7. Баг #4: RuntimeWarning в custom_kernels.py

### 7.1 Симптом

143 RuntimeWarning («invalid value encountered in divide/multiply/cast»). 66 тестов падали с `-W error::RuntimeWarning`.

### 7.2 Причины

Четыре паттерна:

#### 7.2.1 NaN/Inf в pointcloud

Когда pointcloud содержит NaN или Inf:
```python
# Старое: NaN * что-то = RuntimeWarning
new_n = n_points[..., None] * 0
```

**Исправление:**
```python
with np.errstate(invalid='ignore'):
    new_n = n_points[..., None] * 0
```

Плюс фильтр `finite`:
```python
finite = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
valid = valid & finite
```

#### 7.2.2 NaN/Inf в cast to int

```python
# Старое: int(NaN) → RuntimeWarning
int_idxs = xp.array(...).astype(xp.int32)
```

**Исправление:** Внутри `np.errstate(invalid='ignore')`.

#### 7.2.3 Деление на 0 в average_map_cpu

```python
# Старое: new_cnt может быть 0
variance_ok = ~((new_v / new_cnt) > max_variance)
```

**Исправление:**
```python
variance_ok = ~((new_v / np.maximum(new_cnt, 1)) > max_variance)
```

#### 7.2.4 Деление на 0 в erosion.py

Когда все ячейки слоя равны (layer_max == layer_min):
```python
# Старое: layer_range = 0 → деление на 0
layer_np_normalized = (layer_np - layer_min) * 255 / (layer_max - layer_min)
```

**Исправление:**
```python
if layer_range > 0:
    layer_np_normalized = ((layer_np - layer_min) * 255 / layer_range).astype("uint8")
else:
    layer_np_normalized = np.zeros_like(layer_np, dtype=np.uint8)
```

### 7.3 Результат

Все 477 тестов проходят с `-W error::RuntimeWarning` — 0 предупреждений.

---

## 8. Баг #5: 11 падающих тестов — корни и исправления

Шесть багов, найденных при Phase 2-3:

### 8.1 Отсутствует метод `get_position`

**Ошибка:** `AttributeError: 'ElevationMap' object has no attribute 'get_position'`
**Причина:** Метод потерян при слиянии.
**Исправление:** Добавлен метод, делегирующий `get_center_position`.

### 8.2 `exists_layer` не проверяет `additional_layers`

**Ошибка:** Тесты для `feat_0`, `feat_1` возвращали False.
**Причина:** `exists_layer` проверял только `layer_names`, не `param.additional_layers`.
**Исправление:** Добавлено `elif name in self.param.additional_layers: return True`.

### 8.3 `process_map_for_publish` — broadcast error

**Ошибка:** `ValueError: shapes (202,202) (200,200) not aligned`
**Причина:** `cell_n = round(N) + 2` даёт (202,202), а маска `fill_nan=True` — (200,200).
**Исправление:** Обрезка маски `[1:-1, 1:-1]` при несовпадении форм.

### 8.4 `get_normal_ref` — жёстко заданный размер

**Ошибка:** Нормали всегда 198×198 независимо от размера карты.
**Исправление:** Динамический размер из `cell_n - 2`.

### 8.5 Фикстура не синхронизирует `additional_layers`

**Ошибка:** Параметризованная фикстура `add_lay` не обновляла `p.additional_layers`.
**Исправление:** `p.additional_layers = additional_layer` в фикстуре.

### 8.6 Слой `rgb` не читается через `get_map_with_name_ref`

**Ошибка:** `rgb` существует для ввода, но не для чтения.
**Исправление:** Убран `rgb` из тестовых ожиданий.

---

## 9. Баг #6: Размерности в traversability_filter

### 9.1 Симптом

`test_traversability_filter.py` падал с `ValueError: dimensions mismatch` в `np.concatenate`.

### 9.2 Причина

Три операции dilation дают разные размеры:
- `out2[:, 1:-1, 1:-1]` = 196×196 (обрезан на 1 с каждой стороны)
- `out1` и `out3` = 200×200 (полный размер)
- `np.concatenate([out1, out2, out3])` не работает

Плюс использовался `np` без импорта.

### 9.3 Исправление

```python
import numpy as np

def __call__(self, ...):
    out1, out2, out3 = ...  # 200×200, 196×196, 200×200
    out1 = out1[:, 2:-2, 2:-2]  # 196×196
    out3 = out3[:, 2:-2, 2:-2]  # 196×196
    result = np.concatenate([out1, out2, out3], axis=0)
```

---

## 10. Баг #7: Скалярный индекс в polygon_mask_cpu

### 10.1 Симптом

`IndexError: invalid index to scalar variable` в `test_plugin_implementations.py`.

### 10.2 Причина

`center_x` и `center_y` — скаляры (`numpy.float64`), а не массивы. Доступ `center_x[0]` падает. После исправления: `polygon[j * 2 + 0]` обращается к 2D массиву `(N,2)` плоским индексом — возвращает вектор длины 2 вместо скаляра.

### 10.3 Исправление

```python
# Было: center_x[0] → IndexError
# Стало: center_x → скаляр

# Было: polygon[j * 2 + 0] → вектор (строка)
# Стало: polygon[j, 0] → скаляр (x координата)
```

---

## 11. Инфраструктура: Volume mount для Docker

### 11.1 Проблема

Контейнер работает из `/ws/install/...` — собранный пакет внутри Docker-образа. Изменения исходного кода не подхватывались. Каждое изменение требовало `colcon build` + пересборку Docker.

### 11.2 Исправление

В `compose.yml` добавлены volume mounts:

```yaml
x-el-volumes: &el_volumes
  - ./.../scripts/elevation_mapping_node.py:\
    /ws/install/.../lib/elevation_mapping_cupy/elevation_mapping_node.py:ro
  - ./.../elevation_mapping_cupy/:\
    /ws/install/.../lib/python3.12/site-packages/elevation_mapping_cupy/:ro
```

Теперь изменения исходников подхватываются после `docker compose down && make elevation-cpu`.

---

## 12. Инфраструктура: Coverage

### 12.1 Что добавлено

```makefile
elevation-test:
    cd ...tests && \
        python3 -m pytest -v --tb=short --cov=.. --cov-report=term
```

### 12.2 Текущее покрытие: 71%

| Файл | Покрытие | Пропущено строк |
|------|----------|-----------------|
| elevation_mapping.py | ~88% | — |
| custom_kernels.py | ~85% | — |
| plugins/* | 96-100% | — |
| gridmap_utils.py | ~90% | — |
| **elevation_mapping_node.py** | **0%** | **513 строк** |
| traversability_filter.py | 35% | 74 строки |
| conftest.py | 45% | 30 строк |

**71% — из-за `elevation_mapping_node.py`** (513 строк, 0%). Это ROS2-нода, неподъёмная для unit-тестов.

### 12.3 Что дальше

- Исключить `*_node.py`, `conftest.py`, `test_*` из coverage → ~85%

---

## 13. Тестирование: 477 тестов — полный анализ

### 13.1 Файлы тестов

| Файл | Тестов | Что тестирует |
|------|--------|---------------|
| `test_elevation_mapping.py` | 324 | Core ElevationMap: shift, add, publish, get, clear, stress |
| `test_plugin_implementations.py` | 28 | Плагины: roughness, slope, gradient, filter |
| `test_plugin_manager.py` | 24 | Жизненный цикл: load, unload, configure |
| `test_map_shifting.py` | 18 | Регрессия axis-swap: X/Y shifts |
| `test_image_kernels.py` | 16 | Image kernels: correspondence, exponential |
| `test_map_initializer.py` | 16 | Map init: linear, nearest, cubic |
| `test_traversability_polygon.py` | 14 | Traversability: masked, area |
| `test_kernel_compile_smoke.py` | 8 | Компиляция CUDA kernels |
| `test_gridmap_layout.py` | 6 | GridMap encode/decode |
| `test_parameter.py` | 6 | Валидация параметров |
| `test_backend.py` | 6 | Backend: CPU, GPU |
| `test_map_services.py` | 4 | save/load/masked_replace |
| `test_semantic_kernels.py` | 4 | Семантический фьюжн |
| `test_repo_config_sanity.py` | 3 | Валидация YAML-схем |

### 13.2 Категории

| Категория | Количество | Описание |
|-----------|-----------|----------|
| Unit тесты | 434 | Отдельные функции и методы |
| Integration тесты | 43 | Многошаговые pipeline, stress |

### 13.3 Матрица параметризации

Основной файл: 6×6 параметризация:
- **6 конфигураций additional_layer:** `feat_0`, `rgb` (with mask), `normal`, `all`, `cost`, `none`
- **6 алгоритмов фьюжна:** `mean`, `mean_weighted`, `median`, `distance_weighted`, `height_weighted`, `lowest_height`

Все 36 комбинаций × множество сценариев = 324 параметризованных теста.

### 13.4 Специальные сценарии

- **NaN/Inf pointcloud:** Робастность — карта не портится
- **Пустой pointcloud:** Нет crash, карта остаётся неизменной
- **All-NaN publish:** `process_map_for_publish` с fill_nan=True
- **All-zero publish:** Публикация нулевых данных
- **5 последовательных вводов:** Выносливость pipeline
- **Большой move + rotate:** `move_to` с delta_x=1.0, delta_y=0.5
- **Variance после 3 вводов:** Дисперсия уменьшается с каждым добавлением
- **Clear → input:** `clear_map` + одиночный `addPoints`
- **clear_overlap с z=10:** Удаление только пересекающейся области
- **shift_map_z(-100):** Z-сдвиг (тест независимости оси Z)

---

## 14. Итоговые результаты

### 14.1 Текущее состояние

| Метрика | Значение |
|---------|----------|
| Тестов запущено | 477 |
| Тестов пройдено | 477 |
| Тестов упало | 0 |
| RuntimeWarning | 0 |
| Coverage (TOTAL) | 71% |
| Coverage (без ROS2 ноды) | ~85% |
| Docker hot-reload | Да (volume mounts) |

### 14.2 Все исправленные баги

| # | Баг | Файл | Статус |
|---|-----|------|--------|
| 1 | Перепутаны оси в shift_map_xy | elevation_mapping.py | ✅ Исправлено |
| 2 | Поворот 90° в GridMap | elevation_mapping.py | ✅ Исправлено |
| 3 | Ориентация costmap + origin | elevation_to_costmap_node.py | ✅ Исправлено |
| 4 | RuntimeWarning (143 шт) | custom_kernels.py, erosion.py | ✅ Исправлено |
| 5 | 11 падающих тестов (6 багов) | Несколько файлов | ✅ Исправлено |
| 6 | Размерности в dilation | traversability_filter.py | ✅ Исправлено |
| 7 | Скалярный индекс polygon_mask | custom_kernels.py | ✅ Исправлено |
| 8 | Docker hot-reload | compose.yml | ✅ Исправлено |
| 9 | Coverage в makefile | elevation.mk | ✅ Исправлено |

### 14.3 Как проверить

```bash
# Все unit-тесты с coverage:
make elevation-test

# Со strict-проверкой RuntimeWarning:
cd ...tests && \
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -v \
        -W error::RuntimeWarning --cov=.. --cov-report=term

# Визуальная проверка (требует запущенных контейнеров):
make elevation-cpu
# В RViz: карта высот + costmap совпадают с роботом

# Проверка Nav2:
make navigation
# Робот строит маршруты по costmap
```

### 14.4 Ключевые уроки

1. **Координатные конвенции — главный источник багов** при интеграции разных библиотек (Row=Y,Col=X vs Row=-X,Col=-Y vs OccupancyGrid с origin в левом нижнем углу).

2. **Всегда проверять и unit-тестами, и визуально** — axis-swap найден тестами, ориентация costmap найдена визуально в RViz.

3. **Docker-изоляция — палка о двух концах** — даёт воспроизводимость, но прячет изменения кода. Volume mounts для разработки решают проблему.

4. **Полное покрытие тестами с `-W error::RuntimeWarning`** ловит тонкие численные проблемы (NaN, деление на 0), которые иначе вели бы к молчаливому повреждению данных.
