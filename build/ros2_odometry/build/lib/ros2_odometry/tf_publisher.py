import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped, PoseStamped
from rclpy.qos import QoSProfile
import copy


class OdomTransformBroadcaster(Node):
    def __init__(self):
        super().__init__("odom_tf_broadcaster")

        # Инициализация TransformBroadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # Создание подписки на топик /odom
        qos_profile = QoSProfile(depth=10)
        self.odom_subscription = self.create_subscription(
            Odometry, "/odom", self.odom_callback, qos_profile
        )

        # Инициализация сообщения Path и паблишера для пути
        self.path_msg = Path()
        self.path_msg.header.frame_id = "odom"
        self.path_publisher = self.create_publisher(Path, "/path", 10)

        self.get_logger().info("Odom to TF Broadcaster started")

    def odom_callback(self, msg: Odometry):
        # Создание сообщения TransformStamped
        t_odom = TransformStamped()

        # Трансформируем временную метку на время получения сообщения
        t_odom.header.stamp = msg.header.stamp

        # Трансформируем идентификаторы фреймов
        t_odom.header.frame_id = "odom"
        t_odom.child_frame_id = "base_link"

        # Трансформируем перевод
        t_odom.transform.translation.x = msg.pose.pose.position.x
        t_odom.transform.translation.y = msg.pose.pose.position.y
        t_odom.transform.translation.z = msg.pose.pose.position.z

        # Трансформируем вращение
        t_odom.transform.rotation = msg.pose.pose.orientation

        # Трансформация для base_footprint
        t_base_footprint = copy.deepcopy(t_odom)
        t_base_footprint.header.frame_id = "base_link"
        t_base_footprint.child_frame_id = "base_footprint"
        t_base_footprint.transform.translation.z = 0.0

        # Трансляция трансформаций
        # odom -> base based on ground truth plugin
        # base -> base_footprint projecting to z=0
        self.tf_broadcaster.sendTransform(t_base_footprint)
        self.tf_broadcaster.sendTransform(t_odom)

        # Создание PoseStamped для пути
        pose_stamped = PoseStamped()
        pose_stamped.header = msg.header
        pose_stamped.pose = msg.pose.pose

        # Добавление позы в сообщение Path
        self.path_msg.poses.append(pose_stamped)

        # Обновление временной метки сообщения Path
        self.path_msg.header.stamp = msg.header.stamp

        # Публикация пути
        self.path_publisher.publish(self.path_msg)


def main(args=None):
    rclpy.init(args=args)

    node = OdomTransformBroadcaster()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
