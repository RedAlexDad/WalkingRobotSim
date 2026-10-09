# Журнал прогонов — gazebo-rl-vs-ik

## 2026-10-09 (часть 1) — план и прототип

- Изучен Gazebo-стек: **gz-sim + gz_ros2_control**, робот из
  `go2_description/xacro/robot.xacro`, спавн `ros_gz_sim create`.
- Интерфейс: `joint_group_controller` (`JointGroupPositionController`),
  топик `/{ns}/joint_group_controller/commands` (`Float64MultiArray`, 12).
  Порядок: `rf, lf, rh, lh` x (`hip`, `upper_leg`, `lower_leg`).
- Созданы `plan.md`, `README.md`; написан прототип
  `src/gazebo_sim/scripts/go2_policy_gz.py`.
- Offline self-test: `obs 48 -> action 12` — OK.

## 2026-10-09 (часть 2) — подъём, исправления, прогоны RL

### Инфраструктура

- Контейнер `walking_robot_sim` поднят из готового образа (без
  пересборки). Внутри: Python 3.12, **torch 2.14.1+cpu**, `gz sim`,
  `gz_ros2_control`, `ros_gz_sim`. Скрипт доступен через bind-mount
  `./src` → `/root/ws/src`.
- Исправление **headless**: добавлен `gui:=false` в
  `src/gazebo_sim/launch/launch.launch.py` (`gz sim -s`).
- Исправление **`/clock`**: добавлен GZ→ROS bridge в
  `src/gazebo_sim/config/gz_bridge.yaml` — без него `gz_ros2_control`
  не двигал суставы.
- Добавлен `gz-sim-odometry-publisher-system` (плагин) + bridge
  `/model/robot1_my_bot/odometry` → `/robot1/odom_gz`.
- Добавлен **effort-интерфейс** суставов (`gazebo.xacro`) и
  `joint_group_effort_controller` (`ros_control.yaml`).

### Ключевая правка

- **Порядок суставов политики ≠ порядку контроллера Gazebo.**
  Политика (IsaacLab/NVIDIA Go2): **FL, FR, RL, RR**; контроллер:
  **FR, FL, RR, RL** (`rf, lf, rh, lh`). Введена перестановка `PERM`
  в узле. Без неё робот кувыркался; после — начал двигаться.

### Результаты прогонов (effort + PD, kp=25, kd=0.5)

- Робот **управляем**: стоит на высоте ≈0.28 м, суставы двигаются,
  команды идут 50 Гц (`/robot1/joint_group_effort_controller/commands`).
- **В одном прогоне — поступательное движение вперёд**: x 0.05 → **3.6 м**
  за ~10 с (≈0.36 м/с при команде 0.3 м/с).
- В остальных прогонах — **круговое/дрейфующее** движение (не устойчивая
  прямолинейная ходьба).

### Что пробовали

- `control_mode=effort` (PD в узле) vs `position` (интерфейс
  контроллера) → effort даёт управляемое движение.
- `hip_sign=-1` → робот стабилизируется в стойку, но не идёт.
- `odom_gz` (истинная скорость) vs нулевая скорость → устойчивой
  ходьбы не даёт ни то, ни другое.

### Вывод

Порт предобученной политики из **PhysX (Isaac)** в **gz-sim** работает
**частично**: цепочка управления налажена, робот управляем, но политика
не даёт устойчивой походки (sim-to-sim gap: контакты/трение/демпфирование
иные). Дальнейшие шаги: подбор PD/демпфирования/трения, проверка знаков
суставов, при необходимости — fine-tune политики в Gazebo.

### Артефакты

- `src/gazebo_sim/scripts/go2_policy_gz.py` — узел (режимы position/effort,
  перестановка суставов, `imu_invert`, `hip_sign`, `odom_gz`).
- Правки: `launch.launch.py`, `gz_bridge.yaml`, `gazebo.xacro`,
  `ros_control.yaml`.

## 2026-10-09 (часть 3) — сверка с rl_sar и правки

- Найдены готовые решения (см. `existing-solutions.md`): **rl_sar**,
  Go2Arm_sim2sim, legged_gym_gazebo, quadruped-robotics-stack.
- Разобран **rl_sar** (`rl_sim.cpp`): control-loop **200 Гц**
  (`dt=0.005`, `decimation=4`), политика — 50 Гц; шлёт **целевую позу +
  kp/kd по каждому суставу** (свой `robot_joint_controller`); есть
  `joint_mapping`; `ang_vel` в body.
- **Внесено** в `go2_policy_gz.py`: PD считается на **200 Гц**
  (политика — 50 Гц, `POLICY_DECIMATION=4`) — раньше PD был 50 Гц.
- **Ограничение среды**: headless gz-sim на CPU — низкий real-time
  factor / высокая нагрузка; фактический поток команд ≈17 Гц вместо 200,
  замеры нестабильны. Для полноценной оценки ходьбы нужна ускоренная
  симуляция (GPU) либо существенно больше времени.

### Промежуточный вывод

Порт методологически верен (сверено с `physx_env.yaml` и rl_sar);
остаточная проблема — **sim-to-sim gap** + производительность
симуляции в текущем окружении. Практические варианты — взять rl_sar
(Gazebo Classic) / quadruped-robotics-stack (gz-sim8) или обучать
политику сразу в Gazebo.
