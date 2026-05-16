# Устранение дрифта одометрии в Python контроллере

## Текущая ветка
`fix/python-odometry-drift`

## Цель
Привести Python launch (`gazebo_multi_nav2_world.launch.py`) к паритету с C++
launch (`gazebo_multi_nav2_cpp.launch.py`) в части одометрии и навигации.

---

## План

### Шаг 1: IMU топик в одометрии
**Проблема**: Python odometry подписан на `/{namespace}/imu` (строка 210),
но Gazebo bridge публикует IMU в `/{namespace}/imu_plugin/out` (строка 139).
Одометрия не получает IMU → дрифт.

**Решение**: Исправить `imu_topic` на `/{namespace}/imu_plugin/out`.

**Файлы**: `gazebo_multi_nav2_world.launch.py:210`

---

### Шаг 2: enable_odom_tf
**Проблема**: `enable_odom_tf: True` (строка 214) — одометрия сама публикует
`odom→base_link` TF. Но EKF (robot_localization) тоже публикует этот TF.
Конфликт приводит к дёрганью и дрифту. В C++ версии `enable_odom_tf: False`,
TF публикует только EKF.

**Решение**: Выставить `enable_odom_tf: False`.

**Файлы**: `gazebo_multi_nav2_world.launch.py:214`

---

### Шаг 3: waypoint_collector
**Проблема**: В Python launch нет `waypoint_collector`. В C++ (строка 320-328)
он добавлен.

**Решение**: Добавить `waypoint_collector` Node в `robot_group`.

**Файлы**: `gazebo_multi_nav2_world.launch.py`

---

### Шаг 4: Проверка EKF конфига
**Проблема**: Возможно, `config/ekf.yaml` настроен для C++ топиков
(IMU топик, odom топик). Нужно проверить соответствие.

**Решение**: Сверить параметры EKF в `config/ekf.yaml` с тем, что реально
публикуется в Python версии.

**Файлы**: `config/ekf.yaml`

---

### Шаг 5: Проверка ros2 topic list после gazebo-py
**Проблема**: Может не хватать каких-то топиков/трансформаций, которые есть
в C++ версии.

**Решение**: Запустить `gazebo-py`, собрать `ros2 topic list` и `ros2 tf echo`,
сравнить с ожидаемым набором.

---

### Шаг 6: Тестирование навигации
**Проблема**: Дрифт может быть вызван не только одометрией, но и
неправильной начальной позицией (initial pose), loss of localization.

**Решение**: После исправления IMU и TF — проверить `make waypoint-start`
с тестовыми waypoints, убедиться что робот едет без дрифта.

---

## Результат

### Реальная причина дрифта
Дрифт **не был связан** с IMU топиком или `enable_odom_tf`.

**Первичная причина** — **circular import** в `QuadrupedOdometry/__init__.py`:
- Импорт `from .node_main import MainLoop` стоял до `from .odometry_update import update_odometry`
- `node_main.py` делает `from QuadrupedOdometry import update_odometry` — но модуль ещё не инициализирован
- → `QuadrupedOdometryNode.py` падает при старте: `ImportError: cannot import name 'update_odometry'`
- → нет топика `odom` → EKF не публикует TF → Nav2 не получает `base_link → odom` → нет траекторий

**Вторичная причина** — переписанный `local_positions.py`:
- Изменён формат выхода с `(4,3)` (строки = ноги) на `(3,4)` (столбцы = ноги)
- `compute_all_joint_angles` пытался обработать оба формата через `is_new_format`
- Контроллеры (StandController, TrotGaitController) продолжали передавать `(4,3)` → некорректные joint angles

### Что было исправлено
1. **IMU топик** — `/{ns}/imu` → `/{ns}/imu_plugin/out` (параметр в launch, node использует хардкод)
2. **enable_odom_tf** — `True` → `False` (EKF публикует TF, не дублировать)
3. **waypoint_collector** добавлен в Python launch
4. **quadropted_controller заменён на main** — исправлен circular import, возвращён рабочий IK

### Коммиты
```
48cc83b fix: исправить IMU топик и отключить дублирование TF в Python launch
c74b5e1 feat: добавить waypoint_collector в Python launch
ef9d9b1 refactor: заменить quadropted_controller на версию из main
```

### Методика
- Каждый шаг = отдельный коммит
- После каждого шага — тест (`make gazebo-py`)
- Отчёт дополняется в `docs/waypoint-executor-fix.md`
- По завершению — переключиться на `main` и смержить ветку
