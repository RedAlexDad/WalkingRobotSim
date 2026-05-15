# Исправление конфликта executor в waypoint_collector.py

## Проблема

Нода `waypoint_collector.py` падала с `RuntimeError: Executor is already spinning` сразу после запуска.

### Коренная причина

В `main()` использовался `rclpy.spin(node)`, который запускает **глобальный executor** в бесконечном цикле. При этом:

1. **`waitUntilNav2Active()`** (в фоновом потоке `_wait_for_nav2`) вызывает `rclpy.spin_until_future_complete(self, future)` — эта функция пытается использовать тот же глобальный executor, который уже крутится в `main()`. Результат: `RuntimeError: Executor is already spinning` → `_wait_for_nav2` завершался с ошибкой.

2. **`_spin_basic_navigator`** (таймер 0.5с) вызывает `rclpy.spin_once(self.navigator, timeout_sec=0)` — тоже пытается использовать глобальный executor, который уже занят. Результат: тот же `RuntimeError` → процесс умирал.

Обе ошибки — следствие одной проблемы: глобальный executor не может быть одновременно задействован в `main()` и во вложенных вызовах.

### Исправление

- **Вместо** `rclpy.spin(node)` (использует глобальный executor) в `main()` создаётся собственный `SingleThreadedExecutor`:
  ```python
  executor = SingleThreadedExecutor()
  executor.add_node(node)
  executor.spin()
  ```
- **Глобальный executor остаётся свободным** — `waitUntilNav2Active()` и `rclpy.spin_once(self.navigator)` могут его использовать без конфликта.
- **`_spin_basic_navigator` таймер** восстановлен (был удалён по ошибке), так как теперь глобальный executor не занят.
- **`rclpy.spin_once(self, ...)` в `clear_waypoints_callback`** удалён — он вызывал `spin_once` на том же executor, в котором исполняется сам колбэк (тоже приводило бы к ошибке). Замена не требуется, `cancelTask()` достаточно.

## Новые Makefile цели

Добавлены в `Makefile`:

```
make waypoint-start   → ros2 service call /start_navigation std_srvs/Trigger
make waypoint-clear   → ros2 service call /clear_waypoints std_srvs/Trigger
```

---

# Текущая проблема: робот не идёт после make waypoint-start

## Симптомы

После `make waypoint-start` сервис возвращает `success=True`, но:
- Робот не двигается (cmd_vel = 0 всегда)
- В логе `waypoint_collector`:
  ```
  Navigation result: TaskResult.UNKNOWN
  Navigation completed, ready for new start command
  ```
  сразу после вызова, без паузы
- Затем бесконечно: `'FollowWaypoints' action server not available, waiting...`

## Диагностика

### 1. Nav2 работает, action server существует

Все узлы Nav2 активны в namespace `/robot1/`:
```
/robot1/amcl
/robot1/bt_navigator
/robot1/controller_server
/robot1/planner_server
/robot1/waypoint_collector (2 экземпляра: сама нода + BasicNavigator внутри неё)
...
```

Action `/robot1/follow_waypoints` присутствует в списке (подтверждено `ros2 action list`).

### 2. AMCL не публикует map→odom

На топике `/robot1/tf` присутствует только `odom → base_link` (от EKF).
`map → odom` (от AMCL) **никогда не публикуется**, несмотря на `tf_broadcast: true` в nav2_params.yaml.

### 3. AMCL не может локализоваться

AMCL pose показывает неверную позицию: `x=2.25, y=-2.26` (меняется от запуска к запуску).
Одометрия робота в Gazebo: примерно `x=-1.53, y=-2.15`.

**Сканирование не совпадает с картой** — AMCL не может найти соответствие между laser scan и `cafe_world_map.pgm`.

### 4. Initial pose не принимается

Даже после последовательности:
```
reinitialize_global_localization (сброс частиц)
→ 3x publish /robot1/initialpose с нужными координатами
→ SetInitialPose service call
```
AMCL всё равно сходится к неправильной позиции.

### 5. waypoint_collector не может подключиться к FollowWaypoints

Несмотря на то, что action server `/robot1/follow_waypoints` существует,
`BasicNavigator.followWaypoints()` не может к нему подключиться.
Возвращает `TaskResult.UNKNOWN` немедленно.

## Причины (предположительно)

### А. Несовпадение карты и мира

`cafe.world` (Gazebo) использует `model://cafe` из Fuel — модель может обновляться/отличаться от той, по которой делалась `cafe_world_map.pgm`. Плюс `cafe_table` расставлены вручную. В результате laser scan в позиции робота не совпадает с картой.

### Б. Проблема с namespace в BasicNavigator

```python
ns = self.get_namespace().lstrip('/')  # '/robot1' → 'robot1'
self.navigator = BasicNavigator(namespace=ns)
```

BasicNavigator ищет action `follow_waypoints` — должен находить `/robot1/follow_waypoints`. Факт: находит не всегда.

### В. Timing в launch файле

Launch файл публикует `/robot1/initialpose` одновременно с `bringup_cmd`:
```python
# initial pose публикуется в параллельном процессе, AMCL не готов
```

### Г. Нет проверки nav2_ready

В `start_navigation_callback` нет проверки `self.nav2_ready`:
```python
# followWaypoints() стартует сразу, даже если Nav2 ещё не инициализирован
```

## Что нужно сделать

### 1. Исправить initial pose в launch файле

Добавить задержку или lifecycle-триггер, чтобы initial pose публиковался **после** активации AMCL.

### 2. Диагностировать map→odom

Проверить:
- Параметр `tf_broadcast: true` в AMCL
- Состояние AMCL (lifecycle активен?)
- Почему AMCL не публикует transform

### 3. Диагностировать FollowWaypoints

Проверить:
- Какой именно action name использует BasicNavigator?
- Есть ли QoS mismatch?
- Почему wait_for_server() не находит сервер?

### 4. Добавить ожидание nav2_ready

В `start_navigation_callback` добавить проверку `self.nav2_ready`:
```python
if not self.nav2_ready:
    response.success = False
    response.message = "Nav2 not ready yet"
    return response
```

### 5. Альтернатива: regenerate map или изменить мир

Если карта не совпадает с миром — перегенерировать карту через SLAM Toolbox,
либо изменить spawn координаты робота в `robots.yaml` на `(0, 0)`.

---

# Вторая итерация: followWaypoints не подключается к action server (исправлено)

## Проблема

После `make waypoint-start`:
- `success=True` возвращается сразу
- В логе: `Navigation result: TaskResult.UNKNOWN` + `Navigation completed`
- Робот не двигается

## Коренная причина

**Проблема 1: `BasicNavigator.followWaypoints()` не может найти action server**

`followWaypoints()` вызывает `wait_for_server()` в цикле:
```python
while not self.follow_waypoints_client.wait_for_server(timeout_sec=1.0):
    self.info("'FollowWaypoints' action server not available, waiting...")
```

`wait_for_server()` использует `rclpy.spin_until_future_complete(self, future)` внутри, который
добавляет ноду `BasicNavigator` в **глобальный executor** и крутит его. Но:

1. `_spin_basic_navigator` таймер (0.5с) вызывает `rclpy.spin_once(self.navigator, timeout_sec=0)` —
   тоже через глобальный executor, но `timeout_sec=0` возвращается мгновенно,
   не давая DDS discovery завершиться

2. `_wait_for_nav2` в фоновом потоке тоже вызывает `rclpy.spin_until_future_complete(self, future)`
   через глобальный executor — race condition с `_spin_basic_navigator`

3. Нода `BasicNavigator` **не добавлена ни в один executor** стабильно —
   она то появляется в глобальном executor (через `spin_until_future_complete`),
   то исчезает, вызывая нестабильность DDS discovery.

**Проблема 2: `isTaskComplete()` даёт false positive**

```python
def isTaskComplete(self):
    if not self.result_future:
        return True  # <-- БАГ: None result_future трактуется как "завершено"
```

Когда `followWaypoints()` застрял в `wait_for_server()`, `result_future` ещё `None`,
но `check_navigation()` (таймер 0.1с) вызывает `isTaskComplete()` и получает `True` →
немедленно логирует `TaskResult.UNKNOWN`.

## Исправление (текущее)

Полностью переписан механизм отправки goal:

### Iteration 1: async ActionClient

После первого запуска с async ActionClient — SIGABRT:

```
geometry_msgs__msg__pose_stamped__convert_from_py: Assertion
`strncmp("geometry_msgs.msg._pose_stamped.PoseStamped", full_classname_dest, 43) == 0' failed.
```

**Причина**: `FollowWaypoints.Goal.poses` ожидает `PoseStamped[]`, а код отправлял `Pose[]`:
```python
# BUG: wp.pose — это Pose, а нужно PoseStamped
goal_msg.poses = [wp.pose for wp in self.waypoints]
# FIX: self.waypoints уже содержит PoseStamped
goal_msg.poses = self.waypoints
```

Дополнительно: `wait_for_server(timeout_sec=1.0)` может вернуть `False` — добавлена проверка.

### Итоговый код

1. **ActionClient на ноде WaypointCollector** (а не на BasicNavigator):
   ```python
   self._follow_wp_client = ActionClient(
       self, FollowWaypoints, 'follow_waypoints'
   )
   ```
   WaypointCollector уже в executor (custom SingleThreadedExecutor в `main()`),
   поэтому его колбэки обрабатываются стабильно.

2. **Асинхронная отправка goal** вместо блокирующего `followWaypoints()`:
   ```python
   def _send_goal_async(self):
       goal_msg = FollowWaypoints.Goal()
       goal_msg.poses = [wp.pose for wp in self.waypoints]
       self._follow_wp_client.wait_for_server(timeout_sec=1.0)
       send_goal_future = self._follow_wp_client.send_goal_async(
           goal_msg, self._feedback_callback
       )
       send_goal_future.add_done_callback(self._goal_response_callback)
   ```
   - `send_goal_async` не блокирует executor
   - Колбэки `_goal_response_callback` / `_result_callback` обрабатываются executor'ом

3. **Проверка `nav2_ready`** в `start_navigation_callback`:
   ```python
   if not self.nav2_ready:
       response.success = False
       response.message = "Nav2 is not ready yet"
       return response
   ```

4. **Удалён `_spin_basic_navigator` таймер** — больше не нужен.

5. **Правильное отслеживание завершения** через `_nav_result_future` и
   `GoalStatus` в `check_navigation()`.

## Файлы

- `src/gazebo_sim/scripts/waypoint_collector.py` — основная нода (исправлена)
- `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py` — launch файл с проблемным timing
- `src/gazebo_sim/config/nav2_params.yaml` — AMCL конфиг
- `src/gazebo_sim/config/robots.yaml` — spawn координаты робота
- `src/gazebo_sim/maps/cafe_world_map.yaml` — карта
- `src/gazebo_sim/world/cafe.world` — мир Gazebo
