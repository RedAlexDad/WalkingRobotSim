# RobotModeCommand

**Тип:** ROS 2 Message (msg)  
**Пакет:** `quadropted_msgs`  
**Файл:** `src/quadropted_msgs/msg/RobotModeCommand.msg`

## Описание

Сообщение `RobotModeCommand` определяет режим работы четвероногого робота. Используется для переключения между состояниями: покой, стояние, ходьба различными походками.

## Поля сообщения

| Поле | Тип | Описание |
|------|-----|----------|
| `mode` | `string` | Режим работы: `REST`, `TROT`, `CRAWL`, `STAND` и др. |
| `robot_id` | `uint16` | Идентификатор робота (для мультироботных систем) |

## Возможные режимы

| Режим | Описание |
|-------|----------|
| `REST` | Робот в покое, все ноги сложены |
| `STAND` | Робот стоит на всех четырёх ногах |
| `TROT` | Рысь — диагональная походка |
| `CRAWL` | Медленная походка, все ноги поочерёдно |

## Пример использования

### Публикация команды режима

```bash
ros2 topic pub /robot_mode quadropted_msgs/msg/RobotModeCommand \
  "{mode: 'TROT', robot_id: 1}"
```

### Python-код подписки

```python
from quadropted_msgs.msg import RobotModeCommand

def mode_callback(msg: RobotModeCommand):
    print(f"Robot {msg.robot_id} switched to mode: {msg.mode}")

subscription = node.create_subscription(
    RobotModeCommand,
    'robot_mode',
    mode_callback,
    10
)
```

## Связанные сообщения

- [[RobotVelocity]] — команда скорости для робота
- [[RobotGaitCommand]] — параметры походки (высота корпуса, тип)
- [[RobotFootContact]] — состояние контактов стоп с поверхностью

## Диаграмма состояний

```
   [REST] ──STAND──> [STAND]
     │                  │
     │              TROT/CRAWL
     │                  │
     └──────REST───────┘
```
