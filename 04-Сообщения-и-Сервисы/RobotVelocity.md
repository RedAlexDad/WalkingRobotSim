# RobotVelocity

**Тип:** ROS 2 Message (msg)  
**Пакет:** `quadropted_msgs`  
**Файл:** `src/quadropted_msgs/msg/RobotVelocity.msg`

## Описание

Сообщение `RobotVelocity` обёртывает стандартное `geometry_msgs/Twist` с добавлением идентификатора робота. Используется для передачи команд скорости в мультироботных системах.

## Поля сообщения

| Поле | Тип | Описание |
|------|-----|----------|
| `robot_id` | `uint16` | Идентификатор целевого робота |
| `cmd_vel` | `geometry_msgs/Twist` | Команда линейной и угловой скорости |

### Структура cmd_vel

| Компонент | Описание |
|-----------|----------|
| `linear.x` | Скорость вперёд/назад (м/с) |
| `linear.y` | Скорость влево/вправо (м/с) |
| `linear.z` | Вертикальная скорость (м/с) |
| `angular.x` | Крен (рад/с) |
| `angular.y` | Тангаж (рад/с) |
| `angular.z` | Рыскание/поворот (рад/с) |

## Масштабирование скоростей

Узел `RobotVelocityHandler` (`cmd_vel_pub.py`) применяет нелинейное масштабирование к входящим командам:

```python
# Нелинейное масштабирование с экспоненциальной функцией
def multiply_and_limit(self, value, scale_factor, min_limit, max_limit):
    if value > 0:
        adjusted_value = value * 0.035
        scaled_value = scale_factor * (1 - math.exp(-100 * adjusted_value))
    else:
        adjusted_value = (-value) * 0.035
        scaled_value = -scale_factor * (1 - math.exp(-100 * adjusted_value))
    return self.limit_value(scaled_value, min_limit, max_limit)
```

### Коэффициенты масштабирования

| Ось | Коэффициент | Мин | Макс |
|-----|-------------|-----|------|
| `linear.x` | 0.035 (экспоненциальное) | -1.0 | 1.0 |
| `linear.y` | 0.012 (экспоненциальное) | -1.0 | 1.0 |
| `angular.z` | 1.0 (прямое ограничение) | -1.0 | 1.0 |
| `linear.z` | Без изменений | — | — |

## Пример использования

### Публикация

```bash
ros2 topic pub /robot_velocity quadropted_msgs/msg/RobotVelocity \
  "{robot_id: 1, cmd_vel: {linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.3}}}"
```

### Подписка (Python)

```python
from quadropted_msgs.msg import RobotVelocity

def velocity_callback(msg: RobotVelocity):
    if msg.robot_id == 1:
        vx = msg.cmd_vel.linear.x
        vy = msg.cmd_vel.linear.y
        wz = msg.cmd_vel.angular.z
        # Обработка команды скорости
```

## Поток данных

```
geometry_msgs/Twist ──> [RobotVelocityHandler] ──> RobotVelocity
     /cmd_vel              cmd_vel_pub.py            /robot_velocity
```

## Связанные сообщения

- [[RobotModeCommand]] — переключение режимов работы
- [[RobotGaitCommand]] — параметры походки
- [[Одометрия по контакту стоп]] — узел одометрии подписывается на RobotVelocity
