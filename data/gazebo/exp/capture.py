import sys
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

OUT = sys.argv[2] if len(sys.argv) > 2 else "/root/ws/data/exp/frames"
MAXN = int(sys.argv[1]) if len(sys.argv) > 1 else 10

class Cap(Node):
    def __init__(self):
        super().__init__("cap")
        self.bridge = CvBridge()
        self.n = 0
        self.create_subscription(Image, "/camera/image", self.cb, 10)
    def cb(self, msg):
        if self.n >= MAXN:
            return
        img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        cv2.imwrite(f"{OUT}/frame_{self.n:03d}.png", img)
        self.n += 1
        if self.n % 5 == 0:
            print("saved", self.n, flush=True)
        if self.n >= MAXN:
            rclpy.shutdown()

def main():
    rclpy.init()
    node = Cap()
    try:
        rclpy.spin(node)
    except Exception:
        pass
    print("total", node.n)

if __name__ == "__main__":
    main()
