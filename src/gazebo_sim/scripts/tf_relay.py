#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from tf2_msgs.msg import TFMessage

QOS_TF = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=100,
)

QOS_TF_STATIC = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=100,
)


class TFRelay(Node):
    def __init__(self):
        super().__init__("tf_relay")
        self._msg_count = 0
        self.sub = self.create_subscription(TFMessage, "/robot1/tf", self.cb_tf, QOS_TF)
        self.sub_static = self.create_subscription(TFMessage, "/robot1/tf_static", self.cb_tf_static, QOS_TF_STATIC)
        self.pub = self.create_publisher(TFMessage, "/tf", QOS_TF)
        self.pub_static = self.create_publisher(TFMessage, "/tf_static", QOS_TF_STATIC)
        self.get_logger().info("TF relay started: /robot1/tf -> /tf, /robot1/tf_static -> /tf_static")

    def cb_tf(self, msg):
        self._msg_count += 1
        if self._msg_count == 1:
            self.get_logger().info(f"First TF message received: {len(msg.transforms)} transforms")
        self.pub.publish(msg)

    def cb_tf_static(self, msg):
        self.pub_static.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TFRelay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
