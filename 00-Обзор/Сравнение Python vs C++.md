# Сравнение Python vs C++

## Описание

Проект WalkingRobotSim содержит **две параллельные реализации** контроллера четырёхногого робота:
- **Python** -- оригинальная реализация (`quadropted_controller/`)
- **C++** -- высокопроизводительная версия (`quadropted_controller_cpp/`)

Обе реализации имеют **идентичную функциональность** и подтверждённую **численную точность** через кросс-валидацию.

## Архитектурные различия

| Аспект | Python | C++ |
|--------|--------|-----|
| **Язык** | Python 3 | C++17 |
| **Линейная алгебра** | NumPy, SciPy | Eigen3 |
| **Типы данных** | `np.ndarray`, `list` | `Eigen::MatrixXd`, `std::vector` |
| **Сборка** | Интерпретируемый | CMake + Ament, `-O2` |
| **Тестирование** | pytest (13 файлов) | Google Mock (12 файлов) |
| **Бенчмарки** | timeit | Google Benchmark |
| **ROS 2 клиент** | rclpy | rclcpp |

## Производительность

### Время выполнения операций

| Операция | Python (нс) | C++ (нс) | Ускорение |
|----------|-------------|----------|-----------|
| FK all legs | ~15,000 | ~500 | **30×** |
| IK | ~20,000 | ~800 | **25×** |
| Trot step | ~35,000 | ~1,200 | **29×** |
| PID run | ~2,000 | ~50 | **40×** |

### Потребление ресурсов

| Метрика | Python | C++ | Разница |
|---------|--------|-----|---------|
| **RSS память** | ~150 MB | ~50 MB | 3× меньше |
| **VSZ память** | ~400 MB | ~200 MB | 2× меньше |
| **Время запуска узла** | ~1.5 с | ~0.5 с | 3× быстрее |
| **Gazebo Realtime Factor** | 0.7-0.9 | >1.0 | Стабильнее |
| **CPU Usage** | 15-25% | 5-10% | 2-3× меньше |

### Частота работы

| Узел | Ожидаемая | Python | C++ |
|------|-----------|--------|-----|
| robot_controller | 60 Hz | ✅ 60 Hz | ✅ 60 Hz |
| odometry_node | 50 Hz | ✅ 50 Hz | ✅ 50 Hz |

## Точность вычислений

### Численная идентичность

| Компонент | Точность совпадения | Тест |
|-----------|---------------------|------|
| Rotation matrices | `1e-10` | `test_rotation_matrices.cpp` |
| Forward Kinematics | `1e-10` | `test_cross_validation.cpp` |
| Inverse Kinematics | `1e-10` | `test_cross_validation.cpp` |
| Trot Gait step | `1e-10` | `test_cross_validation.cpp` |
| Rest Controller | `1e-10` | `test_cross_validation.cpp` |
| Odometry | `1e-9` | `test_odometry.cpp` |

**Почему float64 = double:**
- Python: `np.float64` (64-бит IEEE 754)
- C++: `double` (64-бит IEEE 754)
- Идентичное представление чисел

## Преимущества и недостатки

### Python

| Преимущества | Недостатки |
|--------------|------------|
| Быстрая итерация разработки | Медленнее в 25-40× |
| Лёгкая отладка (интерпретатор) | Больше потребление памяти |
| Интерактивные ноутбуки | Зависимость от интерпретатора |
| Прототипирование алгоритмов | Сложнее деплой |
| Обучение и демонстрация | Меньше стабильность realtime |

### C++

| Преимущества | Недостатки |
|--------------|------------|
| В 25-40× быстрее | Дольше компиляция |
| Меньше потребление памяти | Сложнее отладка |
| Стабильный realtime factor | Дольше итерация разработки |
| Готов к реальному роботу | Строгая типизация |
| Меньше CPU overhead | |

## Когда использовать

### Python

| Сценарий | Причина |
|----------|---------|
| **Прототипирование** | Быстрая итерация, REPL |
| **Обучение** | Проще читать и понимать |
| **Демонстрация** | Лёгкий запуск без компиляции |
| **Jupyter notebooks** | Интерактивная визуализация |
| **Исследование алгоритмов** | Быстрое тестирование идей |

### C++

| Сценарий | Причина |
|----------|---------|
| **Продакшен симуляция** | Стабильный realtime |
| **Реальный робот** | Низкий latency |
| **CI/CD тесты** | Быстрое выполнение |
| **Бенчмарки** | Точные замеры |
| **Мультироботная система** | Меньше CPU на робота |

## Структура кода

### Пример: Матрицы вращения

**Python:**
```python
import numpy as np

def rotx(alpha):
    return np.array([
        [1, 0, 0],
        [0, np.cos(alpha), -np.sin(alpha)],
        [0, np.sin(alpha), np.cos(alpha)]
    ])
```

**C++:**
```cpp
#include <Eigen/Dense>

Eigen::Matrix3d rotx(double alpha) {
    Eigen::Matrix3d R;
    R << 1, 0, 0,
         0, std::cos(alpha), -std::sin(alpha),
         0, std::sin(alpha),  std::cos(alpha);
    return R;
}
```

### Пример: Прямая кинематика

**Python:**
```python
def forward_kinematics_all_legs(joint_angles):
    foot_positions = []
    for i in range(4):
        angles = joint_angles[i*3:(i+1)*3]
        foot = compute_leg_fk(angles, i)
        foot_positions.append(foot)
    return np.array(foot_positions)
```

**C++:**
```cpp
std::vector<Eigen::Vector3d> forward_kinematics_all_legs(
    const std::vector<double>& joint_angles) {
    std::vector<Eigen::Vector3d> foot_positions;
    foot_positions.reserve(4);
    for (int i = 0; i < 4; ++i) {
        std::vector<double> angles(joint_angles.begin()+i*3,
                                   joint_angles.begin()+(i+1)*3);
        foot_positions.push_back(compute_leg_fk(angles, i));
    }
    return foot_positions;
}
```

## Тестирование

### Python (pytest)

```bash
cd src/quadropted_controller
pytest test/ -v
```

13 файлов тестов, покрытие ~90%.

### C++ (Google Mock)

```bash
colcon test --packages-select quadropted_controller_cpp
colcon test-result --verbose
```

12 файлов тестов, покрытие ~95%.

### Кросс-валидация

Отдельные тесты подтверждают идентичность результатов:

```bash
# Из src/tests/
python test_python_vs_cpp.py
```

## Бенчмарки

### Python

```bash
cd src/tests
python benchmark_performance.py
python benchmark_cpp_vs_python.py
```

### C++

```bash
./build/quadropted_controller_cpp/benchmark
```

## Запуск

### Python

```bash
make gazebo-py
```

### C++

```bash
make gazebo-cpp
```

## Миграция с Python на C++

### Что изменилось

| Python | C++ |
|--------|-----|
| `np.array` | `Eigen::MatrixXd` |
| `R @ v` | `R * v` |
| `np.zeros((3,4))` | `Eigen::MatrixXd::Zero(3, 4)` |
| `np.cos()` | `std::cos()` |
| `list.append()` | `std::vector::push_back()` |

### Что осталось

- Алгоритмы
- Параметры контроллеров
- ROS 2 топики и сервисы
- Логика работы

## Связанные документы

- [[Обзор C++ архитектуры]]
- [[Обзор Python архитектуры]]
- [[Кросс-валидация]]
- [[Производительность C++]]
- [[Тестирование C++]]
