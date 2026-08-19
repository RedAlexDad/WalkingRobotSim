# Анализ уровня навыков программиста — WalkingRobotSim

**Дата:** 2026-05-28  
**Исключена из анализа:** `quadropted_controller` (исходная Python-реализация, мигрирована на C++)

---

## Итоговая оценка: **Senior**

Программист уверенно демонстрирует уровень **Senior (старший разработчик)**.  
Ниже — детальное обоснование по ключевым критериям.

---

## 1. Архитектурное мышление и организация проекта

Проект представляет собой ROS 2 монорепозиторий, состоящий из **~10 активных ROS-пакетов**, объединённых единой Makefile-инфраструктурой (**~1135 строк** в 10 `.mk` файлах) и Docker-сборкой.

| Компонент | Назначение | Уровень сложности |
|-----------|-----------|-------------------|
| `quadropted_controller_cpp` | Gait-контроллер на C++17 с Eigen, тестами, бенчмарками | **Высокий** |
| `elevation_mapping_cupy` | GPU-ускоренное построение карт высот (CuPy, CUDA) | **Очень высокий** |
| `plane_segmentation` | Планарная сегментация (CGAL, RANSAC, OpenCV) | **Очень высокий** |
| `gazebo_sim` | Оркестрация симуляции (Gazebo, Nav2, ros2_control) | **Средний-высокий** |
| `makefiles/` | 10 модулей Makefile для сборки/деплоя/тестов | **Средний** |
| `docker/` | 10-стадийный Multi-stage Docker-образ | **Высокий** |
| `tests/` | Кросс-валидация Python vs C++, бенчмарки | **Средний-высокий** |

**Аргументация:**  
Проект спроектирован как модульная, расширяемая система с чёткими границами ответственности между пакетами. Это не «скрипт для одной задачи», а инженерная платформа — признак архитектурного опыта, характерного для Senior.

---

## 2. Миграция Python → C++ (ключевой аргумент)

В `quadropted_controller_cpp` видна осознанная и профессионально выполненная миграция:

- **Выбор C++17** — современный стандарт, достаточный для эффективной работы с Eigen и ROS 2.
- **Полное покрытие тестами** — каждое ядро (FK, IK, PID, odometry, gait) покрыто **gmock-тестами**.
- **Benchmark** — отдельный исполняемый файл для сравнения производительности.
- **Кросс-валидация** — `tests/test_python_vs_cpp.py` запускает обе реализации и сравнивает численные результаты с заданной точностью.
- **Структура CMake** — библиотека + исполняемые узлы + тесты + бенчмарк с правильным экспортом целей.

Это не «переписал на C++ потому что надо», а системный подход: измерение, валидация корректности, поддержка обеих реализаций до полной замены. Именно так поступает Senior, а не Junior.

---

## 3. Глубина знаний C++

Примеры из `quadropted_controller_cpp/src/controllers/pid_controller.cpp`:

```cpp
// Антивиндап-защита интегрального члена
i_term_[i] += error[i] * step;
if (i_term_[i] < -max_i_)
    i_term_[i] = -max_i_;
else if (i_term_[i] > max_i_)
    i_term_[i] = max_i_;

// Защита от деления на ноль при малом шаге
if (step < 1e-6) return {0.0, 0.0};
```

Пример из `forward_kinematics.cpp`:
```cpp
// Сложная кинематика через гомогенные преобразования
Eigen::Matrix4d T_total = T_base * T_hip * T_thigh * T_thigh_t * T_calf * T_calf_t * T_foot;
```

Используются:
- Пространства имён (`quadropted`)
- `std::array` для фиксированных векторов
- `Eigen::Matrix`, `Eigen::Vector` для линейной алгебры
- Лямбда-функции
- Исключения с осмысленными сообщениями
- `const`-корректность, передача по ссылке, `reserve()` для векторов

Это уровень Senior, хорошо знающего современный C++.

---

## 4. GPU-вычисления и Python

`elevation_mapping_cupy` демонстрирует:

- **CuPy** для GPU-ускорения с Custom CUDA-ядрами
- **Управление памятью GPU**: `cp.cuda.MemoryPool(cp.cuda.malloc_managed)`
- **Плагинная система**: `PluginManager` с динамической загрузкой фильтров
- **1234 строки** основного модуля (`elevation_mapping.py`) с продакшн-качеством
- **Типизированный Python**: полные аннотации типов (PEP 484)
- **Поддержка CPU fallback** при отсутствии GPU

Всё это требует глубокого понимания не только Python, но и GPU-архитектуры, управления памятью и численных методов.

---

## 5. Интеграционное тестирование

Документация в `elevation_mapping_cupy/AGENTS.md` содержит **профессиональное описание отладки DDS**:
- Анализ проблем обнаружения DDS (FastDDS Shared Memory, CycloneDDS)
- Настройка `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`
- Использование `add_ros_isolated_launch_test` для уникальных ROS_DOMAIN_ID
- Диагностика QoS-несовместимости
- Исправление 41 упавшего теста (31 → 72 passing) с детальным описанием каждого фикса

Это не уровень Middle, знакомого с тестами «на уровне документации». Это практический боевой опыт Senior, который реально отлаживал распределённые системы ROS 2.

---

## 6. DevOps и инфраструктура

- **Docker**: многостадийная сборка из 10 этапов с кэшированием (`--mount=type=cache`)
- **Makefile-оркестрация**: 10 модулей, покрывающих сборку, деплой, запуск, тестирование, CI
- **Git-практики**: Conventional Commits, feature-ветки (`feat/elevation-mapping`, `benchmark-python-cpp`, `feat/rust-migration`)
- **CI**: GitHub Actions workflows, линтинг YAML/Python/C++

Senior-разработчик не пишет код в вакууме — он строит инфраструктуру вокруг него.

---

## 7. Междисциплинарность

Программист владеет как минимум **4 языками** на продакшн-уровне:
- **C++17** — основной контроллер
- **Python 3** — elevation mapping, YOLO, тесты
- **CUDA/CuPy** — GPU-ядра для карт высот
- **Bash** — Makefile-модули, скрипты развёртывания
- **Rust** (экспериментально) — попытка интеграции ROS 2 + Rust

Также демонстрирует понимание:
- **CGAL** (computational geometry) — планарная сегментация
- **Nav2** — навигационный стек ROS 2
- **Gazebo Sim** — физическая симуляция
- **YOLO / Ultralytics** — компьютерное зрение

---

## 8. Документирование и научная работа

Код сопровождается русскоязычной документацией:
- Научно-исследовательская работа (НИР) в формате LaTeX с Mermaid-диаграммами
- README на 331 строку с полным описанием архитектуры
- Внутренние AGENTS.md с детальными инструкциями по отладке

---

## Почему не Middle?

| Аспект | Middle | Senior (что видим здесь) |
|--------|--------|--------------------------|
| **Архитектура** | Один пакет, монолит | Много пакетов, разделение ответственности |
| **Миграция** | Просто перепишет | Измерит, перепишет, проверит кросс-валидацией |
| **Тесты** | Unit-тесты для ключевых модулей | Unit + integration + benchmark + DDS-отладка |
| **GPU** | Использует готовые библиотеки | Пишет кастомные CUDA-ядра, управляет памятью |
| **Инфраструктура** | Базовый Dockerfile | 10-стадийный Docker, Makefile-оркестрация, CI |
| **Документация** | Минимальная | Полная НИР + внутренние гайды |
| **Git** | Одна ветка | Feature-ветки, Conventional Commits |

---

## Вывод

Программист, написавший WalkingRobotSim (исключая старую `quadropted_controller`), обладает уровнем **Senior**.  

Проект демонстрирует:
- Системное архитектурное мышление
- Глубокое владение C++17 и Python с GPU-ускорением
- Профессиональные практики тестирования и CI/CD
- Опыт отладки сложных распределённых систем (ROS 2 DDS)
- Умение проектировать инфраструктуру вокруг кода (Docker, Make, CI)
- Способность к межъязыковой миграции с валидацией корректности

Миграция с Python на C++ в `quadropted_controller_cpp` — не просто «переписал», а инженерное решение: с замерами производительности, кросс-валидацией результатов и постепенным вытеснением старой реализации. Это поведение опытного инженера, который понимает цену производительности и корректности.

---

## Приложение: рекомендации по улучшению

### 🔴 High — Derivative kick в PIDController (`src/quadropted_controller_cpp/src/controllers/pid_controller.cpp`)

**Проблема:** D-член считается как `(error - last_error) / step`.
При резкой смене `set_desired()` (0 → 0.3 рад) `last_error_` хранит старую ошибку,
на следующем шаге derivative даёт **гигантский скачок** — классический derivative kick,
способный дестабилизировать робота.

**Рекомендация:** перейти на «derivative on measurement» (берётся производная от измерения,
а не от ошибки), либо пересчитывать `last_error_` внутри `set_desired()`:

```cpp
// ВАРИАНТ A: derivative on measurement (рекомендуется)
void PIDController::run_impl(double roll, double pitch, double /*current_time*/) {
    double error[2] = {desired_roll_pitch_[0] - roll,
                       desired_roll_pitch_[1] - pitch};
    double d_roll  = -(roll  - last_roll_pitch_[0]) / step;
    double d_pitch = -(pitch - last_roll_pitch_[1]) / step;
    // P term from error, D term from measurement
    result[i] = kp_ * error[i] + ki_ * i_term_[i] + kd_ * d_meas[i];
}

// ВАРИАНТ B: пересчёт last_error в set_desired (минимальное изменение)
void PIDController::set_desired(double roll, double pitch) {
    double prev_roll  = desired_roll_pitch_[0];
    double prev_pitch = desired_roll_pitch_[1];
    desired_roll_pitch_[0] = roll;
    desired_roll_pitch_[1] = pitch;
    // Скорректировать last_error, чтобы D не увидел скачка
    last_error_[0] -= (roll - prev_roll);
    last_error_[1] -= (pitch - prev_pitch);
}
```

**Приоритет:** 🔴 High —直接影响 стабильность контроллера в динамике.

---

### 🟡 Medium — Устаревший CMake (`include_directories`)

**Проблема:** `CMakeLists.txt` в `quadropted_controller_cpp` использует устаревший подход:

```cmake
find_package(Eigen3 REQUIRED)
include_directories(${EIGEN3_INCLUDE_DIR})
```

Это **pre-3.0 стиль**: не транзитивен, не масштабируется на большие проекты.

**Рекомендация:** перейти на modern CMake с целевым интерфейсом:

```cmake
find_package(Eigen3 REQUIRED)
target_link_libraries(${PROJECT_NAME} PUBLIC Eigen3::Eigen)
```

Плюс стоит поднять `cmake_minimum_required(VERSION 3.15)` — 3.8 не имеет
`FetchContent`, `target_precompile_headers`, современных генераторных выражений.

---

### 🟡 Medium — `ros2_rust_pubsub_test`: мёртвый код

**Проблема:** Папка `src/ros2_rust_pubsub_test` содержит только `target/`
(артефакты сборки Rust). Ни одного `.rs`-файла или `Cargo.toml`.

**Рекомендация:**
- **Вариант 1:** Удалить (`rm -rf src/ros2_rust_pubsub_test/target` и саму папку, если проект заброшен).
- **Вариант 2:** Создать `README.md` внутри папки с пояснением: что пытались сделать,
какой был результат, ссылка на issue/трекер.

---

### 🟢 Low — `elevation_mapping.py`: 1234 строки в одном файле

**Проблема:** Почти вся логика GPU-ускоренного elevation mapping — в одном файле.
Сложно навигировать, тестировать изолированные части, ревьювить.

**Рекомендация:** разбить на модули:
- `grid_geometry.py` — `GridGeometry` и расчёт границ
- `map_operations.py` — shift, merge, crop, get_position
- `elevation_mapping.py` — только класс `ElevationMap` как оркестратор
- `backend.py` (уже есть) — `xp`, `GPU_AVAILABLE`, memory pool

---

### 🟢 Low — `kk.py`: неинформативное имя

**Проблема:** `elevation_mapping_cupy/.../kernels/kk.py` — имя ничего не говорит
о содержимом (вероятно, семантические ядра для traversability).

**Рекомендация:** переименовать в `custom_semantic_kernels.py` или объединить
с одноимённым файлом, если они родственные.

---

### 🟢 Low — `math_utils.cpp`: пустой файл-заглушка

**Проблема:** Файл `src/quadropted_controller_cpp/src/utils/math_utils.cpp`
содержит только комментарий: «пустой, чтобы удовлетворить структуру проекта».
При этом он всё равно компилируется (пустой translation unit).

**Рекомендация:**
- Сделать math_utils header-only (все функции уже в соседних `.hpp`)
- Убрать `src/utils/math_utils.cpp` из списка исходников в `CMakeLists.txt`
- (Опционально) удалить файл физически

---

### 🟢 Low — Stale git-ветки

**Проблема:** В репозитории есть ветки, которые давно не используются:
`benchmark-python-cpp`, `feat/rust-migration`, `humble`, `ros2_rust_tutorial` и др.

**Рекомендация:**
```bash
# Ветки, которые можно удалить (слиты или abandoned):
git branch -d benchmark-python-cpp feat/rust-migration ros2_rust_tutorial

# Если нужна архивная копия — создать тег перед удалением:
git tag archive/rust-experiment feat/rust-migration
git branch -D feat/rust-migration
```

---

### Сводная таблица

| Prior. | Область | Проблема | Эффект от исправления |
|--------|---------|----------|-----------------------|
| 🔴 H | `pid_controller.cpp` | Derivative kick | Стабильность контроллера при смене уставки |
| 🟡 M | `CMakeLists.txt` | Old-style `include_directories` | Чистота зависимостей, транзитивность |
| 🟡 M | `ros2_rust_pubsub_test` | Мёртвый код / только артефакты | Порядок в репозитории |
| 🟢 L | `elevation_mapping.py` | 1234 строки — монолит | Удобство поддержки и тестирования |
| 🟢 L | `kk.py` | Неинформативное имя | Читаемость |
| 🟢 L | `math_utils.cpp` | Пустой файл | Минус пустой compilation unit |
| 🟢 L | Git-ветки | Stale branches | Порядок в VCS |
