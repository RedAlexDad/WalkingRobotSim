#!/usr/bin/env python3
"""go2_policy_gz.py — запуск обученной RL-политики Go2 (physx_policy.pt) в
Gazebo (gz-sim) через существующий позиционный интерфейс
`joint_group_controller`.

Идея: политика обучена (48 наблюдений -> 12 действий, TorchScript, CPU).
В Gazebo уже есть позиционный контроллер суставов (тот же топик, что у
Rust IK/TROT-контроллера). Узел собирает наблюдения, прогоняет политику и
публикует целевые углы `target = q_def + action_scale * action`.

Запуск (полный, в ROS 2 + Gazebo):
    python3 src/gazebo_sim/scripts/go2_policy_gz.py \
        --ros-args -p namespace:=robot1 -p vx:=0.3 -p use_sim_time:=true

Оффлайн-проверка (без ROS/Gazebo) — загрузка политики и сборка obs:
    .venv-mujoco/bin/python src/gazebo_sim/scripts/go2_policy_gz.py --selftest

Требуется torch (в системном python его нет; есть в .venv-mujoco).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
POLICY_PATH = (
    REPO
    / "src"
    / "isaac"
    / "assets"
    / "Isaac"
    / "Samples"
    / "Policies"
    / "go2"
    / "physx_policy.pt"
)

# Порядок суставов контроллера Gazebo: rf, lf, rh, lh x (hip, upper_leg, lower_leg).
# Это же соответствует порядку политики FR, FL, RR, RL (rh=RR, lh=RL).
JOINT_ORDER = [
    "rf_hip_joint", "rf_upper_leg_joint", "rf_lower_leg_joint",
    "lf_hip_joint", "lf_upper_leg_joint", "lf_lower_leg_joint",
    "rh_hip_joint", "rh_upper_leg_joint", "rh_lower_leg_joint",
    "lh_hip_joint", "lh_upper_leg_joint", "lh_lower_leg_joint",
]

# Порядок ПОЛИТИКИ (IsaacLab/NVIDIA Go2): FL, FR, RL, RR x (hip, thigh, calf).
# default_joint_pos в порядке политики:
#   FL 0.1/0.8/-1.5, FR -0.1/0.8/-1.5, RL 0.1/1.0/-1.5, RR -0.1/1.0/-1.5.
DEFAULT_POS = np.array(
    [
        0.1, 0.8, -1.5,   # FL
        -0.1, 0.8, -1.5,  # FR
        0.1, 1.0, -1.5,   # RL
        -0.1, 1.0, -1.5,  # RR
    ],
    dtype=np.float32,
)

# JOINT_ORDER (контроллер Gazebo) = rf(FR), lf(FL), rh(RR), lh(RL).
# PERM[i] — индекс сустава в порядке политики для i-го сустава контроллера.
# (Перестановка симметрична: одинаково переводит контроллер<->политику.)
PERM = np.array([3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8], dtype=np.intp)

ACTION_SCALE = 0.25
RL_HZ = 50.0          # частота политики (dt * decimation)
CTRL_HZ = 200.0       # частота control-loop (как в rl_sar: dt=0.005, dec=4)
POLICY_DECIMATION = int(CTRL_HZ / RL_HZ)
NUM_JOINTS = 12
OBS_DIM = 48


def quat_to_mat(q: np.ndarray) -> np.ndarray:
    """Кватернион (w, x, y, z) -> матрица поворота 3x3."""
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float32,
    )


def build_obs(
    quat_wxyz: np.ndarray,
    lin_vel_body: np.ndarray,
    ang_vel_body: np.ndarray,
    cmd: np.ndarray,
    q: np.ndarray,
    dq: np.ndarray,
    last_action: np.ndarray,
) -> np.ndarray:
    """Собрать 48-мерное наблюдение политики (как в go2_policy_mj.py)."""
    r = quat_to_mat(quat_wxyz)
    gravity_body = r.T @ np.array([0.0, 0.0, -1.0], dtype=np.float32)
    obs = np.concatenate(
        [
            lin_vel_body.astype(np.float32),      # 3
            ang_vel_body.astype(np.float32),      # 3
            gravity_body.astype(np.float32),      # 3
            cmd.astype(np.float32),               # 3
            (q - DEFAULT_POS).astype(np.float32),  # 12
            dq.astype(np.float32),                # 12
            last_action.astype(np.float32),       # 12
        ]
    )
    assert obs.shape == (OBS_DIM,), obs.shape
    return obs.astype(np.float32)


def load_policy():
    import torch  # локально, чтобы --selftest не тянул rclpy

    policy = torch.jit.load(str(POLICY_PATH), map_location="cpu").eval()
    return policy


def _run_policy(policy, obs: np.ndarray) -> np.ndarray:
    import torch

    with torch.inference_mode():
        action = policy(torch.from_numpy(obs[None]))[0].numpy().copy()
    return action.astype(np.float32)


def selftest() -> int:
    """Оффлайн-проверка: политика грузится и даёт 12 действий."""
    print(f"policy: {POLICY_PATH} (exists={POLICY_PATH.exists()})")
    policy = load_policy()
    obs = build_obs(
        quat_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        lin_vel_body=np.zeros(3, dtype=np.float32),
        ang_vel_body=np.zeros(3, dtype=np.float32),
        cmd=np.array([0.3, 0.0, 0.0], dtype=np.float32),
        q=DEFAULT_POS.copy(),
        dq=np.zeros(NUM_JOINTS, dtype=np.float32),
        last_action=np.zeros(NUM_JOINTS, dtype=np.float32),
    )
    action = _run_policy(policy, obs)
    target = DEFAULT_POS + ACTION_SCALE * action
    print(f"obs.shape={obs.shape} action.shape={action.shape}")
    print(f"action  min={action.min():+.3f} max={action.max():+.3f}")
    print(f"target  min={target.min():+.3f} max={target.max():+.3f}")
    assert action.shape == (NUM_JOINTS,)
    assert np.all(np.isfinite(action))
    print("SELFTEST OK")
    return 0


def run_ros() -> int:
    """Полный режим: ROS 2 узел, публикующий целевые углы в контроллер."""
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy
    from sensor_msgs.msg import Imu, JointState
    from std_msgs.msg import Float64MultiArray
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry

    class PolicyNode(Node):
        def __init__(self) -> None:
            super().__init__("go2_policy_gz")
            self.declare_parameter("namespace", "robot1")
            self.declare_parameter("vx", 0.3)
            self.declare_parameter("vy", 0.0)
            self.declare_parameter("wz", 0.0)
            self.declare_parameter("odom_topic", "")
            self.declare_parameter("joint_order", JOINT_ORDER)
            self.declare_parameter("imu_invert", False)
            self.declare_parameter("control_mode", "position")  # position | effort
            self.declare_parameter("kp", 25.0)
            self.declare_parameter("kd", 0.5)
            self.declare_parameter("effort_limit", 23.5)
            self.declare_parameter("vel_limit", 30.0)
            self.declare_parameter("hip_sign", 1.0)

            ns = self.get_parameter("namespace").value
            self.mode = str(self.get_parameter("control_mode").value)
            self.kp = float(self.get_parameter("kp").value)
            self.kd = float(self.get_parameter("kd").value)
            self.effort_limit = float(self.get_parameter("effort_limit").value)
            self.vel_limit = float(self.get_parameter("vel_limit").value)
            self.policy = load_policy()
            self.last_action = np.zeros(NUM_JOINTS, dtype=np.float32)
            self.joint_names = list(self.get_parameter("joint_order").value)

            self.q = None
            self.dq = None
            self.quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
            self.ang_vel = np.zeros(3, dtype=np.float32)
            self.lin_vel = np.zeros(3, dtype=np.float32)
            self.cmd = np.array(
                [
                    float(self.get_parameter("vx").value),
                    float(self.get_parameter("vy").value),
                    float(self.get_parameter("wz").value),
                ],
                dtype=np.float32,
            )
            self.received = False

            odom_topic = self.get_parameter("odom_topic").value or f"/{ns}/odom_gz"
            self.create_subscription(JointState, f"/{ns}/joint_states", self._on_joints, 10)
            self.create_subscription(Imu, f"/{ns}/imu_plugin/out", self._on_imu, 10)
            self.create_subscription(Odometry, odom_topic, self._on_odom, 10)
            self.create_subscription(Twist, "/cmd_vel", self._on_cmd, 10)

            self.pub = self.create_publisher(
                Float64MultiArray,
                (f"/{ns}/joint_group_effort_controller/commands"
                 if self.mode == "effort"
                 else f"/{ns}/joint_group_controller/commands"),
                10,
            )
            self.tick = 0
            self.target_p = DEFAULT_POS.copy()
            # Публикуем дефолтную стойку (в порядке контроллера) до прихода данных.
            self._publish_target(DEFAULT_POS[PERM])
            self.create_timer(1.0 / CTRL_HZ, self._control)
            self.get_logger().info(
                f"go2_policy_gz запущен (ns={ns}, mode={self.mode}, "
                f"vx={self.cmd[0]:.2f}, ctrl={CTRL_HZ:.0f} Hz, rl={RL_HZ:.0f} Hz)"
            )

        def _on_joints(self, msg: JointState) -> None:
            pos = {n: p for n, p in zip(msg.name, msg.position)}
            vel = {n: v for n, v in zip(msg.name, msg.velocity)}
            if not all(n in pos for n in self.joint_names):
                return
            self.q = np.array([pos[n] for n in self.joint_names], dtype=np.float32)
            self.dq = np.array([vel.get(n, 0.0) for n in self.joint_names], dtype=np.float32)

        def _on_imu(self, msg: Imu) -> None:
            o = msg.orientation
            q = np.array([o.w, o.x, o.y, o.z], dtype=np.float32)
            if bool(self.get_parameter("imu_invert").value):
                q = np.array([q[0], -q[1], -q[2], -q[3]], dtype=np.float32)
            self.quat = q
            a = msg.angular_velocity
            self.ang_vel = np.array([a.x, a.y, a.z], dtype=np.float32)

        def _on_odom(self, msg: Odometry) -> None:
            t = msg.twist.twist
            self.lin_vel = np.array([t.linear.x, t.linear.y, t.linear.z], dtype=np.float32)

        def _on_cmd(self, msg: Twist) -> None:
            self.cmd = np.array(
                [msg.linear.x, msg.linear.y, msg.angular.z], dtype=np.float32
            )

        def _publish_target(self, target: np.ndarray) -> None:
            out = Float64MultiArray()
            out.data = [float(x) for x in target]
            self.pub.publish(out)

        def _control(self) -> None:
            if self.q is None:
                return
            dq = self.dq if self.dq is not None else np.zeros(NUM_JOINTS, dtype=np.float32)
            # В порядок политики (FL, FR, RL, RR).
            q_p = self.q[PERM]
            dq_p = dq[PERM]
            self.tick += 1
            # Политика обновляется раз в POLICY_DECIMATION такт (50 Гц),
            # PD применяется каждый такт (200 Гц) — как в rl_sar.
            if self.tick % POLICY_DECIMATION == 0:
                obs = build_obs(
                    self.quat, self.lin_vel, self.ang_vel, self.cmd, q_p, dq_p,
                    self.last_action,
                )
                try:
                    action = _run_policy(self.policy, obs)
                except Exception as exc:  # noqa: BLE001
                    self.get_logger().error(f"policy error: {exc}")
                    return
                self.last_action = action
                self.target_p = DEFAULT_POS + ACTION_SCALE * action
            target_p = self.target_p
            if self.mode == "effort":
                tau_p = self.kp * (target_p - q_p) - self.kd * dq_p
                upper = np.clip(
                    self.effort_limit * (1 - dq_p / self.vel_limit), 0, self.effort_limit
                )
                lower = np.clip(
                    self.effort_limit * (-1 - dq_p / self.vel_limit), -self.effort_limit, 0
                )
                out_p = np.clip(tau_p, lower, upper).astype(np.float32)
            else:
                out_p = target_p.astype(np.float32)
            # Обратно в порядок контроллера Gazebo и публикация.
            if float(self.get_parameter("hip_sign").value) != 1.0:
                out_p = out_p.copy()
                out_p[[0, 3, 6, 9]] *= float(self.get_parameter("hip_sign").value)
            self._publish_target(out_p[PERM])
            self.received = True

    rclpy.init()
    node = PolicyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Go2 RL policy in Gazebo (gz-sim)")
    ap.add_argument("--selftest", action="store_true", help="оффлайн-проверка политики")
    ap.add_argument("--duration", type=float, default=0.0, help="(резерв) длительность")
    args, _ = ap.parse_known_args()
    if args.selftest:
        return selftest()
    return run_ros()


if __name__ == "__main__":
    raise SystemExit(main())
