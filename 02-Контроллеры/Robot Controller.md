# Robot Controller — Главный контроллер

## Файл
`src/quadropted_controller/scripts/RobotController/RobotController.py`

## Класс `Robot`

Центральный конечный автомат (state machine), управляющий переключением между контроллерами походки.

### Инициализация

```python
Robot(node, body, legs, imu, robot_id)
```

**Параметры:**
- `node` -- ROS 2 Node (для создания подписок/сервисов)
- `body` -- [длина, ширина] тела = [0.3762, 0.0935]
- `legs` -- [l1, l2, l3, l4] = [0.0, 0.0955, 0.213, 0.213]
- `imu` -- использовать ли IMU компенсацию
- `robot_id` -- идентификатор робота для мультиробота

### Внутренние контроллеры

| Контроллер | Класс | Назначение |
|---|---|---|
| TrotGaitController | `TrotGaitController` | Ходьба рысью (диагональные пары) |
| CrawlGaitController | `CrawlGaitController` | Ползание (последовательные ноги) |
| StandController | `StandController` | Стойка (вращение на месте) |
| RestController | `RestController` | Покой (неподвижность) |

### Параметры стойки по умолчанию

```python
delta_x = body[0] * 0.5           # 0.1881
delta_y = body[1] * 0.5 + legs[1] # 0.14225
x_shift_front = 0.02
x_shift_back = 0.0
default_height = 0.25
```

**Default stance** (FR, FL, RR, RL):
```
X: [0.2081, 0.2081, -0.1881, -0.1881]
Y: [-0.14225, 0.14225, -0.14225, 0.14225]
Z: [0, 0, 0, 0]
```

### Подписки

| Топик | Тип | Callback |
|---|---|---|
| `robot_mode` | `RobotModeCommand` | `mode_callback` |
| `robot_velocity` | `RobotVelocity` | `velocity_callback` |

### Сервис

| Сервис | Тип | Callback |
|---|---|---|
| `robot_behavior_command` | `RobotBehaviorCommand` | `handle_behavior_command` |

### Режимы (BehaviorState)

```python
class BehaviorState(Enum):
    REST = 0    # Покой
    TROT = 1    # Рысь
    CRAWL = 2   # Ползание
    STAND = 3   # Стойка
```

### Инициализация по умолчанию

При создании `Robot` автоматически:
1. Устанавливает `trot_event = True`
2. Вызывает `change_controller()` -- переключается на TROT

### Логика переключения контроллеров

Метод `change_controller()` обрабатывает события:

1. **TROT + REST** (оба True) -- Сначала REST, затем TROT (для команды 'walk')
2. **TROT** -- TrotGaitController (сброс ticks)
3. **CRAWL** -- CrawlGaitController (first_cycle=True, сброс ticks)
4. **STAND** -- StandController (body_local_position[2] = 0.005)
5. **REST** -- RestController (сброс PID)

### Сервис поведения

| Команда | Действие |
|---|---|
| `sit` | STAND режим, body_local_position[2] = -0.15 |
| `up` | REST режим, body_local_position[2] = 0.0 |
| `walk` | REST + TROT переход, body_local_position[2] = 0.0 |

### Метод `run()`

Вызывает `currentController.run(state, command)` и возвращает позиции стоп (3x4 матрица).

### State и Command

**State** -- текущее состояние робота:
- `foot_locations` -- позиции стоп (3x4)
- `body_local_position` -- [x, y, z] тела
- `body_local_orientation` -- [roll, pitch, yaw]
- `imu_roll`, `imu_pitch` -- данные IMU
- `ticks` -- счётчик тактов походки
- `behavior_state` -- текущий режим
- `robot_height` -- высота тела

**Command** -- команды управления:
- `velocity` -- [x, y, z] скорость
- `yaw_rate` -- [roll, pitch, yaw] угловая скорость
- `robot_height` -- высота тела
- `rest_event`, `trot_event`, `crawl_event`, `stand_event` -- флаги событий
