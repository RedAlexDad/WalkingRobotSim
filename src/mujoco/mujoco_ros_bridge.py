"""ROS 2-мост: MuJoCo (Go2) <-> Rust-контроллер (robot_controller_node).

Контроллер Feedforward: ему нужны только imu и sim_time; он публикует
целевые углы суставов. Мост читает их, считает момент PD и подаёт в MuJoCo.

Топики (ns=/robot1):
    -> imu                        (sensor_msgs/Imu)              мост публикует
    -> sim_time                   (std_msgs/Float64MultiArray)   мост публикует
    <- joint_group_controller/commands (std_msgs/Float64MultiArray) мост слушает

Запуск (host ROS 2 lyrical):
    source /opt/ros/lyrical/setup.bash
    .venv-mujoco/bin/python src/mujoco/mujoco_ros_bridge.py --duration 30 --vx 0.5 --viewer
"""

from __future__ import annotations

import argparse
import contextlib
import math
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np
import rclpy
from mujoco_params import CMD_TO_MJ, DEFAULT_MJ, KD, KP, LIMIT, VMAX, _rpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float64MultiArray

# quadropted_msgs собраны только в контейнере (Jazzy); в host-ROS lyrical их
# нет. Импортируем опционально: при отсутствии телеметрия теряет cmd/mode,
# но движение (joint commands) работает.
try:
    from quadropted_msgs.msg import (  # type: ignore[import-not-found]
        RobotModeCommand,
        RobotVelocity,
    )

    _HAS_QUADROPTED = True
except ImportError:
    RobotModeCommand = Any
    RobotVelocity = Any
    _HAS_QUADROPTED = False

import mujoco  # type: ignore[import-untyped]

REPO = Path(__file__).resolve().parents[2]
SCENE = REPO / "external" / "mujoco_menagerie" / "unitree_go2" / "scene.xml"


def _write_row(
    csv: Any,
    model: Any,
    data: Any,
    node: Any,
    tau: np.ndarray,
    target: np.ndarray,
) -> None:
    """Записать полную строку телеметрии (как в Isaac: суставы, момент, стопы)."""

    r, p, y = _rpy(data.qpos[3:7])
    base = data.qpos[:3]
    quat = data.qpos[3:7]
    lin = data.qvel[:3]
    ang = data.qvel[3:6]
    q = data.qpos[7:19]
    dq = data.qvel[6:18]
    # Позиции стоп как proxy — тела *_calf (в Menagerie нет тел foot).
    foot_z, foot_x = [], []
    for i in range(1, model.nbody):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i) or ""
        if name.endswith("_calf"):
            pos = data.xpos[i]
            foot_z.append(float(pos[2]))
            foot_x.append(float(pos[0]))
    vals = (
        [f"{data.time:.3f}", node.mode]
        + [f"{v:.3f}" for v in node.cmd]
        + [f"{v:.4f}" for v in base]
        + [f"{v:.5f}" for v in quat]
        + [f"{r:.4f}", f"{p:.4f}", f"{y:.4f}"]
        + [f"{v:.4f}" for v in lin]
        + [f"{v:.4f}" for v in ang]
        + [f"{v:.5f}" for v in q]
        + [f"{v:.5f}" for v in dq]
        + [f"{v:.5f}" for v in target]
        + [f"{v:.4f}" for v in tau]
        + [f"{v:.4f}" for v in (foot_z + [0.0] * 4)[:4]]
        + [f"{v:.4f}" for v in (foot_x + [0.0] * 4)[:4]]
    )
    csv.write(",".join(vals) + "\n")


class Bridge(Node):
    def __init__(self, ns: str = "/robot1") -> None:
        super().__init__("mujoco_bridge")
        self.imu_pub = self.create_publisher(Imu, f"{ns}/imu", 10)
        self.time_pub = self.create_publisher(Float64MultiArray, f"{ns}/sim_time", 10)
        self.target = DEFAULT_MJ.copy()
        self.cmd = np.zeros(3, dtype=np.float32)  # [vx, vy, wz]
        self.mode = "STAND"
        self.cmd_count = 0
        self.lock = threading.Lock()
        # QoS BEST_EFFORT: Rust-публикатор (rclrs) может быть BEST_EFFORT,
        # а RELIABLE-подписка с ним несовместима (данные не идут).
        from rclpy.qos import (
            QoSDurabilityPolicy,
            QoSHistoryPolicy,
            QoSProfile,
            ReliabilityPolicy,
        )

        qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
        )
        self.create_subscription(
            Float64MultiArray,
            f"{ns}/joint_group_controller/commands",
            self._on_cmd,
            qos,
        )
        if _HAS_QUADROPTED:
            self.create_subscription(
                RobotVelocity, f"{ns}/robot_velocity", self._on_vel, qos
            )
            self.create_subscription(
                RobotModeCommand, f"{ns}/robot_mode", self._on_mode, qos
            )

    def _on_vel(self, msg: RobotVelocity) -> None:
        with self.lock:
            self.cmd[:] = [
                msg.cmd_vel.linear.x,
                msg.cmd_vel.linear.y,
                msg.cmd_vel.angular.z,
            ]

    def _on_mode(self, msg: RobotModeCommand) -> None:
        with self.lock:
            self.mode = msg.mode

    def _on_cmd(self, msg: Float64MultiArray) -> None:
        if len(msg.data) != 12:
            return
        cmd = np.asarray(msg.data, dtype=np.float32)
        tgt = np.zeros(12, dtype=np.float32)
        tgt[CMD_TO_MJ] = cmd
        with self.lock:
            self.target = tgt
            self.cmd_count += 1

    def publish_state(
        self, quat: np.ndarray, gyro: np.ndarray, sim_time: float
    ) -> None:
        imu = Imu()
        imu.header.frame_id = "base"
        imu.orientation.w = float(quat[0])
        imu.orientation.x = float(quat[1])
        imu.orientation.y = float(quat[2])
        imu.orientation.z = float(quat[3])
        imu.angular_velocity.x = float(gyro[0])
        imu.angular_velocity.y = float(gyro[1])
        imu.angular_velocity.z = float(gyro[2])
        self.imu_pub.publish(imu)
        t = Float64MultiArray()
        t.data = [float(sim_time)]
        self.time_pub.publish(t)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=30.0)
    ap.add_argument(
        "--vx", type=float, default=0.0, help="команда скорости (для логов)"
    )
    ap.add_argument("--viewer", action="store_true")
    args = ap.parse_args()

    rclpy.init()
    node = Bridge()

    def _spin() -> None:
        # Ctrl+C завершает spin() исключением — глушим штатно.
        with contextlib.suppress(Exception):
            rclpy.spin(node)

    spin = threading.Thread(target=_spin, daemon=True)
    spin.start()

    model = mujoco.MjModel.from_xml_path(str(SCENE))
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)
    data.qpos[2] = 0.30
    data.qpos[3:7] = [1, 0, 0, 0]
    data.qpos[7:19] = DEFAULT_MJ
    mujoco.mj_forward(model, data)

    viewer = None
    if args.viewer:
        import mujoco.viewer as mjviewer  # type: ignore[import-untyped]

        viewer = mjviewer.launch_passive(model, data)

    print(f"мост запущен: {model.opt.timestep} c, vx={args.vx} (управляет Rust-нода)")
    log_dir = REPO / "logs" / "mujoco"
    log_dir.mkdir(parents=True, exist_ok=True)
    csv_path = log_dir / f"telemetry_{time.strftime('%Y%m%d-%H%M%S')}.csv"
    csv = csv_path.open("w")
    _cols = (
        ["t", "mode", "cmd_vx", "cmd_vy", "cmd_wz"]
        + [f"base_p{i}" for i in "xyz"]
        + [f"quat_{i}" for i in ("w", "x", "y", "z")]
        + [f"rpy_{i}" for i in ("r", "p", "y")]
        + [f"base_v{i}" for i in ("x", "y", "z")]
        + [f"base_w{i}" for i in ("x", "y", "z")]
        + [f"q{i}" for i in range(12)]
        + [f"dq{i}" for i in range(12)]
        + [f"tgt{i}" for i in range(12)]
        + [f"tau{i}" for i in range(12)]
        + [f"foot_z{i}" for i in range(4)]
        + [f"foot_x{i}" for i in range(4)]
    )
    csv.write(",".join(_cols) + "\n")
    n = int(args.duration / model.opt.timestep)
    try:
        for step in range(n):
            q = data.qpos[7:19]
            dq = data.qvel[6:18]
            with node.lock:
                target = node.target.copy()
            tau = KP * (target - q) - KD * dq
            upper = np.clip(LIMIT * (1 - dq / VMAX), 0, LIMIT)
            lower = np.clip(LIMIT * (-1 - dq / VMAX), -LIMIT, 0)
            data.ctrl[:] = np.clip(tau, lower, upper)
            mujoco.mj_step(model, data)
            if step % 10 == 0:
                node.publish_state(data.qpos[3:7], data.qvel[3:6], float(data.time))
            if step % 25 == 0:
                _write_row(csv, model, data, node, tau, target)
            if viewer is not None:
                if not viewer.is_running():
                    break
                viewer.sync()
            time.sleep(0.0)
    except KeyboardInterrupt:
        print("\nпрервано пользователем")
    finally:
        csv.close()
        dist = math.hypot(float(data.qpos[0]), float(data.qpos[1]))
        print(
            f"пройдено={dist:.3f} м, команд получено={node.cmd_count}, телеметрия: {csv_path}"
        )
        if viewer is not None:
            viewer.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
