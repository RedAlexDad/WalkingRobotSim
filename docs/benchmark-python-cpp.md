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

### Python

```python
# Параметры из RobotController.py
stance_time = 0.55  # время стойки (сек)
swing_time = 0.45   # время шага (сек)
step_height = 0.05   # высота шага (м)
robot_height = 0.25  # высота робота (м)
```

### C++

```cpp
// Параметры из конфигурации
stance_time = 0.55f;   // время стойки (сек)
swing_time = 0.45f;     // время шага (сек)
step_height = 0.05f;    // высота шага (м)
robot_height = 0.25f;   // высота робота (м)
```

## Ожидаемые результаты

### Стойка (REST)

| Параметр | Python | C++ | Ожидаемое |
|----------|--------|-----|-----------|
| joint[0] hip | ~0.0 | ~0.0 | ✅ Идентично |
| joint[1] thigh | ~0.86 | ~0.86 | ✅ Совпадение |
| joint[2] calf | ~-1.88 | ~-1.88 | ✅ Совпадение |

### Ходьба (TROT)

| Параметр | Python | C++ | Ожидаемое |
|----------|--------|-----|-----------|
| joint[0] hip | ~0.0 | ~0.0 | ✅ Идентично |
| joint[1] thigh | ~1.42 | ~1.42 | ✅ Совпадение |
| joint[2] calf | ~-2.54 | ~-2.54 | ✅ Совпадение |

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

### Этап 1: Базовая стойка
- [ ] Запустить Python controller в режиме стойки
- [ ] Запустить C++ controller в режиме стойки
- [ ] Сравнить углы суставов

### Этап 2: Ходьба вперед
- [ ] Запустить Python controller с vx=0.03
- [ ] Запустить C++ controller с vx=0.03
- [ ] Сравнить углы суставов в разные моменты времени

### Этап 3: Поворот
- [ ] Запустить Python controller с yaw=1.0
- [ ] Запустить C++ controller с yaw=1.0
- [ ] Сравнить углы суставов

### Этап 4: Автоматический тест
- [ ] Запустить automated benchmark script
- [ ] Сгенерировать отчет с результатами

## Предыдущие известные проблемы (исправлены)

1. ❌ **IK dz параметр**: `robot_height` → `body_local_position[2]`
2. ❌ **Foot locations update**: добавлено обновление после каждого шага
3. ❌ **Startup grace**: добавлена задержка при старте
4. ❌ **IMU compensation**: отключена для стабильности

## Результаты будут записаны после проведения тестов

---

*Данный документ будет обновлён после проведения бенчмарка*
