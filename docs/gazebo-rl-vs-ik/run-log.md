# Журнал прогонов — gazebo-rl-vs-ik

## 2026-10-09 (часть 1) — план и прототип

- Изучен Gazebo-стек: **gz-sim + gz_ros2_control**, робот из
  `go2_description/xacro/robot.xacro`, спавн `ros_gz_sim create`.
- Интерфейс: `joint_group_controller` (`JointGroupPositionController`),
  топик `/{ns}/joint_group_controller/commands` (`Float64MultiArray`, 12),
  100 Гц. Порядок: `rf, lf, rh, lh` x (`hip`, `upper_leg`, `lower_leg`).
- Созданы `plan.md`, `README.md`; написан прототип
  `src/gazebo_sim/scripts/go2_policy_gz.py`.
- **Offline self-test**: политика грузится, `obs 48 -> action 12` — OK.
- Имена суставов URDF совпадают с `JOINT_ORDER` — OK.

## 2026-10-09 (часть 2) — подъём Gazebo и первый прогон RL

### Подъём стека

- Контейнер `walking_robot_sim` поднят из готового образа
  (`docker compose -f compose.yml up -d`), **без пересборки**.
- Внутри: Python 3.12, **torch 2.14.1+cpu**, `gz sim` (ROS Jazzy),
  `gz_ros2_control`, `ros_gz_sim`, `gazebo_sim`, `go2_description`.
  Наш скрипт доступен через bind-mount `./src` → `/root/ws/src`.
- Self-test в контейнере — **OK**.

### Исправленные проблемы

1. **GUI Gazebo (Qt) падал** без дисплея → добавлен аргумент
   `gui:=false` в `src/gazebo_sim/launch/launch.launch.py`
   (headless: `gz sim -s`). `gazebo_sim` пересобран в контейнере.
2. **`/clock` не пробрасывался в ROS** (отсутствовал в
   `gz_bridge.yaml`) → `gz_ros2_control` писал
   «No clock received, using time argument instead», и **суставы не
   двигались**. Добавлен bridge `GZ_TO_ROS` для `/clock`. После этого
   `/clock` ~945 Гц, предупреждений нет, **суставы активировались**.

### Первый прогон RL-политики

- IK-узел (`robot_controller_node`) остановлен; запущен наш узел:
  `go2_policy_gz.py -p namespace:=robot1 -p vx:=0.3 -p use_sim_time:=true`.
- Узел публикует команды **50 Гц** в
  `/robot1/joint_group_controller/commands` (значения валидны).
- Робот **реагирует**: стронулся (x 0.05 → 0.23, z ≈ 0.27), затем
  **остановился** и ушёл вбок (y ≈ −0.6). Устойчивой ходьбы нет.

### Наблюдения (почему не идёт)

- `/robot1/odom` (Rust) отдаёт **twist = 0** → в наблюдение идёт нулевая
  линейная скорость.
- IMU (`/robot1/imu_plugin/out`, frame `imu_link`) даёт ориентацию
  **≈180° по X** (x≈0.998, w≈0.005) — вероятно, **смещение frame
  imu_link** относительно корпуса → в наблюдение попадает перевёрнутая
  гравитация.

### Гипотезы

1. **PD-гейны**: позиционный интерфейс не воспроизводит `kp=25 / kd=0.5`
   → нужен **effort + PD в узле** либо настройка гейнов.
2. **Наблюдение**: `lin_vel = 0` (odom) и/или смещение ориентации IMU.
3. **Sim-to-sim gap** (политика обучалась в PhysX).
4. Возможные знаки/дефолты суставов.

Добавлен параметр `imu_invert` (инверсия IMU) — быстрый тест, но без
сброса позы эффект не подтверждён.

### Дальше

1. Корректный источник **base velocity** (ground truth/odometry) и
   ориентации.
2. **Effort + PD (kp 25 / kd 0.5)** в узле — точное воспроизведение
   политики.
3. Проверить порядок/знаки суставов и default-позы.
4. Прогон, метрики, сравнение с IK.
