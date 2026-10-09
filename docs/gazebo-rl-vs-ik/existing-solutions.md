# Существующие решения RL-локомоции в Gazebo

**Дата:** 2026-10-09
**Назначение:** обзор готовых проектов «RL-политика для четвероногого
робота в Gazebo», чтобы не изобретать решение и сверить наш подход.

---

## 1. Найденные проекты

| Проект | Что делает | Среда |
|---|---|---|
| **fan-ziqi/rl_sar** | Фреймворк «sim & real»: RL-политики для **Unitree Go2** в **Gazebo**, MuJoCo и на железе (IsaacGym/IsaacSim, libtorch/onnx). Готовые конфиги `policy/go2/*` | Gazebo **Classic**, ROS2 Humble/Foxy |
| **zzzJie-Robot/Go2Arm_sim2sim** | **IsaacLab → Gazebo** для legged-манипулятора (Go2 + arm) | ROS Noetic, Gazebo |
| **mertgungor/legged_gym_gazebo** | «Interface to run trained quadruped model in Gazebo» (legged_gym → Gazebo) | — |
| **darshmenon/quadruped-robotics-stack** | Go2 RL-локомоция в **Gazebo Harmonic (gz-sim8)** + MuJoCo; native `JointPositionController` + `ros_gz_bridge` | ROS2 Humble, **gz-sim8** (как у нас) |
| **shaoxiang/awesome-unitree-robots** | Кураторский список (Isaac/MuJoCo/Gazebo/RL) | — |

Ссылки:
- https://github.com/fan-ziqi/rl_sar
- https://github.com/zzzJie-Robot/Go2Arm_sim2sim
- https://github.com/mertgungor/legged_gym_gazebo
- https://github.com/darshmenon/quadruped-robotics-stack
- https://github.com/shaoxiang/awesome-unitree-robots

## 2. Ключевые уроки

### 2.1. Порядок действий и PD (прямое подтверждение)

В `Go2Arm_sim2sim` (перенос IsaacLab → Gazebo) прямо сказано:

> «Порядок действий, которые выводит модель, должен совпадать с порядком
> в этом проекте, а также совпадать с **PD-параметрами моторов**».

Reference-контроллер — **rl_sar**. Это ровно две проблемы, которые мы
встретили при порте.

### 2.2. Конфиги rl_sar для Go2

`policy/go2/base.yaml`:
- порядок суставов: **FR, FL, RR, RL** (`FR_hip, FR_thigh, FR_calf, ...`);
- `dt = 0.005`, `decimation = 4` → **50 Гц**;
- `fixed_kp/kd = 80/3`, `rl_kp/kd = 20/0.5` (robot_lab) или `40/1`
  (himloco);
- `default_dof_pos = [0, 0.8, -1.5]` на каждую ногу;
- `torque_limits = 23.5`.

`policy/go2/robot_lab/config.yaml`:
- наблюдения: `[ang_vel, gravity_vec, commands, dof_pos, dof_vel, actions]`
  (45 значений, без `lin_vel`);
- `action_scale` **разный по суставам**: hip 0.125, thigh/calf 0.25;
- масштабы obs: `lin_vel 2.0`, `ang_vel 0.25`, `dof_pos 1.0`,
  `dof_vel 0.05`.

### 2.3. Наш конфиг (`physx_env.yaml`, NVIDIA-политика)

- наблюдения: `[base_lin_vel, base_ang_vel, projected_gravity,
  commands, joint_pos_rel, joint_vel_rel, last_action]` = **48**, без
  масштабов — **совпадает с нашим `build_obs`**;
- `action_scale = 0.25` (равномерно), `stiffness = 25`, `damping = 0.5`,
  `effort_limit = 23.5`, `velocity_limit = 30`;
- `default`: L-hip **+0.1**, R-hip **−0.1**, front thigh `0.8`, rear
  thigh `1.0`, calf `−1.5`.

## 3. Выводы

1. **Наш порт методологически верен**: порядок наблюдений, `action_scale`,
   PD-гейны и дефолтная стойка совпадают с эталонным конфигом.
2. «Круговое» поведение в gz-sim — это классический **sim-to-sim gap**
   (политика обучена в **PhysX**, Gazebo считает контакты/трение иначе),
   плюс возможные различия в порядке суставов конкретного USD-ассета.
3. **Gazebo-RL у Go2 — известная «капризная» задача**: даже у
   `quadruped-robotics-stack` Gazebo-бэкенд работает частично (робот
   реагирует на `/cmd_vel`, но скорость ≈25% от заданной; в roadmap —
   «нужна настройка походки»).
4. **Практические пути:**
   - взять **rl_sar** (готовый Go2 в Gazebo), но там **Gazebo Classic**,
     а у нас **gz-sim**;
   - ориентироваться на **quadruped-robotics-stack** (ближайший: gz-sim8);
   - надёжнее — **обучать политику прямо в Gazebo** (как делает
     `quadruped-robotics-stack`) — тогда sim-to-sim gap устраняется.

## 4. Что из этого следует для проекта

- Реалистично получить устойчивую ходьбу «простым портом» PhysX-политики в
  gz-sim **не гарантируется** — это согласуется с опытом сообщества.
- Для статьи/ВКРМ это, скорее, **самоценный результат** (sim-to-sim
  переносимость), чем тупик.

---

## 5. Практическая попытка взять rl_sar / quadruped-robotics-stack

**rl_sar** — склонирован с сабмодулями (`git submodule update --init
--recursive`). Окружение собирается **только целиком через свой Docker**
(ROS2 **Humble** + **Gazebo Classic** + libtorch + MuJoCo). Сборка образа
запущена и **упала** на шаге `./build.sh`:
`[ERROR] Cannot download robot descriptions in offline mode`
`[ERROR] Failed to setup robot descriptions`
(нужны дополнительные загрузки описаний роботов в сети/сабмодулях; отладка
— отдельная задача). Вывод: rl_sar — это отдельный тяжёлый контейнер, не
наш gz-sim-стек.

**quadruped-robotics-stack** — склонирован. Полезное из их конфигов
(стек **тот же — gz-sim8 + gz_ros2_control**, что и у нас):

- контроллер — **позиционный** (`position_controllers/
  JointGroupPositionController`), `update_rate = 200`;
- **порядок суставов — FL, FR, RL, RR** (FL первым);
- для стойки — нативные gz `JointPositionController` по суставам
  (`/go2/cmd/<joint>`, `std_msgs/Float64`), мосты через `ros_gz_bridge`;
- политика **обучается прямо в Gazebo** (`training/envs/
  go2_gazebo_env.py`, SB3) — поэтому у них нет sim-to-sim gap;
- их же заметка: фактическая скорость ≈25% заданной, «нужна настройка
  походки».

## 6. Наши эксперименты (сводка)

В `docs/gazebo-rl-vs-ik/run-log.md` и `performance-assessment.md`:

- порядок суставов: пробовали **FL-first** (как quadruped) и **FR-first**
  (как rl_sar) — не помогло;
- интерфейс: **position** и **effort+PD** — не помогло;
- при **RTF ≈ 1.0** (минимальный launch) NVIDIA-политика всё равно
  **оседает** (z ≈ 0.1) и дрейфует.

**Итог:** прямой перенос предобученной **PhysX**-политики в **gz-sim**
рабочей походки не даёт (sim-to-sim gap), независимо от порядка/интерфейса
и производительности. Надёжные пути: **обучать политику прямо в Gazebo**
(подход quadruped-robotics-stack) либо запускать **готовое окружение
rl_sar** (Gazebo Classic, своя политика).
