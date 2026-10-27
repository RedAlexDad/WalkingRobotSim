# ИМ оператора: новая RViz-конфигурация

**Файлы:**

- `rviz/im_operator.rviz` — конфигурация операторской ИМ (standalone, без симуляции);
- `rviz/im_operator_sim.rviz` — то же для запуска внутри симуляции;
- `im_publisher.py` — издатель карты, waypoints, пути, робота, статуса, события, кнопок и препятствия;
- `screenshots/im_state_*.png` — снимки состояний 3456×2160.

**Что реализовано:**

- карта кафе на `/cafe_map`;
- путь `/im_path` (текущая → следующая waypoint);
- waypoints `/im_waypoints`: текущая 8, следующая 1 (синяя), остальные серые;
- робот `/im_robot`: прямоугольный footprint 0,73×0,36 м и стрелка курса; поза берётся из `/robot1/odom`;
- статус `/im_status`: режим, пара WP, состояние, статус робота, связь;
- событие `/im_event`: тип, причина, действие, дедлайн;
- подтверждение `/im_confirm`: кнопки `CONFIRM` / `CANCEL` (только в `confirm` и `stuck`);
- препятствие: L-образный контур 0,90×0,55 м, а не точка;
- легенда: CURRENT / NEXT / OTHER / PATH / OBSTACLE;
- waypoints и текущая цель — из `/waypoint_state` коллектора, а не из файла: пока список пуст, ИМ не рисует точки и показывает `WP: NONE`.

## Запуск без симуляции

```bash
cd ~/GitHub/WalkingRobotSim
source /opt/ros/lyrical/setup.bash
python3 experiments/ergonomics_rviz/im_publisher.py \
  --ros-args -p text_scale:=0.76
```

Во втором терминале:

```bash
cd ~/GitHub/WalkingRobotSim
source /opt/ros/lyrical/setup.bash
rviz2 -d experiments/ergonomics_rviz/rviz/im_operator.rviz
```

Без одометрии маркер робота стоит на текущей waypoint и печатает предупреждение в лог: это заглушка, а не измеренная поза.

## Запуск с реальной симуляцией

Одной командой:

```bash
make gazebo RVIZ=ergonomic
```

`RVIZ` принимает:

| Значение | Поведение |
|---|---|
| `default` (по умолчанию) | штатный RViz из launch |
| `false` | без RViz |
| `ergonomic` | полноэкранный RViz с этой ИМ + издатель ИМ |
| `<путь>.rviz` | любой конфиг; RViz стартует отдельно, издатель не запускается |

`make gazebo RVIZ=ergonomic` копирует `rviz/im_operator_sim.rviz` и `im_publisher.py` в контейнер, поднимает издатель с `use_sim_time:=true`, запускает `rviz2 --fullscreen` с ремапами `/tf`, `/tf_static` и `__ns:=/robot1`, а после выхода из симуляции гасит оба процесса. Если make прерван по Ctrl+C, хвосты убирает `make rviz-kill`.

Ручной запуск (для отладки):

```bash
make gazebo RVIZ=false
```

```bash
docker cp experiments/ergonomics_rviz/im_publisher.py walking_robot_sim:/tmp/
docker cp experiments/ergonomics_rviz/rviz/im_operator_sim.rviz walking_robot_sim:/tmp/

docker exec -it walking_robot_sim bash
source /opt/ros/jazzy/setup.bash
source /root/ws/install/setup.bash

python3 /tmp/im_publisher.py \
  --map-yaml /root/ws/install/gazebo_sim/share/gazebo_sim/maps/cafe_world_map.yaml \
  --waypoints-yaml /root/ws/install/gazebo_sim/share/gazebo_sim/config/waypoints/default.yaml \
  --ros-args -p use_sim_time:=true -p text_scale:=0.76 &

rviz2 --fullscreen -d /tmp/im_operator_sim.rviz --ros-args \
  -p use_sim_time:=true \
  -r __ns:=/robot1 \
  -r /tf:=tf \
  -r /tf_static:=tf_static
```

`RobotModel` и `LaserScan` в конфиге выключены: `RobotModel` дублирует footprint и спорит с ним по позе, пока `/tf` не даёт ту же позу, что `/odom`.

## Состояния

Состояние переключается сообщением в `/im_state` (`std_msgs/String`):

```bash
ros2 topic pub --once /im_state std_msgs/msg/String "{data: normal}"
ros2 topic pub --once /im_state std_msgs/msg/String "{data: confirm}"
ros2 topic pub --once /im_state std_msgs/msg/String "{data: confirmed}"
ros2 topic pub --once /im_state std_msgs/msg/String "{data: cancelled}"
ros2 topic pub --once /im_state std_msgs/msg/String "{data: stuck}"
```

| Состояние | Панель события | Кнопки | ROBOT | Препятствие |
|---|---|---|---|---|
| `normal` | зелёная `SYSTEM NOMINAL` | скрыты | `READY` | нет |
| `confirm` | красная `CONFIRMATION_REQUIRED` | видны | `WAITING` | нет |
| `confirmed` | зелёная `CONFIRMED` | скрыты | `CONFIRMED` | нет |
| `cancelled` | янтарная `CANCELLED` | скрыты | `HOLD` | нет |
| `stuck` | красная `STUCK_AT_OBSTACLE` | видны | `BLOCKED` | L-контур |

`confirmed` не двигает робота и не переключает пару waypoints. Переключение 8→1 должно происходить по факту прибытия, то есть по координате из `/odom`, а не по нажатию.

## Значения, которые заложены

| Параметр | Значение | Почему |
|---|---|---|
| Масштаб вида | 120 px/м | окно 3456×2160; при 120 px/м карта 22,35 м выше экрана, поэтому виден рабочий участок со всеми 8 WP |
| Текст панелей | `text_scale = 0.76 м` | глиф 0,54 м; при 290 PPI и 700 мм это 27,8′ |
| Вторичный текст | `0.8 × text_scale = 0,61 м` | 22,3′ |
| Кнопки | 3,8×1,5 м | 456×180 px = 39,9×15,8 мм, больше 11,64 мм |
| Путь | тёмно-зелёный `0;102;0`, 0,06 м | K = 0,890 на белой карте |
| Текущая WP / робот | тёмно-оранжевый `199;99;0` | K = 0,756 |
| Следующая WP | синий `0;128;255` | K = 0,738 |
| Остальные WP | серый `140;140;140` | K = 0,696 |
| Препятствие | тёмно-красный `158;13;13` | K = 0,912, форма видна |
| Панели | тёмный фон, белый текст | K = 0,995, CR = 19,3 |
| Слои | карта, путь, waypoints, робот, статус, событие, подтверждение | без costmap/TF/отладки |

## Ограничения

1. **Кнопки `CONFIRM` / `CANCEL` — визуальные маркеры, не кликабельные.** Для реального подтверждения нужен custom RViz panel или внешний пульт.
2. **Препятствие задано вручную**: динамических препятствий в сцене нет. В реальной системе контур должен приходить из costmap или кластера.
3. **Путь `/im_path` — отрезок между waypoints**, а не результат планировщика. В реальной системе нужно `/plan`.
4. **`P_ош`, `t_ип`, `K_загр` не проверены**: нужен пилот.
5. Цвета и размеры проверены расчётом по пикселям снимка, но не пилотом.

## Настройка

Параметры издателя:

```bash
-p text_scale:=0.76
-p current_id:=8
-p next_id:=1
-p state:=normal
-p odom_topic:=/robot1/odom
-p source:=ros          # ros — /waypoint_state; demo — default.yaml (офлайн)
```

Для 96 PPI можно поставить `text_scale:=0.45`; для 189 PPI — `0.76`.
