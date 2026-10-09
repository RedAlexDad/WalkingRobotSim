# Журнал прогонов — gazebo-rl-vs-ik

## 2026-10-09

- Изучен Gazebo-стек: **gz-sim + gz_ros2_control**, робот из
  `go2_description/xacro/robot.xacro`, спавн `ros_gz_sim create`.
- Интерфейс: `joint_group_controller` (`JointGroupPositionController`),
  топик `/{ns}/joint_group_controller/commands` (`Float64MultiArray`, 12),
  100 Гц. Порядок: `rf, lf, rh, lh` x (`hip`, `upper_leg`, `lower_leg`).
- Топики: IMU `/{ns}/imu_plugin/out`, `/{ns}/joint_states`,
  `/{ns}/odom`, ground-truth поза; IK/TROT — `robot_controller_node`.
- Созданы `plan.md`, `README.md`.
- Написан прототип `src/gazebo_sim/scripts/go2_policy_gz.py`.
- **Offline self-test** (`.venv-mujoco/bin/python ... --selftest`):
  политика `physx_policy.pt` грузится, `obs 48 -> action 12`,
  `target` конечны — **OK**.
- Имена суставов URDF совпадают с `JOINT_ORDER` (rf/lf/rh/lh x
  hip/upper_leg/lower_leg) — **OK**.
- Host ROS = `lyrical`, но Gazebo-пакеты (`gz_ros2_control`,
  `ros_gz_sim`, `gazebo_sim`, `go2_description`) в source не найдены →
  полный прогон только в контейнере/`colcon_ws`.

### Дальше

1. Запустить в Gazebo (контейнер), проверить: робот **стоит** на
   дефолтной стойке, затем **идёт**.
2. Если не выдерживает — перейти на **effort** + PD в узле (kp 25 / kd 0.5)
   или подобрать гейны/трение.
3. Добавить телеметрию Gazebo (по образцу `src/isaac/telemetry.py`).
4. Серия RL vs IK, метрики (скорость, Z/σ, roll/pitch, дрейф, CoT,
   падения), отчёт.
