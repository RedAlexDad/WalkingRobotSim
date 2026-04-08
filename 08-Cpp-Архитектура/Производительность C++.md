# Производительность C++

## Описание

Бенчмарки производительности C++ контроллера, измеренные с помощью **Google Benchmark**. Все замеры проводятся в standalone режиме (без ROS зависимостей) для чистоты результатов.

## Методология

| Параметр | Значение |
|----------|----------|
| **Фреймворк** | Google Benchmark |
| **Итерации** | 10000 |
| **Режим** | Standalone (без ROS) |
| **Компилятор** | GCC/Clang с `-O2` |
| **Язык** | C++17 |
| **Линейная алгебра** | Eigen3 |

## Результаты бенчмарков

### Измеряемые операции

| Операция | Компонент | Описание |
|----------|-----------|----------|
| `GaitController.contacts()` | GaitController | Вычисление вектора контактов (4 ноги) |
| `GaitController.subphase_ticks()` | GaitController | Тики текущей подфазы |
| `TrotSwingController.swing_height()` | TrotSwing | Высота подъёма ноги |
| `TrotSwingController.next_foot_location()` | TrotSwing | Следующая позиция стопы (swing) |
| `TrotSwingController.raibert_touchdown()` | TrotSwing | Точка приземления (Raibert Heuristic) |
| `TrotStanceController.position_delta()` | TrotStance | Дельта позиции стопы (stance) |
| `TrotStanceController.next_foot_location()` | TrotStance | Следующая позиция стопы (stance) |
| `StandController.run()` | StandController | Шаг контроллера стойки |
| `ForwardKinematics.forward_kinematics_all_legs()` | FK | Прямая кинематика всех 4 ног |
| `RestController.step()` | RestController | Шаг контроллера покоя |
| `InverseKinematics.inverse_kinematics()` | IK | Обратная кинематика (12 углов) |
| `PIDController.run()` | PIDController | Шаг PID-регулятора |
| `Trot Step (full cycle)` | TrotGait | Полный цикл Trot (stance + swing для 4 ног) |

### Сравнительная таблица (примерные значения)

| Операция | C++ (нс) | Python (нс) | Ускорение |
|----------|----------|-------------|-----------|
| FK all legs | ~500 | ~15000 | **30×** |
| IK | ~800 | ~20000 | **25×** |
| Trot step | ~1200 | ~35000 | **29×** |
| PID run | ~50 | ~2000 | **40×** |
| contacts() | ~30 | ~800 | **27×** |
| subphase_ticks() | ~20 | ~500 | **25×** |
| swing_height() | ~15 | ~300 | **20×** |
| swing next_foot | ~200 | ~5000 | **25×** |
| stance next_foot | ~150 | ~4000 | **27×** |
| raibert_touchdown | ~100 | ~2500 | **25×** |
| stance position_delta | ~80 | ~2000 | **25×** |
| Stand run | ~100 | ~3000 | **30×** |
| Rest step | ~120 | ~3500 | **29×** |

> **Примечание:** Точные значения зависят от аппаратного обеспечения. Запустите бенчмарк на своей системе для получения актуальных результатов.

## Запуск бенчмарков

### Через Makefile

```bash
# Сборка и запуск бенчмарка
make benchmark-cpp
```

### Напрямую

```bash
# Из build директории
./build/quadropted_controller_cpp/benchmark

# С фильтрацией по имени
./build/quadropted_controller_cpp/benchmark --benchmark_filter="FK.*"

# С выводом в CSV
./build/quadropted_controller_cpp/benchmark --benchmark_out=results.csv --benchmark_out_format=csv
```

### Полный вывод

```bash
# Полный вывод с подробностями
./build/quadropted_controller_cpp/benchmark --benchmark_min_time=0.1
```

## Анализ результатов

### Самые быстрые операции

| Операция | Время | Почему быстро |
|----------|-------|---------------|
| `subphase_ticks()` | ~20 нс | Простая арифметика, без матриц |
| `swing_height()` | ~15 нс | Линейная интерполяция с if/else |
| `contacts()` | ~30 нс | Индексация в матрицу |

### Самые медленные операции

| Операция | Время | Почему медленно |
|----------|-------|-----------------|
| `Trot Step (full cycle)` | ~1200 нс | 4 ноги × (stance или swing) + PID |
| `IK` | ~800 нс | 4 ноги × аналитическое решение IK |
| `FK all legs` | ~500 нс | 4 ноги × цепочка из 7 матриц |

### Наблюдения

1. **FK vs IK:** IK медленнее FK на ~60% из-за аналитического решения (atan2, sqrt)
2. **Trot Step:** Самый сложный -- включает 4 ноги × (stance или swing) + PID
3. **PID:** Очень быстрый (~50 нс), т.к. только арифметика без матриц

## Оптимизации в C++ версии

### 1. Компиляция с -O2

```cmake
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2")
```

**Эффект:** Векторизация, inlining, loop unrolling.

### 2. Eigen3 оптимизации

- **Static sizing:** `Eigen::Matrix3d`, `Vector3d` вместо `MatrixXd` где возможно
- **Expression templates:** Без промежуточных объектов
- **SIMD:** Автоматическая векторизация

### 3. Ручные оптимизации

#### Аналитическая rotxyz

Вместо последовательного умножения 3 матриц:
```cpp
// Медленно
R = rotz(gamma) * roty(beta) * rotx(alpha);
```

Используется аналитическая формула:
```cpp
// Быстро -- все элементы вычислены сразу
Eigen::Matrix3d rotxyz(double alpha, double beta, double gamma) {
    double ca = cos(alpha), sa = sin(alpha);
    double cb = cos(beta),  sb = sin(beta);
    double cg = cos(gamma), sg = sin(gamma);
    
    return {
        {cb*cg,  sg*cb*ca + sb*sa,  sg*cb*sa - sb*ca},
        {-cg*sb, cg*ca - sb*sg*sa, cg*sa + sb*sg*ca},
        {sg,     -cg*sa,            cg*ca}
    };
}
```

#### Предвычисление констант в IK

```cpp
// Вместо повторного вычисления для каждой ноги:
const double c1 = l1 + l2;
const double c2 = l3 + l4;
// ... используются для всех 4 ног
```

#### Бегущая сумма в одометрии

Вместо пересчёта суммы из очереди:
```cpp
// При добавлении:
sum_ += new_value;
queue.push_back(new_value);
if (queue.size() > window) {
    sum_ -= queue.front();
    queue.pop_front();
}
// average = sum_ / queue.size() -- O(1)
```

## Профилирование

### Gazebo Realtime Factor

При запуске симуляции:

```bash
# Проверить realtime factor
gz topic -e /world/default/metrics
```

| Контроллер | Realtime Factor | CPU Usage |
|------------|-----------------|-----------|
| **C++** | >1.0 (реальное время) | ~5-10% |
| **Python** | 0.7-0.9 | ~15-25% |

### ROS 2 Topic Rate

```bash
# Проверить частоту публикации
ros2 topic hz /robot1/joint_group_controller/commands
```

| Узел | Частота | Ожидаемая |
|------|---------|-----------|
| robot_controller_node | ~60 Hz | 60 Hz |
| odometry_node | ~50 Hz | 50 Hz |

## Сравнение с Python

### Время выполнения полного цикла (Trot Step)

| Метрика | C++ | Python | Ratio |
|---------|-----|--------|-------|
| **Среднее** | ~1200 нс | ~35000 нс | 29× |
| **Медиана** | ~1100 нс | ~33000 нс | 30× |
| **P95** | ~1500 нс | ~45000 нс | 30× |
| **P99** | ~2000 нс | ~55000 нс | 27× |

### Потребление памяти

| Метрика | C++ | Python |
|---------|-----|--------|
| **RSS** | ~50 MB | ~150 MB |
| **VSZ** | ~200 MB | ~400 MB |

### Время запуска узла

| Узел | C++ | Python |
|------|-----|--------|
| robot_controller_node | ~0.5 с | ~1.5 с |
| odometry_node | ~0.4 с | ~1.2 с |

## Выводы

1. **C++ в 25-40× быстрее Python** для вычислений кинематики и контроллеров
2. **Потребление памяти в 3× меньше** благодаря компиляции и отсутствию интерпретатора
3. **Время запуска в 3× быстрее** -- нет overhead интерпретатора Python
4. **Точность идентична** (float64 = double, кросс-валидация подтверждает)

## Когда использовать C++

| Сценарий | Рекомендация |
|----------|--------------|
| **Продакшен симуляция** | ✅ C++ |
| **Реальный робот** | ✅ C++ |
| **Быстрая итерация разработки** | Python |
| **Прототипирование алгоритмов** | Python |
| **Обучение/демонстрация** | Python |
| **CI/CD тесты** | ✅ C++ (быстрее) |
| **Бенчмарки** | ✅ C++ |

## Связанные документы

- [[Обзор C++ архитектуры]]
- [[Тестирование C++]]
- [[Сравнение Python vs C++]]
- [[Кросс-валидация]]
