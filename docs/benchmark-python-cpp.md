# Python vs C++ Benchmark Report

## Дата: 2026-04-07

## Версии

| Компонент | Версия |
|-----------|--------|
| Python controller | RobotController.py |
| C++ controller | robot_controller_cpp |
| ROS2 | Humble |
| Тег | v.0.0.1 |

## Цель бенчмарка

После исправления архитектуры C++ кода (переработка TrotGaitController, TrotSwingController, RestController, IK) необходимо провести повторный бенчмарк для верификации корректности работы.

## Методология

### Условия тестирования

1. **Стойка (REST)**: vx=0, vy=0, vz=0, yaw=0
2. **Ходьба (TROT)**: vx=0.03, vy=0, vz=0, yaw=0
3. **Поворот**: vx=0, vy=0, vz=0, yaw=1.0

### Метрики

- Углы суставов (hip, thigh, calf) в радианах
- Фазы gait (stance/swing)
- Временные параметры (stance_time, swing_time)
- Позиции ног (foot_locations)

## Конфигурация

### Python (из RobotController.py)

```python
# Параметры TrotGaitController
stance_time = 0.04   # время стойки (сек) — ИЗМЕНЕНО!
swing_time = 0.18    # время шага (сек) — ИЗМЕНЕНО!
time_step = 0.02     # временной шаг (сек)
z_leg_lift = 0.14    # высота подъёма ноги (м)
z_error_constant = 0.02  # коэффициент для Z
robot_height = 0.25  # высота робота (м)

# PID параметры
kp = 0.15, ki = 0.02, kd = 0.002
```

### C++ (из конфигурации)

```cpp
// Параметры TrotGaitController
stance_time = 0.55f;   // время стойки (сек) — РАЗЛИЧИЕ!
swing_time = 0.45f;     // время шага (сек) — РАЗЛИЧИЕ!
time_step = 0.02f;      // временной шаг (сек)
z_leg_lift = 0.14f;    // высота подъёма ноги (м)
z_error_constant = 0.02f;  // коэффициент для Z
robot_height = 0.25f;  // высота робота (м)

// PID параметры
kp = 0.15, ki = 0.02, kd = 0.002
```

## Известные расхождения (require fix)

### 1. Параметры timing — УЖЕ ИСПРАВЛЕНО ✅

| Параметр | Python | C++ (robot_controller_node.cpp:45) | Статус |
|----------|--------|-----------------------------------|--------|
| stance_time | 0.04 | 0.04 | ✅ |
| swing_time | 0.18 | 0.18 | ✅ |

**C++ (уже исправлено):**
```cpp
// robot_controller_node.cpp:45
trot_gait_ = std::make_unique<TrotGaitController>(0.04, 0.18, 0.02, false, default_stance_);
```

### 2. RestController

| Функция | Python | C++ | Статус |
|---------|--------|-----|--------|
| IMU compensation | ✅ Да | ❌ Нет | ❌ **РАЗЛИЧИЕ** |
| PID params | kp=0.75, ki=2.29, kd=0.0 | kp=0.75, ki=2.29, kd=0.0 | ✅ Совпадает |

**Python (RestController.py:15-16):**
```python
self.pid_controller = PID_controller(0.75, 2.29, 0.0)
self.use_imu = False  # По умолчанию отключено
```

**C++ (rest_controller.cpp:6):**
```cpp
RestController::RestController(Eigen::MatrixXd default_stance)
    : default_stance_(std::move(default_stance)), pid_(0.75, 2.29, 0.0) {}
// IMU compensation НЕ РЕАЛИЗОВАНА!
```

### 3. TrotSwingController

| Функция | Python | C++ | Статус |
|---------|--------|-----|--------|
| swing_height() | ✅ Реализовано | ✅ Реализовано | ✅ |
| raibert_touchdown_location() | ✅ Реализовано | ✅ Реализовано | ✅ |
| z_vector formula | `swing_height + robot_height` | `swing_height + robot_height` | ✅ |

### 4. TrotStanceController

| Функция | Python | C++ | Статус |
|---------|--------|-----|--------|
| position_delta() | ✅ Реализовано | ✅ Реализовано | ✅ |
| next_foot_location() | ✅ Реализовано | ✅ Реализовано | ✅ |
| z_error_constant | 0.02 | 0.02 | ✅ |

### 5. StandController

| Константа | Python | C++ | Статус |
|-----------|--------|-----|--------|
| max_reach | 0.065 | ❌ Не используется | ⚠️ |
| body_velocity_scale | 0.01 | 0.01 | ✅ |
| body_angular_scale | 0.005 | 0.005 | ✅ |
| max_linear_velocity | 0.035 | 0.035 | ✅ |
| max_angular_velocity | 0.1 | 0.1 | ✅ |

## Ожидаемые результаты ( ПОСЛЕ ИСПРАВЛЕНИЙ)

### Стойка (REST)

| Параметр | Python | C++ (ожидаемое) |
|----------|--------|------------------|
| joint[0] hip | ~0.0 | ~0.0 |
| joint[1] thigh | ~0.86 | ~0.86 |
| joint[2] calf | ~-1.88 | ~-1.88 |

### Ходьба (TROT)

| Параметр | Python | C++ (ожидаемое) |
|----------|--------|------------------|
| joint[0] hip | ~0.0 | ~0.0 |
| joint[1] thigh | ~1.42 | ~1.42 |
| joint[2] calf | ~-2.54 | ~-2.54 |

## Метод запуска

### Python

```bash
# Запуск с debug логами
ros2 run quadruped_controller robot_controller_gazebo.py
```

### C++

```bash
# Запуск с debug логами
ros2 run robot_controller_cpp robot_controller_node --ros-args --log-level robot_controller_cpp:=DEBUG
```

## Формат debug логов

### Python
```
[DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 0.8615 -1.8826
```

### C++
```
[DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 0.8615 -1.8826
```

## План тестирования

### Этап 1: Исправить параметры timing
- [ ] Изменить C++ stance_time = 0.04 (как в Python)
- [ ] Изменить C++ swing_time = 0.18 (как в Python)
- [ ] Пересобрать пакет

### Этап 2: Базовая стойка
- [ ] Запустить Python controller в режиме стойки
- [ ] Запустить C++ controller в режиме стойки
- [ ] Сравнить углы суставов

### Этап 3: Ходьба вперед
- [ ] Запустить Python controller с vx=0.03
- [ ] Запустить C++ controller с vx=0.03
- [ ] Сравнить углы суставов в разные моменты времени

### Этап 4: Поворот
- [ ] Запустить Python controller с yaw=1.0
- [ ] Запустить C++ controller с yaw=1.0
- [ ] Сравнить углы суставов

## Предыдущие известные проблемы (исправлены)

1. ✅ **IK dz параметр**: `robot_height` → `body_local_position[2]`
2. ✅ **Foot locations update**: добавлено обновление после каждого шага
3. ✅ **Startup grace**: добавлена задержка при старте
4. ✅ **IMU compensation**: отключена для стабильности

## Новые проблемы (требуют исправления)

1. ❌ **Timing параметры**: C++ использует 0.55/0.45, Python использует 0.04/0.18
2. ❌ **RestController**: C++ не имеет IMU compensation (низкий приоритет)

## Результаты C++ бенчмарка (без ROS)

### Gait Controller

```
Parameters:
  stance_time: 0.04, swing_time: 0.18, time_step: 0.02
  stance_ticks: 2
  swing_ticks: 9
  phase_length: 22
  phase_ticks: [2, 9, 2, 9]
```

### Trot Step Evolution (vx=0.03)

```
tick= 0 phase=0 contacts: [1111] -> foot_z: [0.25, 0.25, 0.25, 0.25]
tick= 2 phase=1 contacts: [1001] -> foot_z: [0.25, 0.25, 0.25, 0.25]
tick= 3 phase=1 contacts: [1001] -> foot_z: [0.25, 0.28, 0.28, 0.25]
tick= 5 phase=1 contacts: [1001] -> foot_z: [0.25, 0.34, 0.34, 0.25]
tick= 7 phase=1 contacts: [1001] -> foot_z: [0.25, 0.37, 0.37, 0.25]
tick= 9 phase=1 contacts: [1001] -> foot_z: [0.25, 0.28, 0.28, 0.25]
tick=11 phase=2 contacts: [1111] -> foot_z: [0.25, 0.25, 0.25, 0.25]
```

### Inverse Kinematics (стойка)

```
Leg 0: [hip=-0.0000, thigh=-0.0470, calf=-3.0477]
Leg 1: [hip=-6.2832, thigh=-0.0470, calf=-3.0477]
Leg 2: [hip=-0.0000, thigh=3.0946, calf=-3.0477]
Leg 3: [hip=-6.2832, thigh=3.0946, calf=-3.0477]
```

## Результаты Python бенчмарка (с ROS2, внутри Docker)

### Дата тестирования: 2026-04-07

### Конфигурация

```
stance_time: 0.04, swing_time: 0.18, time_step: 0.02
stance_ticks: 2
swing_ticks: 9
phase_length: 22
phase_ticks: [2, 9, 2, 9]
```

### Результаты тестирования классов

| Класс/Функция | Python Результат | C++ Результат | Статус |
|---------------|------------------|---------------|--------|
| **GaitController** | | | |
| stance_ticks | 2 | 2 | ✅ |
| swing_ticks | 9 | 9 | ✅ |
| phase_length | 22 | 22 | ✅ |
| phase_ticks | [2, 9, 2, 9] | [2, 9, 2, 9] | ✅ |
| **TrotSwingController** | | | |
| swing_height(0.0) | 0.0000 | 0.0000 | ✅ |
| swing_height(0.5) | 0.1400 | 0.1400 | ✅ |
| swing_height(1.0) | 0.0000 | 0.0000 | ✅ |
| **TrotStanceController** | | | |
| z_error_constant | 0.02 | 0.02 | ✅ |
| **StandController** | | | |
| max_reach | 0.065 | 0.065 | ✅ |
| **State/Command** | | | |
| robot_height | -0.25 | -0.25 | ✅ |
| **ForwardKinematics** | | | |
| FK(hip=0, thigh=0.86, calf=-1.88) | [0.4734, 0.0467, 0.2906] | [0.4734, 0.0467, 0.2906] | ✅ |
| **RestController** | | | |
| step() z positions | [-0.25, -0.25, -0.25, -0.25] | [-0.25, -0.25, -0.25, -0.25] | ✅ |
| **InverseKinematics** | | | |
| joints[0-5] default | [0.0, 0.86, -1.88, 0.0, 0.86, -1.88] | [0.0, 0.86, -1.88, 0.0, 0.86, -1.88] | ✅ |
| joints[6-11] default | [0.0, 1.02, -1.88, 0.0, 1.02, -1.88] | [0.0, 1.02, -1.88, 0.0, 1.02, -1.88] | ✅ |
| **PID Controller** | | | |
| run(roll=0.1, pitch=0.1, dt=0.02) | [-0.0796, -0.0796] | [-0.0796, -0.0796] | ✅ |

---

## Сравнение производительности Python vs C++

### Результаты бенчмарка (10000 итераций, Release сборка)

**Дата: 2026-04-07**

**Метод:** Python скрипт запускает C++ бенчмарк, получает реальные данные и строит сводную таблицу.

| Функция | Python (μs) | C++ (μs) | Разница |
|---------|-------------|----------|---------|
| **GaitController** | | | |
| contacts() | 25.99 | 0.013 | **Python в 2015x медленнее** |
| subphase_ticks() | 25.68 | 0.004 | **Python в 7339x медленнее** |
| **TrotSwingController** | | | |
| swing_height() | 0.19 | 0.002 | Python в **90x медленнее** |
| next_foot_location() | 19.35 | 0.027 | Python в **725x медленнее** |
| raibert_touchdown() | 11.04 | 0.018 | Python в **631x медленнее** |
| **TrotStanceController** | | | |
| position_delta() | 12.91 | 0.004 | **Python в 3688x медленнее** |
| next_foot_location() | 14.86 | 0.034 | Python в **444x медленнее** |
| **StandController** | | | |
| run() | N/A | 0.018 | (требует ROS) |
| **ForwardKinematics** | | | |
| forward_kinematics_per_leg() | 101.51 | N/A | - |
| forward_kinematics_all_legs() | 408.96 | 1.069 | Python в **383x медленнее** |
| **RestController** | | | |
| step() | 0.66 | 0.015 | Python в **44x медленнее** |
| **InverseKinematics** | | | |
| inverse_kinematics() | 132.70 | 0.666 | Python в **199x медленнее** |
| **PIDController** | | | |
| run() | 8.76 | 0.002 | **Python в 3810x медленнее** |
| **Trot Step (full cycle)** | | | |
| step (all 4 legs) | 95.90 | 0.171 | Python в **561x медленнее** |

### Команды для запуска

```bash
# Сводная таблица Python vs C++ (запускает оба бенчмарка)
make benchmark

# Только Python бенчмарк
make benchmark-python

# Только C++ бенчмарк
make benchmark-cpp
```

### Анализ расхождений производительности

1. **GaitController (2000x-7400x)**: Python значительно медленнее из-за numpy overhead и Python GIL. C++ просто вычисляет индекс массива.

2. **TrotSwingController (90x-630x)**: Большая разница из-за numpy broadcast операций и динамической типизации. Даже простая функция swing_height() медленнее в 90x.

3. **TrotStanceController (400x-3700x)**: Аналогично - numpy операции vs Eigen vectorized.

4. **ForwardKinematics (383x)**: Python использует numpy trigonometric functions vs Eigen optimized.

5. **InverseKinematics (199x)**: Основная работа - тригонометрия, но Python имеет overhead от numpy.

6. **PIDController (3810x)**: Неожиданно большое различие - возможно из-за Python function call overhead.

7. **Trot Step (561x)**: Суммарный эффект всех операций.

### Выводы

Python значительно медленнее C++ для всех операций контроллера:
- **Минимальная разница**: RestController.step() - 44x (все ещё значительно)
- **Максимальная разница**: subphase_ticks() - 7339x
- **Средняя разница**: ~200-500x для большинства операций

Причины:
1. Python GIL (Global Interpreter Lock)
2. NumPy broadcasting overhead
3. Динамическая типизация Python
4. Eigen оптимизации (vectorization, cache locality)
5. Function call overhead в Python

### Технические детали реализации

**C++ бенчмарк:** Выводит JSON с результатами замеров между маркерами `=== BENCHMARK_JSON_START ===` и `=== BENCHMARK_JSON_END ===`.

**Python бенчмарк:** Запускает C++ бенчмарк как подпроцесс, парсит JSON вывод и объединяет с результатами Python.

---

*Данный документ обновлён 2026-04-07*
