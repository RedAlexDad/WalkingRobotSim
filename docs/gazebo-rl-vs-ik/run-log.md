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

## 2026-10-11 — подтверждение нулевого переноса и выбор пути

**Наш стек с GPU и GUI.** Контейнер `walking_robot_sim` поднят с
проброшенным AMD iGPU (`/dev/dri`, `compose.gpu.yml`) для GUI. В
`src/gazebo_sim/launch/sim_minimal.launch.py` добавлен аргумент
**`gui:=true`** (по умолчанию headless). Сцена — `flat.world`, режим
**effort**, `vx = 0.3`, окно Gazebo открывается.

**Наша NVIDIA-политика в нашем gz-sim — оседает.** Замер за 8 с
(~21 с после спавна):

| Показатель | Значение | Норма |
|---|---|---|
| `z` базы | mean **0.098** м, min 0.078, max 0.143 | ~0.30 |
| `dx` | +0.035 м | растёт при ходьбе |
| `dy` | **+0.41 м** (дрейф боком) | ≈0 |
| roll / pitch | −1.3° / −4.9° | ~0 |

Робот лежит на «животе» (база ~0.10 м) и смещается боком — походки
нет. Это **повторное подтверждение** нулевого переноса PhysX → gz-sim
(см. отчёт от 2026-10-09).

**Rust-TROT в этом же мире работает** стабильно (по движку и сцене —
без изменений). Значит окружение исправно, а разрыв — именно
«политика ↔ физика gz-sim».

**Отдельно (не наш Rust-TROT):** автономный Python IK-gateway
(`/tmp/trot_ik.py`) в rl_sar (Gazebo Classic) при попытке trot уходил
**назад** при любом знаке страйда: `+0.25 → dx≈−1.40`, `−0.25 → −1.88`,
`+0.18 → назад`, `−0.18 → −0.82`; траектория по образцу Webots-проекта —
`−1.69`. Причина — несовпадение знаков/конвенций приводов, а не
кинематика Rust-контроллера. Направление этой веткой не лечится.

**Решение.** Выбран **путь 2** — обучение политики с
**domain randomization** в GPU-симуляторе и **перенос** в gz-sim.
План и окружение:

- `docs/gpu-rl-training/plan.md` — среда, выбор фреймворка, метод,
  этапы, риски.
- `docs/gpu-rl-training/environment.md` — факты окружения.

**Окружение (факты).** GPU RTX 5070 Ti (Blackwell, `sm_120`), драйвер
595.91.07, CUDA 13.2 (runtime) / 13.1 (nvcc), 16 ГБ; `nvidia` runtime
в Docker; `uv` доступен. Ограничение `sm_120` задаёт требования к
свежести сборок фреймворков.

### Артефакты (2026-10-11)

- `src/gazebo_sim/launch/sim_minimal.launch.py` — аргумент `gui:=true`.
- `docs/gpu-rl-training/README.md`, `plan.md`, `environment.md`.
