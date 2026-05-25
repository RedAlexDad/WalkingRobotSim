import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
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
        super().__init__('tf_relay')
        self.sub = self.create_subscription(
            TFMessage, '/robot1/tf', self.cb_tf, QOS_TF)
        self.sub_static = self.create_subscription(
            TFMessage, '/robot1/tf_static', self.cb_tf_static, QOS_TF_STATIC)
        self.pub = self.create_publisher(TFMessage, '/tf', QOS_TF)
        self.pub_static = self.create_publisher(TFMessage, '/tf_static', QOS_TF_STATIC)

    def cb_tf(self, msg):
        self.pub.publish(msg)

    def cb_tf_static(self, msg):
        self.pub_static.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TFRelay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
