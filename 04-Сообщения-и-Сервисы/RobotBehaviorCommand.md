# RobotBehaviorCommand

**Тип:** ROS 2 Service (srv)  
**Пакет:** `quadropted_msgs`  
**Файл:** `src/quadropted_msgs/srv/RobotBehaviorCommand.srv`

## Описание

Сервис `RobotBehaviorCommand` используется для отправки поведенческих команд роботу и получения результата их выполнения. Поддерживает команды: сесть (`sit`), встать (`up`), идти (`walk`).

## Структура сервиса

### Запрос (Request)

| Поле | Тип | Описание |
|------|-----|----------|
| `command` | `string` | Команда: `sit`, `up`, `walk` |

### Ответ (Response)

| Поле | Тип | Описание |
|------|-----|----------|
| `success` | `bool` | Результат выполнения команды |
| `message` | `string` | Текстовое сообщение о результате |

## Исходное определение

```
# RobotBehaviorCommand.srv
# Команда: [sit, up, walk]
string command
---
# Результат выполнения
bool success
string message
```

## Доступные команды

| Команда | Описание |
|---------|----------|
| `sit` | Робот садится (складывает ноги) |
| `up` | Робот встаёт (распрямляет ноги) |
| `walk` | Робот переходит в режим ходьбы |

## Пример использования

### Вызов сервиса из командной строки

```bash
# Команда сесть
ros2 service call /robot_behavior quadropted_msgs/srv/RobotBehaviorCommand \
  "{command: 'sit'}"

# Команда встать
ros2 service call /robot_behavior quadropted_msgs/srv/RobotBehaviorCommand \
  "{command: 'up'}"

# Команда идти
ros2 service call /robot_behavior quadropted_msgs/srv/RobotBehaviorCommand \
  "{command: 'walk'}"
```

### Python-клиент

```python
from quadropted_msgs.srv import RobotBehaviorCommand

async def send_behavior_command(self, command: str):
    req = RobotBehaviorCommand.Request()
    req.command = command
    
    future = self.client.call_async(req)
    result = await future
    
    if result.success:
        self.get_logger().info(f"Успех: {result.message}")
    else:
        self.get_logger().error(f"Ошибка: {result.message}")
```

### Python-сервер

```python
from quadropted_msgs.srv import RobotBehaviorCommand

def behavior_callback(self, request, response):
    if request.command == 'sit':
        response.success = self.execute_sit()
        response.message = "Сел" if response.success else "Не удалось сесть"
    elif request.command == 'up':
        response.success = self.execute_stand()
        response.message = "Встал" if response.success else "Не удалось встать"
    elif request.command == 'walk':
        response.success = self.execute_walk()
        response.message = "Иду" if response.success else "Не удалось начать ходьбу"
    else:
        response.success = False
        response.message = f"Неизвестная команда: {request.command}"
    
    return response
```

## Диаграмма взаимодействия

```
[Клиент] ──request: command="up"──> [Сервис RobotBehaviorCommand]
                                        │
                                        ├── Выполнение команды
                                        │
<──response: success, message───────────┘
```

## Связанные сообщения

- [[RobotModeCommand]] — переключение режимов
- [[RobotGaitCommand]] — параметры походки
- [[RobotVelocity]] — команды скорости
