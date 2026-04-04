# RobotFootContact

**Тип:** ROS 2 Message (msg)  
**Пакет:** `quadropted_msgs`  
**Файл:** `src/quadropted_msgs/msg/RobotFootContact.msg`

## Описание

Сообщение `RobotFootContact` передаёт информацию о контакте стоп робота с поверхностью. Критически важно для одометрии и управления походкой.

## Поля сообщения

| Поле | Тип | Описание |
|------|-----|----------|
| `contacts` | `bool[4]` | Массив контактов стоп: `[FR, FL, RR, RL]` |

### Индексы стоп

| Индекс | Стопа | Положение |
|--------|-------|-----------|
| 0 | FR | Front-Right (передняя правая) |
| 1 | FL | Front-Left (передняя левая) |
| 2 | RR | Rear-Right (задняя правая) |
| 3 | RL | Rear-Left (задняя левая) |

## Схема расположения стоп

```
       Перед
    ┌─────────┐
    │  [0] [1]│  ← FR(0)  FL(1)
    │  корпус  │
    │  [2] [3]│  ← RR(2)  RL(3)
    └─────────┘
       Зад
```

## Пример использования

### Публикация

```bash
ros2 topic pub /foot_contact quadropted_msgs/msg/RobotFootContact \
  "{contacts: [true, false, false, true]}"
```

### Подписка (Python)

```python
from quadropted_msgs.msg import RobotFootContact

def foot_contacts_callback(msg: RobotFootContact):
    if len(msg.contacts) != 4:
        return
    for i, contact in enumerate(msg.contacts):
        leg = ['FR', 'FL', 'RR', 'RL'][i]
        status = "на земле" if contact else "в воздухе"
        print(f"{leg}: {status}")
```

## Использование в одометрии

Узел [[Одометрия по контакту стоп]] использует это сообщение для определения, какие стопы находятся на земле. Только контактирующие стопы участвуют в расчёте перемещения:

```python
def foot_contacts_callback(self, msg):
    if len(msg.contacts) != 4:
        self.foot_contacts = [False, False, False, False]
        return
    self.foot_contacts = list(msg.contacts)
```

## Связанные сообщения

- [[RobotVelocity]] — команда скорости
- [[RobotModeCommand]] — режим работы робота
- [[Одометрия по контакту стоп]] — основной потребитель сообщения
