# Сравнение RL-политики и IK/TROT в Gazebo

**Дата:** 2026-10-09
**Область:** **только Gazebo** (gz-sim). MuJoCo и Isaac Sim **не
рассматриваем** как среду — они остаются лишь источниками «рецепта»
наблюдений и данных политики.
**Цель:** сравнить обученную RL-политику и модельный IK/TROT-контроллер
на одном роботе Unitree Go2, в одном симуляторе (Gazebo), через один
низкоуровневый интерфейс суставов.

---

## 1. Стек Gazebo (факты из репозитория)

| Компонент | Значение |
|---|---|
| Симулятор | **gz-sim (Ignition)**, запуск через `ros_gz_sim/gz_sim.launch.py` |
| Контроль | **gz_ros2_control** (`GazeboSimROS2ControlPlugin`) + `ros2_control` |
| Модель | `src/go2_description/xacro/robot.xacro` |
| Спавн | `ros_gz_sim create` (из `/{ns}/robot_description`) |
| Интерфейс | позиционный: `joint_group_controller` (`JointGroupPositionController`) |
| Топик команд | `/{ns}/joint_group_controller/commands` (`std_msgs/Float64MultiArray`, 12 углов) |
| Частота контроллера | 100 Гц |
| Порядок суставов | `rf, lf, rh, lh` × (`hip`, `upper_leg`, `lower_leg`) |

Топики (namespace `robot1`):

- IMU: `/robot1/imu_plugin/out` (`sensor_msgs/Imu`)
- Состояние суставов: `/robot1/joint_states` (`sensor_msgs/JointState`)
- Одометрия: `/robot1/odom` (Rust `odometry_node`), `/robot1/odometry/filtered` (EKF)
- Ground truth поза: `/robot1/pose_ground_truth`, `/world/default/dynamic_pose/info`
- Команда: `cmd_vel` (`geometry_msgs/Twist`)

IK/TROT-узел `quadropted_controller_rust/robot_controller_node` публикует в
тот же топик команд и подписан на `imu`, `robot_velocity`, `robot_mode`.
**Это и есть шов:** RL-узел встаёт на его место, интерфейс не меняется.

## 2. Что переносим из политики (без запуска Isaac/MuJoCo)

- Модель: `src/isaac/assets/Isaac/Samples/Policies/go2/physx_policy.pt`
  (TorchScript, CPU, **48 наблюдений → 12 действий**).
- Рецепт наблюдений — по `src/mujoco/go2_policy_mj.py` (используется только
  как спецификация, MuJoCo не запускаем).
- Параметры: `action_scale = 0.25`, `kp = 25`, `kd = 0.5`,
  default-позы по звеньям, decimation → **50 Гц**.

## 3. Вектор наблюдений (48)

`[ lin_vel_body(3), ang_vel_body(3), gravity_body(3), cmd(3),
(q − q_def)(12), dq(12), last_action(12) ]`

- `lin_vel_body` — из одометрии (или ground-truth поза);
- `ang_vel_body` — из IMU;
- `gravity_body = R^T · [0, 0, −1]` — из ориентации IMU;
- `cmd` — целевые $v_x, v_y, \omega_z$;
- `q, dq` — из `/robot1/joint_states` (сопоставление по именам);
- `last_action` — предыдущий выход политики.

## 4. Архитектура RL-узла

Новый узел `go2_policy_gz.py` (rclpy):

- подписки: `joint_states`, `imu_plugin/out`, `odom`, `cmd_vel`;
- загрузка `physx_policy.pt`;
- публикация `target = q_def + 0.25 · action` в
  `joint_group_controller/commands`;
- такт **50 Гц** на **sim-time** (не wall-clock — иначе повторится дефект
  P1 из статьи);
- сопоставление суставов по именам; порядок контроллера `rf, lf, rh, lh`.

## 5. Ключевые вопросы и риски

| Вопрос | Комментарий |
|---|---|
| **PD-гейны** | Текущий интерфейс позиционный; нужно задать гейны как у политики (kp 25 / kd 0.5) либо перейти на **effort** и считать момент в узле ($\tau = kp(q^*-q) - kd\,\dot q$) — точнее воспроизводит политику |
| **base lin vel** | В Gazebo нет прямого base-twist; брать из `odom` (body) или ground-truth (дифференцирование) |
| **sim-to-sim gap** | Политика обучена в PhysX; в Gazebo контакты/трение иные → возможна деградация; при провале — fine-tune/гейны/трение |
| **joint naming/order/signs** | `upper_leg`=thigh, `lower_leg`=calf; `rh`=RR, `lh`=RL; проверить знаки hip |
| **torch в ROS-python** | в системном python `torch` нет (есть в `.venv-mujoco`); нужно обеспечить зависимость для узла |

## 6. Метрики и протокол (как в статье)

- Единый URDF, ровная поверхность, одна команда $v_x$ (0.3 м/с),
  одинаковая длительность и число прогонов, **sim-time**.
- Метрики: средняя скорость, путь, $Z$ (mean/std), max roll/pitch, дрейф
  $|Y|$, CoT, падения, время до устойчивой походки.
- Общая телеметрия (по образцу `src/isaac/telemetry.py`) — для обоих
  контроллеров.

## 7. Этапы

1. ✅ План (этот документ).
2. ⏳ **Прототип** `go2_policy_gz.py` + self-test (загрузка политики,
   сборка obs).
3. ⏳ Запуск в Gazebo: стоит/идёт.
4. ⏳ При деградации — effort + PD (или подбор гейнов/трения).
5. ⏳ Телеметрия Gazebo.
6. ⏳ Серия RL vs IK, метрики, отчёт.

## 8. Команды (черновик)

```bash
# 1) поднять Gazebo (Rust-контроллер) — проверка сцены
ros2 launch gazebo_sim launch.launch.py

# 2) вместе с прототипом RL (пример)
python3 src/gazebo_sim/scripts/go2_policy_gz.py --ros-args -p namespace:=robot1 -p vx:=0.3

# 3) оффлайн self-test (без Gazebo): загрузка политики и obs
.venv-mujoco/bin/python src/gazebo_sim/scripts/go2_policy_gz.py --selftest
```

## 9. Ограничения

- Только Gazebo; MuJoCo и Isaac Sim как среда исключены.
- Политика готовая (NVIDIA), нами не обучалась.
- Сравнение при «родных» настройках; выравнивание PD — отдельный вопрос
  (см. §5).
