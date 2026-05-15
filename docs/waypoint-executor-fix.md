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
