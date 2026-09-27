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
import threading
import time
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float64MultiArray

import mujoco  # type: ignore[import-untyped]

REPO = Path(__file__).resolve().parents[2]
SCENE = REPO / "external" / "mujoco_menagerie" / "unitree_go2" / "scene.xml"

# Порядок суставов MuJoCo = FL, FR, RL, RR; контроллер/Isaac = FR, FL, RR, RL.
CMD_TO_MJ = np.array([3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8])

KP, KD, LIMIT, VMAX = 25.0, 0.5, 23.5, 30.0
# Стойка (в порядке MuJoCo FL, FR, RL, RR): hip ∓0.1, thigh 0.8/1.0, calf −1.5.
DEFAULT_MJ = np.array(
    [0.1, 0.8, -1.5, -0.1, 0.8, -1.5, 0.1, 1.0, -1.5, -0.1, 1.0, -1.5],
    dtype=np.float32,
)


class Bridge(Node):
    def __init__(self, ns: str = "/robot1") -> None:
        super().__init__("mujoco_bridge")
        self.imu_pub = self.create_publisher(Imu, f"{ns}/imu", 10)
        self.time_pub = self.create_publisher(Float64MultiArray, f"{ns}/sim_time", 10)
        self.target = DEFAULT_MJ.copy()
        self.lock = threading.Lock()
        self.create_subscription(
            Float64MultiArray,
            f"{ns}/joint_group_controller/commands",
            self._on_cmd,
            10,
        )

    def _on_cmd(self, msg: Float64MultiArray) -> None:
        if len(msg.data) != 12:
            return
        cmd = np.asarray(msg.data, dtype=np.float32)
        tgt = np.zeros(12, dtype=np.float32)
        tgt[CMD_TO_MJ] = cmd
        with self.lock:
            self.target = tgt

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
    spin = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
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
    n = int(args.duration / model.opt.timestep)
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
        if viewer is not None:
            viewer.sync()
        time.sleep(0.0)

    print(
        f"после {args.duration:.1f}с: base x={data.qpos[0]:+.3f} y={data.qpos[1]:+.3f} z={data.qpos[2]:.3f}"
    )
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
