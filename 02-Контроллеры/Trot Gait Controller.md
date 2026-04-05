# Trot Gait Controller — Контроллер рыси

## Файл
`src/quadropted_controller/scripts/RobotController/TrotGaitController.py`

## Описание

Реализует походку «рысь» (trot) — диагональные пары ног двигаются синхронно. Самый быстрый режим ходьбы.

## Параметры

| Параметр | Значение | Описание |
|---|---|---|
| `stance_time` | 0.04 с | Время фазы опоры |
| `swing_time` | 0.18 с | Время фазы переноса |
| `time_step` | 0.02 с | Шаг дискретизации |
| `z_leg_lift` | 0.14 м | Высота подъёма ноги |
| `z_error_constant` | 0.02 | Скорость коррекции по Z |

### Лимиты скорости

| Ось | Максимум |
|---|---|
| X (вперёд) | 0.035 м/с |
| Y (бок) | 0.012 м/с |
| Yaw (поворот) | 0.5 рад/с |

### Фазы контакта

```
        Фаза 0  Фаза 1  Фаза 2  Фаза 3
FR:       1       1       1       0
FL:       1       0       1       1
RR:       1       0       1       1
RL:       1       1       1       0
```

Диагональные пары: (FL+RR) и (FR+RL) двигаются вместе.

## Внутренние классы

### TrotSwingController

Управляет фазой переноса ноги.

**Ключевые методы:**

- `raibert_touchdown_location(leg_index, command)` — вычисляет точку приземления по эвристике Raibert:
  ```
  touchdown = rotation(default_stance) + velocity * phase_length * time_step
  ```
- `swing_height(swing_phase)` — профиль высоты подъёма ноги (треугольный, макс = z_leg_lift)
- `next_foot_location(swing_prop, leg_index, state, command)` — следующая позиция ноги в фазе переноса

### TrotStanceController

Управляет фазой опоры (нога на земле).

**Ключевые методы:**

- `position_delta(leg_index, state, command)` — вычисляет смещение ноги в фазе опоры:
  - X/Y: движение против направления скорости (тело движется вперёд)
  - Z: P-регулятор к целевой высоте
- `next_foot_location(leg_index, state, command)` — следующая позиция ноги в фазе опоры

## PID компенсация

```python
PID_controller(kp=0.15, ki=0.02, kd=0.002)
```

Компенсирует крен (roll) и тангаж (pitch) по данным IMU. Anti-windup: max_I = 0.2.

## AutoRest

При `autoRest = True` и нулевой скорости, робот автоматически переходит в режим покоя на каждом чётном цикле.

## Публикации

| Топик | Тип | Описание |
|---|---|---|
| `foot_contact` | `RobotFootContact` | Состояния контакта 4 ног |
| `controller_velocity` | `geometry_msgs/Twist` | Скорость для ros2_control |

**Примечание:** `foot_contact` публикуется на каждом шаге `step()` с текущими режимами контакта ног. При autoRest (все ноги на земле) публикуется `[True, True, True, True]`.
