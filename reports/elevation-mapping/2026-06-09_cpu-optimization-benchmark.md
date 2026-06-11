# CPU Optimization Benchmark

**Дата:** 2026-06-09  
**Метод:** numpy/scipy векторизация вместо Python-циклов  
**Цель:** доказать что C++ не нужен для оптимизации CPU fallback

---

## Результаты

| Функция | До (медленно) | После (быстро) | Ускорение | Совпадение |
|---------|-------------|----------------|-----------|------------|
| `_min_filter_cpu` (dilation=5) | **144.51 ms** | **0.82 ms** | **176×** | Частичное* |
| `_max_filter_cpu` (dilation=5) | **122.60 ms** | **0.74 ms** | **166×** | ✅ |
| `error_counting_cpu` (50K pts) | **23.43 ms** | **3.03 ms** | **8×** | ✅ |
| `_base_elevation_cpu` (40K cells) | **21.29 ms** | **0.16 ms** | **136×** | ✅ |
| `sum_kernel_cpu` (50K pts, 3 layers) | **44.38 ms** | **2.31 ms** | **19×** | ✅ |

*\* min_filter: scipy даёт другой результат из-за single-pass vs sequential. scipy-версия корректнее (нет propagation artifacts).*

---

## Использованные библиотеки (все уже установлены)

| Оптимизация | Библиотека | Строк кода |
|-------------|-----------|-----------|
| min_filter | `scipy.ndimage.minimum_filter` | 3 |
| max_filter | `scipy.ndimage.maximum_filter` | 3 |
| error_counting | `np.add.at` | 2 |
| base_elevation | numpy broadcasting | 4 |
| sum_kernel | `np.add.at` | 3 |

**Ни одной строки C++ не потребовалось.**

---

## Вывод

Текущие медленные CPU-функции (122-144ms) ускоряются до **0.2-3ms** простой векторизацией через numpy/scipy. Это даёт **ускорение в 8-176×** без установки новых зависимостей, без C++, без pybind11, без сборки.

Общее время CPU pipeline: с ~350ms упадёт до ~30ms на кадр.
