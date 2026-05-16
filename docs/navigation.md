# Waypoint навигация

Система навигации по точкам маршрута на базе Nav2 waypoint_follower и кастомного RViz инструмента.

---

## Компоненты

### waypoint_collector (Python, quadropted_controller)

Узел для сбора и управления waypoints:

- Сервис `/get_waypoints` — отдаёт текущий список waypoints
- Интеграция с Nav2 `waypoint_follower`
- Загрузка waypoints из YAML/JSON файлов
- Хранение в папке `src/gazebo_sim/config/waypoints/`

### rviz_waypoint_tool

Кастомный RViz плагин. Расстановка waypoints кликами мыши на 2D карте. Каждая точка содержит позицию (x, y, z) и ориентацию (yaw).

### Nav2 waypoint_follower

Асинхронный ActionServer `FollowWaypoints`. Принимает массив waypoints и последовательно отправляет робота к каждому, используя Nav2 planner/controller.

---

## Основные сценарии

### Расстановка точек в RViz

1. Запустить симуляцию: `make gazebo-py`
2. Открыть RViz (открывается автоматически)
3. Использовать `WaypointTool` на панели инструментов RViz
4. Кликать по карте для добавления waypoints

### Запуск навигации

```bash
make waypoint-start
# или
make waypoint-navigate
```

### Управление

| Команда | Действие |
|---------|----------|
| `make waypoint-start`   | Загрузить способность и запустить навигацию |
| `make waypoint-navigate` | Начать или продолжить навигацию |
| `make waypoint-stop`    | Остановить (прогресс сохраняется) |
| `make waypoint-resume`  | Продолжить с прерванной точки |
| `make waypoint-clear`   | Очистить все waypoints |
| `make waypoint-load FILE=test` | Загрузить из файла |
| `make waypoint-get`     | Показать текущие точки |

---

## Формат файла waypoints

YAML (список):
```yaml
- # 1
  x: 2.33
  y: -3.46
  z: 0.0
  yaw: 0.0
- # 2
  x: -0.5
  y: -2.0
  z: 0.0
  yaw: 1.57
```

Файлы хранятся в `src/gazebo_sim/config/waypoints/`.

---

## Зависимости

- Nav2 (waypoint_follower, controller_server, planner_server, bt_navigator)
- TF2
- AMCL (локализация на карте)
- rviz_waypoint_tool (кастомный плагин)

---

## Ссылки

- [Waypoint executor fix](../reports/waypoint-executor-fix.md) — процесс разработки и отладки
- [Waypoint collector report](../reports/waypoint-collector-fix-report.md) — краткий отчёт
