#!/usr/bin/env python3
"""Подписчик команд суставов с настраиваемым ограничением hip.

Замена ``go2_isaac_ros2.ros.Go2SubNode``: тот жёстко клампит hip к ±0.3,
что обрезает IMU-компенсацию крена (контроллер хочет до ±0.5) и не даёт
выпрямить корпус. Здесь предел задаётся через ``GO2_HIP_CLAMP``.

Топик: /robot1/joint_group_controller/commands (std_msgs/Float64MultiArray,
12 углов, порядок FR,FL,RR,RL × hip,thigh,calf).
"""

from __future__ import annotations

import os
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import torch

JOINT_CMD_TOPIC = "/robot1/joint_group_controller/commands"
HIP_IDX = [0, 3, 6, 9]


class Go2CmdSubNode(Node):
    def __init__(self, env):
        super().__init__("go2_cmd_sub_node")
        self.env = env
        self.hip_clamp = float(os.environ.get("GO2_HIP_CLAMP", "0.3"))
        self.count = 0
        self.cmd_sub = self.create_subscription(
            Float64MultiArray, JOINT_CMD_TOPIC, self.cmd_cb, 1
        )
        self.thread = threading.Thread(target=self._spin, daemon=True)
        print(f"[go2_cmd_sub] hip clamp = ±{self.hip_clamp}", flush=True)

    def _spin(self):
        from rclpy.executors import SingleThreadedExecutor
        executor = SingleThreadedExecutor()
        executor.add_node(self)
        try:
            while rclpy.ok():
                executor.spin_once(timeout_sec=0.01)
        except Exception as e:
            print(f"[go2_cmd_sub] spin error: {e}", flush=True)
        finally:
            executor.shutdown()

    def cmd_cb(self, msg: Float64MultiArray):
        action = torch.zeros(12)
        stiffness = torch.zeros(12)
        damping = torch.zeros(12)
        for i in range(12):
            action[i] = msg.data[i]
            stiffness[i] = 75.0
            damping[i] = 0.5
        action[HIP_IDX] = action[HIP_IDX].clamp(-self.hip_clamp, self.hip_clamp)
        self.env.set_action(action)
        self.env.set_stiffness(stiffness)
        self.env.set_damping(damping)
        self.count += 1

    def start(self):
        self.thread.start()
