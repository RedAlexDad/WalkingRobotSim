# Тестирование C++

## Описание

Пакет `quadropted_controller_cpp` использует **Google Mock** для модульного и интеграционного тестирования, а также **Google Benchmark** для замеров производительности.

## Инфраструктура

### Фреймворки

| Фреймворк | Назначение | Файлы |
|-----------|------------|-------|
| **Google Mock** | Модульные и интеграционные тесты | `test/*.cpp` (12 файлов) |
| **Google Benchmark** | Замеры производительности | `benchmark/benchmark.cpp` |

### Конфигурация сборки

В `CMakeLists.txt`:

```cmake
# Тесты
ament_add_gmock(test_rotation_matrices test/test_rotation_matrices.cpp)
ament_add_gmock(test_homogeneous_transforms test/test_homogeneous_transforms.cpp)
# ... ещё 10 тестов

# Бенчмарк (standalone, без ROS зависимостей)
add_executable(benchmark benchmark/benchmark.cpp)
target_link_libraries(benchmark ${BENCHMARK_LIBRARIES} quadropted_controller_cpp)
```

### Запуск тестов

```bash
# Из корня проекта
make test-cpp

# Из workspace
colcon test --packages-select quadropted_controller_cpp
colcon test-result --verbose

# Бенчмарк
./build/quadropted_controller_cpp/benchmark
```

## Модульные тесты (Google Mock)

### 1. test_rotation_matrices.cpp

**Что тестирует:** `rotx`, `roty`, `rotz`, `rotxyz`

| Тест | Описание |
|------|----------|
| Identity | `rotxyz(0, 0, 0)` = единичная матрица |
| Single axis | Отдельные оси X, Y, Z |
| Combined | Комбинация всех трёх осей |
| Python equivalence | **Совпадение с Python для 10 наборов углов** |
| Orthogonality | `R × Rᵀ ≈ I` |
| Determinant | `det(R) ≈ 1` |

**Пример:**
```cpp
TEST(RotationMatrices, PythonEquivalence) {
    // 10 наборов углов
    std::vector<std::tuple<double, double, double>> test_cases = {
        {0.0, 0.0, 0.0},
        {0.1, 0.2, 0.3},
        {-0.5, 0.3, 0.1},
        // ...
    };
    
    for (auto [roll, pitch, yaw] : test_cases) {
        auto R_cpp = quadropted::rotxyz(roll, pitch, yaw);
        // Сравнить с Python rotxyz
        EXPECT_TRUE(R_cpp.isApprox(R_python, 1e-10));
    }
}
```

### 2. test_homogeneous_transforms.cpp

**Что тестирует:** `homog_transxyz`, `homog_transform`, `homog_transform_inverse`

| Тест | Описание |
|------|----------|
| Translation only | Чистая трансляция |
| Translation + rotation | Трансляция + вращение |
| Inverse | `M × M⁻¹ ≈ I` |

### 3. test_fk.cpp

**Что тестирует:** Forward Kinematics

| Тест | Описание |
|------|----------|
| Smoke test | FK для 12 нулевых углов → 4 позиции |
| Known angles | Проверка для известных углов |

### 4. test_ik.cpp

**Что тестирует:** Inverse Kinematics

| Тест | Описание |
|------|----------|
| Python equivalence | **IK углы совпадают с Python** |
| Output size | 12 углов на выходе |
| Range | Диапазон углов < 2π |

### 5. test_odometry.cpp

**Что тестирует:** `OdometryState`, `update_odometry`

| Тест | Описание |
|------|----------|
| append_delta | Добавление дельты в очередь |
| average_delta | Среднее дельт в окне |
| reset | Полный сброс состояния |
| update_odometry no contacts | Обновление без контактов (dead reckoning) |

### 6. test_pid.cpp

**Что тестирует:** `PIDController`

| Тест | Описание |
|------|----------|
| Output size | Возвращает 2 элемента (roll, pitch) |

### 7. test_gait.cpp

**Что тестирует:** `GaitController`

| Тест | Описание |
|------|----------|
| phase_ticks | `[2, 9, 2, 9]` для Trot |
| contacts size | Размер вектора контактов = 4 |

### 8. test_message_builders.cpp

**Что тестирует:** `build_odometry_data`, `build_tf_data`

| Тест | Описание |
|------|----------|
| OdometryData | Все поля заполнены корректно |
| TFData | Frame IDs, позиция, ориентация |

### 9. test_cross_validation.cpp

**Что тестирует:** Комплексная кросс-валидация с Python

| Тест | Описание |
|------|----------|
| TrotGait | **Совпадение позиций стоп с Python** |
| TrotSwing | **Совпадение swing траекторий** |
| RestController | **Совпадение stance позиций** |
| IK | **Совпадение углов суставов** |
| FK/IK roundtrip | FK(IK(positions)) ≈ positions |

### 10. test_base_link_roll.cpp

**Что тестирует:** `rotxyz` с акцентом на roll

| Тест | Описание |
|------|----------|
| Identity | `rotxyz(0, 0, 0)` = I |
| 45° roll | Поворот на 45° вокруг X |
| Python equivalence | **Совпадение с Python** |
| Orthogonality | `R × Rᵀ ≈ I` |
| Determinant | `det(R) = 1` |
| ... | Всего 10 тестов |

### 11. test_ik_with_roll.cpp

**Что тестирует:** IK с учётом крена

| Тест | Описание |
|------|----------|
| zero_roll | IK без крена |
| roll=45° | IK с креном 45° |
| roundtrip | IK(FK(angles)) ≈ angles |
| symmetry | Симметрия левых/правых ног |
| negative_roll | Отрицательный крен |
| ... | Всего 8 тестов |

### 12. test_step_trot.cpp

**Что тестирует:** `TrotStanceController.step()`

| Тест | Описание |
|------|----------|
| z_convergence | Сходимость по Z к целевой высоте |
| forward_motion | Движение вперёд при команде скорости |
| yaw_rotation | Поворот при команде yaw_rate |
| Python equivalence | **Совпадение с Python** |
| ... | Всего 8 тестов |

## Бенчмарки (Google Benchmark)

### Файлы

- `benchmark/benchmark.cpp`

### Конфигурация

- **Итерации:** 10000
- **Режим:** Standalone (без ROS)
- **Метрика:** Среднее время на операцию (нс)

### Измеряемые операции

| Операция | Компонент | Описание |
|----------|-----------|----------|
| `GaitController.contacts()` | GaitController | Вычисление вектора контактов |
| `GaitController.subphase_ticks()` | GaitController | Тики текущей подфазы |
| `TrotSwingController.swing_height()` | TrotSwing | Высота подъёма ноги |
| `TrotSwingController.next_foot_location()` | TrotSwing | Следующая позиция (swing) |
| `TrotSwingController.raibert_touchdown()` | TrotSwing | Точка приземления |
| `TrotStanceController.position_delta()` | TrotStance | Дельта позиции (stance) |
| `TrotStanceController.next_foot_location()` | TrotStance | Следующая позиция (stance) |
| `StandController.run()` | StandController | Шаг стойки |
| `ForwardKinematics.forward_kinematics_all_legs()` | FK | FK всех 4 ног |
| `RestController.step()` | RestController | Шаг покоя |
| `InverseKinematics.inverse_kinematics()` | IK | Полный IK |
| `PIDController.run()` | PIDController | Шаг PID |
| `Trot Step (full cycle)` | TrotGait | Полный цикл Trot (stance + swing для 4 ног) |

### Пример результатов

| Операция | C++ (нс) | Python (нс) | Ускорение |
|----------|----------|-------------|-----------|
| FK all legs | ~500 | ~15000 | 30× |
| IK | ~800 | ~20000 | 25× |
| Trot step | ~1200 | ~35000 | 29× |
| PID run | ~50 | ~2000 | 40× |

*(Точные значения зависят от аппаратного обеспечения)*

### Запуск бенчмарка

```bash
# Сборка
make build

# Запуск
./build/quadropted_controller_cpp/benchmark

# Или через Makefile
make benchmark-cpp
```

## Покрытие кода

### Компоненты с тестами

| Компонент | Модульные тесты | Кросс-валидация | Бенчмарк |
|-----------|-----------------|-----------------|----------|
| rotation_matrices | ✅ | ✅ | -- |
| homogeneous_transforms | ✅ | -- | -- |
| forward_kinematics | ✅ | ✅ | ✅ |
| inverse_kinematics | ✅ | ✅ | ✅ |
| odometry | ✅ | -- | -- |
| pid_controller | ✅ | ✅ | ✅ |
| gait_controller | ✅ | -- | ✅ |
| trot_stance | -- | ✅ | ✅ |
| trot_swing | -- | ✅ | ✅ |
| trot_gait | -- | ✅ | ✅ |
| rest_controller | -- | ✅ | ✅ |
| stand_controller | -- | -- | ✅ |
| message_builders | ✅ | -- | -- |

## Стратегия тестирования

### 1. Модульные тесты

Проверяют каждый компонент изолированно:
- Корректность матричных операций
- Граничные условия
- Ошибочные входные данные

### 2. Интеграционные тесты

Проверяют взаимодействие компонентов:
- FK → IK roundtrip
- Gait → Stance/Swing

### 3. Кросс-валидация (Python vs C++)

**Самый важный тип тестов:**

Подтверждает численную идентичность результатов:
```cpp
EXPECT_TRUE(cpp_result.isApprox(python_result, 1e-10));
```

**Тестируемые сценарии:**
- FK для одинаковых углов
- IK для одинаковых позиций
- Trot gait step для одинаковых команд
- Rest controller step
- Swing траектории

### 4. Бенчмарки

Замеры производительности для:
- Выявления узких мест
- Отслеживания регрессий
- Сравнения с Python

## Связанные документы

- [[Обзор C++ архитектуры]]
- [[Кинематика C++]]
- [[Контроллеры C++]]
- [[Кросс-валидация]]
- [[Производительность C++]]
- [[Сравнение Python vs C++]]
