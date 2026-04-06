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

## Реальные логи DEBUG: сравнение Python vs C++

### Стойка (REST, vx=0)

**Python:**
```
[robot_controller_gazebo.py-10] [INFO] [1775461901.127198959] [robot1.quadruped_controller]: [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 0.8615 -1.8826
[robot_controller_gazebo.py-10] [INFO] [1775461902.769182868] [robot1.quadruped_controller]: [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 0.8615 -1.8826
[robot_controller_gazebo.py-10] [INFO] [1775461904.370505747] [robot1.quadruped_controller]: [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 0.8615 -1.8826
```

**C++ (до исправления):**
```
[robot_controller_node-10] [INFO] [1775462001.653524034] [robot1.robot_controller_cpp]: [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: -0.0000 -0.0470 -3.0477
[robot_controller_node-10] [INFO] [1775462002.613441077] [robot1.robot_controller_cpp]: [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: -0.0000 -0.0470 -3.0477
[robot_controller_node-10] [INFO] [1775462003.573485025] [robot1.robot_controller_cpp]: [DEBUG] cmd: vx=0.0000 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: -0.0000 -0.0470 -3.0477
```

**Расхождение:**
```
joint[0] (hip):   Python= 0.0000  vs  C++=-0.0000  →  ✅ совпадает
joint[1] (thigh): Python= 0.8615  vs  C++=-0.0470  →  ❌ разница 0.91 рад (52°)
joint[2] (calf):  Python=-1.8826  vs  C++=-3.0477  →  ❌ разница 1.17 рад (67°)
```

### Ходьба (TROT, vx=0.03)

**Python:**
```
[robot_controller_gazebo.py-10] [INFO] [1775461909.267054112] [robot1.quadruped_controller]: [DEBUG] cmd: vx=0.0299 vy=-0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 0.8829 -1.8847
[robot_controller_gazebo.py-10] [INFO] [1775461910.889358790] [robot1.quadruped_controller]: [DEBUG] cmd: vx=0.0299 vy=-0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 1.4229 -2.5358
[robot_controller_gazebo.py-10] [INFO] [1775461912.481427511] [robot1.quadruped_controller]: [DEBUG] cmd: vx=-0.0000 vy=-0.0000 vz=0.0000 yaw=-1.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.1811 0.7859 -1.9404
```

**C++:**
```
[robot_controller_node-10] [INFO] [1775462016.053822796] [robot1.robot_controller_cpp]: [DEBUG] cmd: vx=0.0299 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 1.3005 -2.0070
[robot_controller_node-10] [INFO] [1775462017.015207096] [robot1.robot_controller_cpp]: [DEBUG] cmd: vx=0.0299 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: -0.0000 3.0078 -2.8740
[robot_controller_node-10] [INFO] [1775462017.973402658] [robot1.robot_controller_cpp]: [DEBUG] cmd: vx=0.0299 vy=0.0000 vz=0.0000 yaw=0.0000 | pos: x=0.0000 y=0.0000 z=0.0000 | joints[0-2]: 0.0000 1.3569 -2.6730
```

**Расхождение (пик при vx=0.03):**
```
joint[0] (hip):   Python= 0.0000  vs  C++= 0.0000  →  ✅ совпадает
joint[1] (thigh): Python= 1.4229  vs  C++= 3.0078  →  ❌ разница 1.59 рад (91°)
joint[2] (calf):  Python=-2.5358  vs  C++=-2.8740  →  ❌ разница 0.34 рад (19°)
```

### Код debug логирования

**Python:** `src/quadropted_controller/scripts/robot_controller_gazebo.py`
```python
DEBUG_JOINTS = True  # Флаг включения debug логов

# В control_loop():
if DEBUG_JOINTS:
    self._debug_tick_count += 1
    if self._debug_tick_count % 60 == 0:
        self.get_logger().info(
            f"[DEBUG] cmd: vx={cmd.velocity[0]:.4f} vy={cmd.velocity[1]:.4f} "
            f"vz={cmd.velocity[2]:.4f} yaw={cmd.yaw_rate[2]:.4f} | "
            f"pos: x={dx:.4f} y={dy:.4f} z={dz:.4f} | "
            f"joints[0-2]: {joint_angles[0]:.4f} {joint_angles[1]:.4f} {joint_angles[2]:.4f}"
        )
```

**C++:** `src/quadropted_controller_cpp/src/nodes/robot_controller_node.cpp`
```cpp
// В control_loop():
if (state_.ticks % 60 == 0) {
    RCLCPP_INFO(get_logger(),
        "[DEBUG] cmd: vx=%.4f vy=%.4f vz=%.4f yaw=%.4f | "
        "pos: x=%.4f y=%.4f z=%.4f | "
        "joints[0-2]: %.4f %.4f %.4f",
        command_.velocity[0], command_.velocity[1], command_.velocity[2], command_.yaw_rate[2],
        state_.body_local_position[0], state_.body_local_position[1], state_.body_local_position[2],
        joint_angles[0], joint_angles[1], joint_angles[2]);
}
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
| `test_base_link_roll` | 10 | ✅ PASS (НОВЫЕ) |
| `test_ik_with_roll` | 8 (C++) + 8 (Python) | ✅ PASS (НОВЫЕ) |
| **Итого** | **68** | **✅ 100%** |

### Новые тесты (Фаза 1)

#### `test_base_link_roll.cpp` — 10 тестов
| Тест | Описание |
|------|----------|
| `rotxyz_zero_is_identity` | rotxyz(0,0,0) = identity |
| `rotx_45_degrees` | rotx(π/4) корректность |
| `rotxyz_only_roll_45` | rotxyz(π/4,0,0) = rotx(π/4) |
| `rotxyz_matches_python_multiple_angles` | 10 наборов углов vs Python |
| `R_legs_matrix_correct` | R_legs = rotxyz(π/2,-π/2,0) |
| `rotxyz_orthogonal` | R * R^T = I |
| `rotxyz_determinant_is_one` | det(R) = 1 |
| `roll_45_transforms_y_axis` | Проверка трансформации оси Y |
| `roll_45_transforms_z_axis` | Проверка трансформации оси Z |
| `rotxyz_negative_roll_45` | rotxyz(-π/4,0,0) корректность |

#### `test_ik_with_roll.cpp` — 8 тестов
| Тест | Описание |
|------|----------|
| `zero_roll_default_stance` | IK с roll=0 для стойки |
| `roll_45_degrees_affects_joint_angles` | Roll 45° меняет углы |
| `matches_python_zero_orientation` | Совпадение с Python при roll=0 |
| `fk_ik_roundtrip_zero_roll` | FK → IK roundtrip |
| `roll_45_angles_in_valid_range` | Углы в допустимом диапазоне |
| `left_right_symmetry_zero_roll` | Симметрия левых/правых ног |
| `negative_roll_45` | Отрицательный крен |
| `matches_python_small_angles` | Малые углы ориентации |

#### `test_ik_with_roll.py` — 8 тестов
| Тест | Описание |
|------|----------|
| `test_ik_zero_roll_default_stance` | IK с roll=0 для стойки |
| `test_ik_roll_45_degrees_affects_angles` | Roll 45° меняет углы |
| `test_ik_roll_45_angles_in_valid_range` | Углы в допустимом диапазоне |
| `test_ik_negative_roll_45` | Отрицательный крен |
| `test_ik_left_right_symmetry_zero_roll` | Симметрия левых/правых ног |
| `test_fk_ik_roundtrip_zero_roll` | FK → IK roundtrip |
| `test_ik_small_orientation_angles` | Малые углы ориентации |
| `test_ik_roll_varies_smoothly` | Плавное изменение roll |

## Заключение

После исправления IK dz параметра углы суставов должны совпадать между Python и C++ версиями.
Для верификации использовать debug логирование в одинаковом формате.

### TODO

- [x] Добавить модульные тесты base_link roll (10 C++ тестов)
- [x] Добавить модульные тесты IK с roll (8 C++ + 8 Python тестов)
- [ ] Проверить совпадение углов после исправления IK dz параметра
- [ ] Добавить автоматический cross-validation тест (Python vs C++ output comparison)
- [ ] Отладить Trot controller при движении (расхождение при vx > 0)
- [ ] Добавить IMU compensation (сейчас отключён для совместимости)
- [ ] Исправить расхождение step_trot между Python и C++
- [ ] Обновить body_local_orientation из IMU в реальном времени
