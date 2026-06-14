# Разработка waypoint-навигации для WalkingRobotSim

## Цель

Разработать и отладить систему навигации робота по waypoint'ам через RViz
(WaypointTool) + `waypoint_collector.py` + Nav2 FollowWaypoints action server.
Система должна позволять:

- Расставлять waypoints кликами в RViz (кастомный инструмент WaypointTool)
- Запускать навигацию по всем точкам
- Останавливать навигацию на ходу
- Продолжать маршрут с прерванного места
- Переходить к конкретному waypoint по индексу
- Очищать все waypoints
- Управление через Makefile цели

## Инструменты

- `src/rviz_waypoint_tool/src/custom_goal_tool.cpp` — кастомный RViz инструмент,
  публикует клик в `/custom_goal_pose`
- `src/gazebo_sim/scripts/waypoint_collector.py` — основной скрипт: сбор точек,
  управление навигацией, публикация маркеров
- `src/gazebo_sim/launch/nav2/navigation_launch.py` — launch Nav2
- `src/gazebo_sim/config/nav2_params.yaml` — параметры Nav2
- `Makefile` — цели `waypoint-*`

---

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

После первого запуска с async ActionClient — SIGABRT.
**Причина**: `FollowWaypoints.Goal.poses` ожидает `PoseStamped[]`, а код отправлял `Pose[]`.

### Iteration 2: wait_for_server внутри колбэка

После исправления типа — `FollowWaypoints action server not available`.
**Причина**: `wait_for_server(timeout_sec=1.0)` не может найти сервер, потому что
вызывается внутри service callback. `SingleThreadedExecutor` занят обработкой
колбэка и не может обрабатывать DDS discovery события.

**Исправление**: timer-based retry вместо блокирующего wait_for_server:
```python
def _send_goal_async(self):
    if self._follow_wp_client.server_is_ready():
        self._do_send_goal(goal_msg)
    else:
        self._goal_retry_timer = self.create_timer(0.5, self._retry_send_goal)

def _retry_send_goal(self):
    if self._follow_wp_client.server_is_ready():
        self._goal_retry_timer.cancel()
        self._do_send_goal(self._pending_goal)
```

Теперь discovery происходит асинхронно, executor не блокируется.

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

---

# Третья итерация: FollowWaypoints action server не запущен (0 серверов)

## Проблема

`ros2 action info /robot1/follow_waypoints`:
- Action clients: 3
- Action servers: 0

Несмотря на то, что `waypoint_collector` (3 клиента) исправно пытается подключиться,
action server `follow_waypoints` физически не запущен в системе.

## Коренная причина

В `navigation_launch.py` нода `waypoint_follower` была **закомментирована**:

```python
lifecycle_nodes = [
    "controller_server", "planner_server", "behavior_server",
    "smoother_server",  "bt_navigator",
    # 'waypoint_follower'  # <-- выключен
]
```

Параметры в `nav2_params.yaml` при этом были полностью настроены:
```yaml
waypoint_follower:
  ros__parameters:
    stop_on_failure: false
    waypoint_pause_duration: 0.0
    plugin: "nav2_waypoint_follower::WaitAtWaypoint"
```

То есть конфиг был готов, но сам lifecycle node не создавался — action server
`/robot1/follow_waypoints` никогда не регистрировался в DDS.

## Исправление

Два изменения в `navigation_launch.py`:

1. `'waypoint_follower'` добавлен в список `lifecycle_nodes`
2. Добавлен `Node(package='nav2_waypoint_follower', executable='waypoint_follower', ...)`

После пересборки и запуска `ros2 action info /robot1/follow_waypoints` должен показать 1 сервер.

---

# Четвёртая итерация: добавлены команды навигации к конкретному waypoint и остановки

## Изменения

### 1. Новый сервис WaypointNavigate в quadropted_msgs

Создан `srv/WaypointNavigate.srv`:
```
int32 index   # index waypoint (-1 = все)
---
bool success
string message
```

### 2. Новые сервисы в waypoint_collector.py

- `/navigate_to_waypoint` (WaypointNavigate) — навигация к waypoint по индексу. `index=-1` = все waypoints.
- `/stop_navigation` (Trigger) — остановка текущей навигации без очистки списка waypoints.
- `/start_navigation` теперь явно передаёт `self.waypoints` в `_send_goal_async()`.

### 3. Новые Makefile цели

```
make waypoint-start               # все waypoints (как было)
make waypoint-navigate INDEX=2    # навигация к waypoint №2
make waypoint-stop                # остановка навигации
make waypoint-clear               # очистка + остановка (было)
```

### 4. Сборка

Требуется пересобрать `quadropted_msgs` (новый .srv):
```
colcon build --packages-select quadropted_msgs
colcon build --packages-select gazebo_sim
```

## Файлы

- `src/gazebo_sim/scripts/waypoint_collector.py` — основная нода (исправлена)
- `src/gazebo_sim/launch/gazebo_multi_nav2_cpp.launch.py` — launch файл с проблемным timing
- `src/gazebo_sim/config/nav2_params.yaml` — AMCL конфиг (уже содержит waypoint_follower параметры)

- `src/gazebo_sim/config/robots.yaml` — spawn координаты робота
- `src/gazebo_sim/maps/cafe_world_map.yaml` — карта
- `src/gazebo_sim/world/cafe.world` — мир Gazebo

---

# Пятая итерация: stop_navigation не работал во время активной навигации

## Проблема

После запуска навигации (`/start_navigation`) вызов `/stop_navigation` возвращал:
```
success: True
message: 'No active navigation'
```

Стоп не срабатывал, пока робот не доедет до всех точек — только после завершения маршрута `navigation_active` сбрасывался в `False`, и стоп ничего не делал.

## Коренная причина

В `stop_navigation_callback` была проверка:
```python
if not self.navigation_active:
    response.success = True
    response.message = "No active navigation"
    return response
```

Если `navigation_active` оказывался `False` (из-за `_result_callback`, `check_navigation` или отсутствия goal handle), стоп немедленно выходил, даже не пытаясь отменить goal.

## Исправление

Проверка `navigation_active` убрана — `stop_navigation_callback` всегда вызывает `cancel_navigation()`, которая сама проверяет наличие `_nav_goal_handle` и отменяет goal через `cancel_goal_async()`:

```python
def stop_navigation_callback(self, request, response):
    try:
        self.cancel_navigation()
        self.get_logger().info("Navigation stopped via /stop_navigation")
        response.success = True
        response.message = "Navigation stopped"
    except Exception as e:
        ...
    return response
```

Флаг `navigation_active` используется теперь только для:
- Индикации состояния (запрет повторного `/start_navigation`, пока активен)
- `navigate_to_waypoint_callback` — отмена предыдущей навигации перед новой
- Визуализации в логах

Сам `cancel_navigation()` остался без изменений:
```python
def cancel_navigation(self):
    if self._nav_goal_handle:
        self._nav_goal_handle.cancel_goal_async()
    self.navigation_active = False
```

---

# Шестая итерация: текстовые метки waypoints в RViz

## Проблема

После добавления TEXT_VIEW_FACING маркеров с номерами индексов (commit `9886b5e`)
метки не были видны в RViz.

## Коренные причины

1. **Белый текст на белой карте** — цвет текста был `(1.0, 1.0, 1.0)`, а map
   в RViz был включён и имел белый фон.
2. **Shared reference на Pose** — `text_marker.pose = wp.pose` присваивал
   ссылку на тот же объект Pose, а не копию. Из-за этого `position.z += 0.4`
   мутировало оригинальный waypoint.
3. **Дрифт позиции при каждом publish** — из-за shared reference каждый вызов
   `publish_markers()` добавлял ещё +0.4 к z-waypoint'а.

## Исправление

- Цвет текста теперь совпадает с цветом сферы (red/green/blue по индексу)
- Позиция копируется через независимые поля (не ссылка):
  ```python
  text_marker.pose.position.x = wp.pose.position.x + 0.3
  text_marker.pose.position.y = wp.pose.position.y
  text_marker.pose.position.z = wp.pose.position.z + 0.3
  text_marker.pose.orientation = wp.pose.orientation
  ```
- Текст смещён на +0.3 по x (вправо) и +0.3 по z (вверх), чтобы не
  перекрываться со сферой

Простое правило: в ROS 2 Python `msg.field = other.field` копирует ссылку,
а не значение. Для независимой копии нужно присваивать поля по одному
или использовать `copy.deepcopy`.

## Коммиты
- `9886b5e` — feat: добавить текстовые метки с номерами waypoints в RViz
  (оригинальная реализация, белый текст, дрифт)
- `7c4241b` — fix: исправить отображение номеров waypoints в RViz
  (цвет + offset + независимые поля)

---

# Седьмая итерация: возобновление навигации после остановки

## Проблема

После `make waypoint-stop` не было способа продолжить маршрут с прерванного
места — `make waypoint-start` начинал все waypoints сначала.

## Реализация

Добавлены:

1. **Сервис `/resume_navigation` (Trigger)** — принимает оставшиеся waypoints
   от `_resume_index` и отправляет их в FollowWaypoints.

2. **Отслеживание текущего waypoint** через `_feedback_callback` от
   FollowWaypoints:
   ```python
   def _feedback_callback(self, feedback_msg):
       self._current_waypoint_index = (
           self._resume_offset + feedback_msg.feedback.current_waypoint
       )
   ```

3. **`_resume_offset`** — смещение от начала `self.waypoints`, чтобы
   пересчитывать относительный индекс из feedback в абсолютный:
   - `start_navigation` → offset = 0
   - `resume_navigation` → offset = `_resume_index`
   - `navigate_to_waypoint` с idx → offset = idx (или 0 для -1)

4. **Makefile**: `make waypoint-resume` — вызывает `/resume_navigation`

## Баг: сброс resume после повторного stop

После первого stop → resume → stop, повторный resume снова начинал с waypoint 0.

Причина: `resume_navigation` отправлял **подмножество** waypoints
(`self.waypoints[self._resume_index:]`). FollowWaypoints в feedback отдавал
индекс **относительно** этого подмножества (0, 1, 2...). `cancel_navigation`
сохраняла этот относительный индекс как `_resume_index`, поэтому после
повторного stop `_resume_index` оказывался 0.

Исправление: введён `_resume_offset`, который хранит начало текущего
подмножества. Feedback складывается с offset, давая абсолютный индекс
в `self.waypoints`.

## Коммиты
- `ee3e542` — feat: добавить возобновление навигации после остановки
  (оригинальная реализация с багом offset)
- `6c31924` — fix: исправить resume после повторного stop
  (добавлен _resume_offset, вычисление абсолютного индекса)

---

# Восьмая итерация: загрузка waypoints из JSON-файла

## Проблема

Waypoints можно было расставлять только вручную кликами в RViz. Для
воспроизводимых сценариев нужна загрузка из файла.

## Реализация

1. **Новый сервис `LoadWaypoints.srv`** в `quadropted_msgs`:
   ```
   string file_path
   ---
   bool success
   string message
   ```

2. **Обработчик `load_waypoints_callback`**:
   - Читает JSON-файл по указанному пути
   - Конвертирует `yaw` в кватернион (`z = sin(yaw/2)`, `w = cos(yaw/2)`)
   - Создаёт `PoseStamped` для каждой точки
   - Публикует маркеры
   - Автоматически отменяет активную навигацию, если есть

3. **Формат JSON**:
   ```json
   [
     {"x": 2.5, "y": 1.0, "z": 0.0, "yaw": 0.0},
     {"x": 3.0, "y": 2.5, "z": 0.0, "yaw": 1.57}
   ]
   ```

4. **Makefile**: `make waypoint-load FILE=waypoints.json`
   - Путь в контейнере, например `/root/ws/waypoints.json`

5. **CMakeLists.txt** `quadropted_msgs` добавлен `LoadWaypoints.srv`

## Коммиты
- `370abb1` — feat: добавить загрузку waypoints из JSON-файла

---

# Девятая итерация: YAML вместо JSON, сервис GetWaypoints, публикация /custom_waypoints

## Изменения

### YAML для waypoints
- Файл `default.json` заменён на `default.yaml` с поддержкой комментариев
- `waypoint_collector.py` определяет формат по расширению: `.yaml`/`.yml` → `yaml.safe_load`, `.json` → `json.load`
- Дефолт: `default.yaml`

### Поиск директории конфигов
- `_get_waypoints_dir()` ищет `config/waypoints/`:
  1. В install tree: `script/../../share/gazebo_sim/config/waypoints/`
  2. В source tree: поднимается вверх от скрипта
  3. Legacy: `script/../config/waypoints/`

### Публикация /custom_waypoints (PoseArray)
- Теперь публикуется при каждом изменении списка (добавление, очистка, загрузка), а не только при старте навигации

### Новый сервис /get_waypoints
- Сообщение `quadropted_msgs/msg/Waypoint.msg`: `float64 x, y, z, yaw`
- Сервис `GetWaypoints.srv`: возвращает `Waypoint[] waypoints`
- Makefile: `make waypoint-get` с tab-разделённым выводом

### Автоподстановка расширения при загрузке
- Если в `FILE=` не указано расширение, скрипт пробует `.yaml`, затем `.json`
- `make waypoint-load FILE=test` → находит `test.yaml`

### Тестовый файл waypoints
- Создан `config/waypoints/test.yaml` с 3 точками для проверки загрузки

## Файлы
- `src/quadropted_msgs/msg/Waypoint.msg` — новое сообщение
- `src/quadropted_msgs/srv/GetWaypoints.srv` — новый сервис
- `src/quadropted_msgs/CMakeLists.txt` — добавлены Waypoint.msg и GetWaypoints.srv
- `src/gazebo_sim/config/waypoints/default.yaml` — новый формат
- `src/gazebo_sim/config/waypoints/test.yaml` — тестовый набор точек
- `src/gazebo_sim/scripts/waypoint_collector.py` — YAML-парсинг, GetWaypoints, автоподстановка расширения, /custom_waypoints при publish_markers()
- `Makefile` — `make waypoint-get`

## Коммиты
- `a314e64` — refactor: перейти с JSON на YAML для waypoints
- `cb28251` — feat: добавить сервис GetWaypoints и YAML для waypoints
