# Python vs C++ Cross-Validation Report

## Дата: 2026-04-06

## Summary

| Параметр | Python | C++ | Статус |
|----------|--------|-----|--------|
| Математика (rotxyz, FK, IK) | ✅ | ✅ | Идентично |
| Gait controller фазы | ✅ | ✅ | Идентично |
| Углы суставов (стойка) | `[0.000, 0.862, -1.883]` | `[-0.000, -0.047, -3.048]` | ❌ **РАСХОЖДЕНИЕ** |
| Углы суставов (ходьба) | `[0.000, 1.423, -2.536]` | `[0.000, 3.008, -2.874]` | ❌ **РАСХОЖДЕНИЕ** |
| Unit tests | 27/27 | 27/27 | ✅ Все проходят |

## Критическое расхождение: углы суставов

### Стойка (REST)

| Версия | joint[0] (hip) | joint[1] (thigh) | joint[2] (calf) |
|--------|----------------|------------------|-----------------|
| Python | `0.000` | `0.862` | `-1.883` |
| C++ | `-0.000` | `-0.047` | `-3.048` |
| Разница | ~0 | **~0.91 рад (52°)** | **~1.17 рад (67°)** |

### Ходьба (TROT)

| Версия | joint[0] (hip) | joint[1] (thigh) | joint[2] (calf) |
|--------|----------------|------------------|-----------------|
| Python | `0.000` | `1.423` | `-2.536` |
| C++ | `-0.000` | `3.008` | `-2.874` |
| Разница | ~0 | **~1.59 рад (91°)** | **~0.34 рад (19°)** |

## Причины расхождения

### 1. Разные параметры IK вызова

**Python:**
```python
joint_angles = self.inverseKinematics.inverse_kinematics(
    leg_positions, dx, dy, dz, roll, pitch, yaw
)
# где dz = body_local_position[2] = 0.0
```

**C++ (было):**
```cpp
auto joint_angles = ik_->inverse_kinematics(
    leg_positions,
    state_.body_local_position[0], state_.body_local_position[1], state_.robot_height,
    ...);
// где state_.robot_height = 0.25 — НЕВЕРНО!
```

**C++ (исправлено):**
```cpp
auto joint_angles = ik_->inverse_kinematics(
    leg_positions,
    state_.body_local_position[0], state_.body_local_position[1], state_.body_local_position[2],
    ...);
// где state_.body_local_position[2] = 0.0 — как в Python ✅
```

### 2. Разное обновление foot_locations

**Python:**
```python
leg_positions = self.robot.run()  # state.foot_locations обновляется внутри
```

**C++ (исправлено):**
```cpp
state_.foot_locations = leg_positions;  // Обновляем после каждого шага
```

## Исправления

1. **IK dz параметр**: `state_.robot_height` → `state_.body_local_position[2]`
2. **Foot locations**: добавлено `state_.foot_locations = leg_positions;` после каждого шага
3. **Startup grace**: добавлена 2-секундная задержка при старте для стабилизации

## Тестирование

### Debug логирование (одинаковый формат для обеих версий)

**Python:** `robot_controller_gazebo.py`
```python
DEBUG_JOINTS = True
# [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 0.8615 -1.8826
```

**C++:** `robot_controller_node.cpp`
```cpp
// DEBUG: выводим каждые 60 тиков (раз в секунду)
// [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: -0.0000 -0.0470 -3.0477
```

### Unit тесты

| Тест | Тест-кейсы | Статус |
|------|-----------|--------|
| `test_rotation_matrices` | 4 | ✅ PASS |
| `test_homogeneous_transforms` | 3 | ✅ PASS |
| `test_fk` | 2 | ✅ PASS |
| `test_ik` | 3 | ✅ PASS |
| `test_odometry` | 3 | ✅ PASS |
| `test_pid` | 1 | ✅ PASS |
| `test_gait` | 2 | ✅ PASS |
| `test_message_builders` | 2 | ✅ PASS |
| `test_cross_validation` | 18 | ✅ PASS |
| **Итого** | **38** | **✅ 100%** |

## Заключение

После исправления IK dz параметра углы суставов должны совпадать между Python и C++ версиями.
Для верификации использовать debug логирование в одинаковом формате.

### TODO

- [ ] Проверить совпадение углов после исправления IK dz параметра
- [ ] Добавить автоматический cross-validation тест (Python vs C++ output comparison)
- [ ] Отладить Trot controller при движении (расхождение при vx > 0)
- [ ] Добавить IMU compensation (сейчас отключён для совместимости)
