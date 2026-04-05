# PID Controller

## Файл
`src/quadropted_controller/scripts/RobotController/PIDController.py`

## Описание

Двухосевой PID-контроллер для компенсации крена (roll) и тангажа (pitch) по данным IMU.

## Параметры

| Параметр | Описание |
|---|---|
| `kp` | Пропорциональный коэффициент |
| `ki` | Интегральный коэффициент |
| `kd` | Дифференциальный коэффициент |
| `max_I` | 0.2 -- ограничение интегральной составляющей (anti-windup) |

## Алгоритм

```
error = desired - measured
I_term += error * dt  (clamped to [-max_I, max_I])
D_term = (error - last_error) / dt
output = kp * error + ki * I_term + kd * D_term
```

## Значения для разных контроллеров

| Контроллер | kp | ki | kd |
|---|---|---|---|
| RestController | 0.75 | 2.29 | 0.0 |
| TrotGaitController | 0.15 | 0.02 | 0.002 |

## Методы

- `run(roll, pitch)` -- вычисляет управляющее воздействие
- `reset()` -- сброс интегральной и дифференциальной составляющих
- `set_desired_RP_angles(roll, pitch)` -- установка целевых углов (по умолчанию [0, 0])
