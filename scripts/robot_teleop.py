#!/usr/bin/env python3
"""Teleop для Go2: скорость + переключение походки в одном окне.

Заменяет teleop_twist_keyboard, добавляя переключение режимов.

Клавиши:
    i / ,  — вперёд / назад        j / l — поворот влево / вправо
    u / o  — вперёд-влево/вправо   k     — стоп (скорость 0)
    1 — TROT    2 — CRAWL    3 — STAND    4 — REST
    q — выход
    w / x — +/- линейная скорость

Запуск (в контейнере, где есть quadropted_msgs):
    ros2 run ... ИЛИ: python3 robot_teleop.py --ros-args -r __ns:=/robot1
"""

from __future__ import annotations

import argparse
import sys
import termios
import tty

import rclpy
from rclpy.node import Node

from quadropted_msgs.msg import (  # type: ignore[import-not-found]
    RobotModeCommand,
    RobotVelocity,
)

MODES = {"1": "TROT", "2": "CRAWL", "3": "STAND", "4": "REST"}
STEP = 0.05


class Teleop(Node):
    def __init__(self, ns: str, vx0: float, wz0: float) -> None:
        super().__init__("robot_teleop")
        self.vx = vx0
        self.wz = wz0
        # Rust-контроллер слушает RobotVelocity (не Twist/cmd_vel).
        self.pub_vel = self.create_publisher(RobotVelocity, f"{ns}/robot_velocity", 10)
        self.pub_mode = self.create_publisher(RobotModeCommand, f"{ns}/robot_mode", 10)
        self.get_logger().info(
            "teleop: i/,/j/l движение; 1 TROT 2 CRAWL 3 STAND 4 REST; q выход"
        )

    def send(self, lx: float, az: float) -> None:
        msg = RobotVelocity()
        msg.robot_id = 1
        msg.cmd_vel.linear.x = float(lx)
        msg.cmd_vel.linear.y = 0.0
        msg.cmd_vel.linear.z = 0.0
        msg.cmd_vel.angular.x = 0.0
        msg.cmd_vel.angular.y = 0.0
        msg.cmd_vel.angular.z = float(az)
        self.pub_vel.publish(msg)

    def set_mode(self, mode: str) -> None:
        msg = RobotModeCommand()
        msg.mode = mode
        msg.robot_id = 1
        self.pub_mode.publish(msg)
        self.get_logger().info(f"режим: {mode}")


def getkey() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", default="/robot1")
    ap.add_argument("--vx", type=float, default=0.3)
    ap.add_argument("--wz", type=float, default=0.5)
    args = ap.parse_args()

    rclpy.init()
    node = Teleop(args.ns, args.vx, args.wz)
    print(f"скорости: vx={args.vx:.2f} wz={args.wz:.2f} (w/x меняют vx)")
    try:
        while rclpy.ok():
            k = getkey()
            if k in ("q", "\x03"):  # q или Ctrl+C
                break
            if k == "i":
                node.send(node.vx, 0.0)
            elif k == ",":
                node.send(-node.vx, 0.0)
            elif k == "j":
                node.send(0.0, node.wz)
            elif k == "l":
                node.send(0.0, -node.wz)
            elif k == "u":
                node.send(node.vx, node.wz)
            elif k == "o":
                node.send(node.vx, -node.wz)
            elif k == "k":
                node.send(0.0, 0.0)
            elif k in MODES:
                node.set_mode(MODES[k])
                node.send(0.0, 0.0)
            elif k == "w":
                node.vx += STEP
                print(f"vx={node.vx:.2f}")
            elif k == "x":
                node.vx = max(0.0, node.vx - STEP)
                print(f"vx={node.vx:.2f}")
    finally:
        node.send(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
