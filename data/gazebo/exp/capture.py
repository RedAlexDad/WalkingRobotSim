"""Сохранение одного кадра с камеры Gazebo: лучший из N по дисперсии.

Gazebo иногда отдаёт пустой или недорисованный кадр, поэтому снимается
несколько подряд, а на диск попадает только лучший.
"""
import os
import sys

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

OUT = sys.argv[2] if len(sys.argv) > 2 else "/root/ws/data/exp/frames"
MAXN = int(sys.argv[1]) if len(sys.argv) > 1 else 3


class Cap(Node):
    def __init__(self):
        super().__init__("cap")
        self.bridge = CvBridge()
        self.frames = []
        self.create_subscription(Image, "/camera/image", self.cb, 10)

    def cb(self, msg):
        if len(self.frames) >= MAXN:
            return
        img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        self.frames.append((float(img.std()), img))
        if len(self.frames) >= MAXN:
            rclpy.shutdown()


def main():
    rclpy.init()
    node = Cap()
    try:
        rclpy.spin(node)
    except Exception:
        pass
    if not node.frames:
        print("saved 0")
        return
    std, img = max(node.frames, key=lambda x: x[0])
    os.makedirs(OUT, exist_ok=True)
    cv2.imwrite(os.path.join(OUT, "frame.png"), img)
    print(f"saved 1 std={std:.1f}")


if __name__ == "__main__":
    main()
