# RobotGaitCommand

**Тип:** ROS 2 Message (msg)  
**Пакет:** `quadropted_msgs`  
**Файл:** `src/quadropted_msgs/msg/RobotGaitCommand.msg`

## Описание

Сообщение `RobotGaitCommand` управляет параметрами походки четвероногого робота: типом походки, высотой корпуса и высотой шага.

## Поля сообщения

| Поле | Тип | Описание |
|------|-----|----------|
| `robot_id` | `uint16` | Идентификатор робота |
| `gait_type` | `uint16` | Тип походки (см. константы ниже) |
| `body_height` | `float32` | Высота корпуса над землёй (м) |
| `leg_height` | `float32` | Высота шага ноги (м) |

## Константы типов походки

| Константа | Значение | Описание |
|-----------|----------|----------|
| `GAIT_TYPE_IDLE` | 0 | Бездействие, ноги сложены |
| `GAIT_TYPE_TROT` | 1 | Рысь — диагональная двухтактная походка |
| `GAIT_TYPE_TROT_RUN` | 2 | Бег рысью — ускоренная рысь |
| `GAIT_TYPE_CLIMB_STAIR` | 3 | Походка для подъёма по лестнице |
| `GAIT_TYPE_TROT_OBST` | 4 | Рысь с преодолением препятствий |

## Пример использования

### Публикация команды походки

```bash
ros2 topic pub /gait_command quadropted_msgs/msg/RobotGaitCommand \
  "{robot_id: 1, gait_type: 1, body_height: 0.25, leg_height: 0.08}"
```

### Python-код

```python
from quadropted_msgs.msg import RobotGaitCommand

msg = RobotGaitCommand()
msg.robot_id = 1
msg.gait_type = 1  # GAIT_TYPE_TROT
msg.body_height = 0.25  # 25 см
msg.leg_height = 0.08   # 8 см высота шага
```

## Диаграмма типов походок

```
[0] IDLE ──────────────────────────────> Покой
  │
  ├──> [1] TROT ──────────────────────> Стандартная ходьба
  │
  ├──> [2] TROT_RUN ──────────────────> Быстрая ходьба
  │
  ├──> [3] CLIMB_STAIR ───────────────> Лестница (высокий шаг)
  │
  └──> [4] TROT_OBST ─────────────────> Препятствия (адаптивный шаг)
```

## Связанные сообщения

- [[RobotModeCommand]] — общий режим работы
- [[RobotVelocity]] — команда скорости
- [[RobotFootContact]] — контакты стоп
- [[RobotBehaviorCommand]] — сервис поведенческих команд
