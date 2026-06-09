# План декомпозиции: покрытие 90% тестами `elevation_mapping_cupy`

**Текущее покрытие**: ~15-20% (источник: 4626 строк)
**Цель**: 90%

---

## Фаза 0 — Инфраструктура тестирования

| # | Задача | Файл | Ожидаемый результат |
|---|--------|------|---------------------|
| 0.1 | Создать `conftest.py` с общими фикстурами (`elmap`, `param`, `gpumock`) | `tests/conftest.py` | Переиспользуемые fixture для всех тестов |
| 0.2 | Создать `.coveragerc` с настройками покрытия (исключить `kk.py`, `build/`, `install/`) | `.coveragerc` | `kk.py` (1240 ст. мёртвого кода) исключён из замера |
| 0.3 | Обновить `CMakeLists.txt` — добавить `--cov` для всех новых тестов | `CMakeLists.txt` | Все тесты регистрируются с флагом coverage |
| 0.4 | Создать `pytest.ini` с маркерами и настройками | `pytest.ini` | Единая конфигурация pytest |

---

## Фаза 1 — Плагины (самый большой пробел: ~886 строк, ~0%)

| # | Задача | Файл теста | Таргет | Приоритет |
|---|--------|------------|--------|-----------|
| 1.1 | **PluginManager**: инициализация из YAML, загрузка плагинов, резолвинг имён/индексов | `tests/test_plugin_manager.py` | `plugin_manager.py` ~289 строк | 🔴 High |
| 1.2 | **PluginBase**: `get_layer_data()`, выделение/проверка массивов, `__call__` type-check | `tests/test_plugin_manager.py` | `plugin_manager.py` (PluginBase) | 🔴 High |
| 1.3 | **CostFunction**: комбинация slope/roughness/elevation_diff → cost, NaN propagation | `tests/test_plugins.py` | `cost_function.py` ~92 строк | 🔴 High |
| 1.4 | **SurfaceGradient**: np.gradient → slope angle, fill_value handling | `tests/test_plugins.py` | `surface_gradient.py` ~50 строк | 🔴 High |
| 1.5 | **Roughness**: uniform filter → local stddev, edge handling | `tests/test_plugins.py` | `roughness.py` ~53 строк | 🔴 High |
| 1.6 | **Erosion**: OpenCV morphological erosion, kernel config | `tests/test_plugins.py` | `erosion.py` ~94 строк | 🔴 High |
| 1.7 | **Inpainting**: OpenCV inpainting (Telea/NS), invalid cell filling | `tests/test_plugins.py` | `inpainting.py` ~70 строк | 🔴 High |
| 1.8 | **SmoothFilter**: two-pass uniform filter, size params | `tests/test_plugins.py` | `smooth_filter.py` ~45 строк | 🔴 High |
| 1.9 | **MaxLayerFilter**: max/min over layers, threshold/scale combos | `tests/test_plugins.py` | `max_layer_filter.py` ~92 строк | 🔴 High |
| 1.10 | **MaxFilter**: iterative dilation (CPU + CUDA path отдельно), GPU mock | `tests/test_plugins.py` | `max_filter.py` ~126 строк | 🔴 High |
| 1.11 | **MinFilter**: iterative min inpainting (CPU + CUDA path), GPU mock | `tests/test_plugins.py` | `min_filter.py` ~129 строк | 🔴 High |
| 1.12 | **RobotCentricElevation**: body-frame transform, NaN rows | `tests/test_plugins.py` | `robot_centric_elevation.py` ~135 строк | 🔴 High |

---

## Фаза 2 — Ядро (elevation_mapping.py: пробелы ~65% методов)

| # | Задача | Файл теста | Таргет | Приоритет |
|---|--------|------------|--------|-----------|
| 2.1 | `get_center_position()` — пустая/заполненная карта, граничные случаи | `tests/test_elevation_mapping.py` | `elevation_mapping.py:161-168` | 🟡 Medium |
| 2.2 | `shift_map_z()` — сдвиг вверх/вниз, переполнение слоёв | `tests/test_map_shifting.py` (дополнить) | `elevation_mapping.py:264-274` | 🟡 Medium |
| 2.3 | `clear_overlap_map()` — полное/частичное пересечение | `tests/test_elevation_mapping.py` | `elevation_mapping.py:420-437` | 🟡 Medium |
| 2.4 | `get_additive_mean_error()` — точность вычислений | `tests/test_elevation_mapping.py` | `elevation_mapping.py:439-445` | 🟡 Medium |
| 2.5 | `update_upper_bound_with_valid_elevation()` — корректность upper_bound | `tests/test_elevation_mapping.py` | `elevation_mapping.py:455-459` | 🟡 Medium |
| 2.6 | `process_map_for_publish()` — подготовка слоёв к публикации | `tests/test_elevation_mapping.py` | `elevation_mapping.py:521-540` | 🟡 Medium |
| 2.7 | Геттеры слой-за-раз: `get_elevation()`, `get_variance()`, `get_traversability()`, `get_time()`, `get_upper_bound()`, `get_is_upper_bound()` | `tests/test_elevation_mapping.py` | `elevation_mapping.py:542-614` | 🔴 High |
| 2.8 | `xp_of_array()` — определение backend массива (cupy/numpy) | `tests/test_elevation_mapping.py` | `elevation_mapping.py:616-628` | 🟢 Low |
| 2.9 | `copy_to_cpu()` — GPU→CPU transfer, stream sync | `tests/test_elevation_mapping.py` | `elevation_mapping.py:630-644` | 🟡 Medium |
| 2.10 | `get_normal_ref()` / `get_normal_maps()` — нормальные карты | `tests/test_elevation_mapping.py` | `elevation_mapping.py:778-811` | 🟡 Medium |
| 2.11 | `get_layer()` — внутренний доступ по индексу слоя | `tests/test_elevation_mapping.py` | `elevation_mapping.py:813-837` | 🟡 Medium |
| 2.12 | `list_layers()` — корректный порядок и имена слоёв | `tests/test_elevation_mapping.py` | `elevation_mapping.py:926-935` | 🟢 Low |
| 2.13 | `export_layers()` — экспорт в numpy dict, проверка значений | `tests/test_elevation_mapping.py` | `elevation_mapping.py:937-945` | 🟡 Medium |
| 2.14 | Приватные хелперы: `_resolve_layer_target()`, `_validate_geometry_against_shape()`, `_compute_overlap_indices()`, `_map_extent_from_slices/mask()`, `_invalidate_caches()` | `tests/test_elevation_mapping.py` | `elevation_mapping.py:1066-1189` | 🟡 Medium |
| 2.15 | Координатные трансформации: `_transform_to_grid_map_coordinate_convention()` / `_transform_to_elevation_mapping_coordinate_convention()` | `tests/test_elevation_mapping.py` | `elevation_mapping.py:731-776` | 🔴 High |

---

## Фаза 3 — Ядерные модули (kernels, backend, utilities)

| # | Задача | Файл теста | Таргет | Приоритет |
|---|--------|------------|--------|-----------|
| 3.1 | **CPU fallbacks**: `add_points_cpu`, `error_counting_cpu`, `average_cpu`, `dilation_filter_cpu`, `normal_filter_cpu`, `polygon_mask_cpu` | `tests/test_cpu_kernels.py` | `custom_kernels.py` ~1103 строк (CPU-пути) | 🔴 High |
| 3.2 | **Semantic kernels**: dispatch всех 9 функций (`sum_kernel`, `bayesian_inference_kernel`, `class_average_kernel`, `class_max_kernel`, `average_kernel`, `alpha_kernel`, `add_color_kernel`, `color_average_kernel`, `sum_compact_kernel`) | `tests/test_semantic_kernels.py` | `custom_semantic_kernels.py` ~557 строк | 🔴 High |
| 3.3 | **Image kernels**: dispatch 4 функций (`image_to_map_correspondence_kernel`, `average_correspondences_to_map_kernel`, `exponential_correspondences_to_map_kernel`, `color_correspondences_to_map_kernel`) | `tests/test_image_kernels.py` | `custom_image_kernels.py` ~510 строк | 🟡 Medium |
| 3.4 | **backend.py**: `_detect_cuda()` (GPU/noGPU/error), `get_stream()`, `asnumpy()` (identity+cupy) | `tests/test_backend.py` | `backend.py` ~49 строк | 🔴 High |
| 3.5 | **map_initializer.py**: `points_initializer()` — linear/cubic/nearest, NaN fallback, пустые точки | дополнить `test_elevation_mapping.py` | `map_initializer.py` ~85 строк | 🟡 Medium |
| 3.6 | **traversability_filter.py**: `__call__` для Torch/Chainer/NumPy, conv bank, weight loading | `tests/test_traversability_filter.py` | `traversability_filter.py` ~167 строк | 🔴 High |
| 3.7 | **traversability_polygon.py**: `is_traversable()`, `calculate_area()`, `calculate_untraversable_polygon()`, `transform_to_map_position()`, `transform_to_map_index()` | дополнить `test_elevation_mapping.py` | `traversability_polygon.py` ~84 строк | 🟡 Medium |
| 3.8 | **gridmap_utils.py**: достичь 100% — edge cases (пустые массивы, нулевые размеры, single-row/col) | дополнить `test_gridmap_layout.py` | `gridmap_utils.py` ~70 строк | 🟢 Low |
| 3.9 | **parameter.py**: достичь 90% — `set_value` с невалидными типами, `update()` после изменений | дополнить `test_parameter.py` | `parameter.py` ~352 строк | 🟢 Low |

---

## Фаза 4 — Интеграционные / End-to-End

| # | Задача | Файл теста | Таргет | Приоритет |
|---|--------|------------|--------|-----------|
| 4.1 | **Пайплайн plugins**: полный цикл input → plugin pipeline → output | `tests/test_plugins.py` | Все plugin + `plugin_manager.py` | 🟡 Medium |
| 4.2 | **ElevationMap stress**: крайние разрешения (0.01, 10.0), большие сдвиги, вращения на 90°/180° | `tests/test_elevation_mapping.py` | `elevation_mapping.py` | 🟡 Medium |
| 4.3 | **NaN/Inf propagation**: точки с NaN, Inf, Out-of-bounds в разных комбинациях | `tests/test_elevation_mapping.py` | `elevation_mapping.py` | 🟡 Medium |
| 4.4 | **Семантическая фузия**: все 6 алгоритмов (average, color, class_average, class_bayesian, class_max, bayesian_inference) с проверкой результатов | `tests/test_elevation_mapping.py` | `elevation_mapping.py` | 🟡 Medium |

---

## Сводка усилий

| Фаза | Файлов тестов | Приблизительно тестов | Ожидаемый прирост покрытия |
|------|---------------|-----------------------|---------------------------|
| 0 — Инфраструктура | 4 новых | — | 0% |
| 1 — Плагины | 2 новых | ~60 unit | ~20% |
| 2 — Ядро | 2 дополнено | ~40 новых | ~20% |
| 3 — Ядерные модули | 4 новых + 3 дополнено | ~70 новых | ~25% |
| 4 — Интеграционные | 3 дополнено | ~20 новых | ~10% |
| **Итого** | **~6 новых + ~5 дополнено** | **~190 тестов** | **~75% → 90%** |

---

## Исключения из coverage (`.coveragerc`)

```ini
[run]
omit =
    */kk.py
    */build/*
    */install/*
    */log/*
    listener_test.py

[report]
exclude_lines =
    pragma: no cover
    raise NotImplementedError
    if __name__ == "__main__":
```
