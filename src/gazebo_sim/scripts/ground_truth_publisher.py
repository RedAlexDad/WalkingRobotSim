#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import Pose, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from tf2_ros import TransformBroadcaster


class GroundTruthPublisher(Node):
    def __init__(self):
        super().__init__("ground_truth_publisher")

        declare_param = self.declare_parameter
        declare_param("publish_rate", 50)
        declare_param("base_frame_id", "base_link_gt")
        declare_param("odom_frame_id", "gt_odom")
        declare_param("pose_topic", "pose_ground_truth")
        declare_param("odom_topic", "ground_truth/odom")

        self.base_frame_id_ = self.get_parameter("base_frame_id").get_parameter_value().string_value
        self.odom_frame_id_ = self.get_parameter("odom_frame_id").get_parameter_value().string_value
        pose_topic = self.get_parameter("pose_topic").get_parameter_value().string_value
        odom_topic = self.get_parameter("odom_topic").get_parameter_value().string_value

        self.tf_broadcaster_ = TransformBroadcaster(self)
        self.odom_pub_ = self.create_publisher(Odometry, odom_topic, 10)

        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.pose_sub_ = self.create_subscription(
            Pose, pose_topic, self.pose_callback, reliable_qos
        )

        self.current_pose_ = None
        self.prev_pose_ = None
        self.prev_time_ = None
        self.current_time_ = None

        timer_period = 1.0 / float(self.get_parameter("publish_rate").get_parameter_value().integer_value)
        self.timer_ = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(
            f"Ground Truth Publisher started: "
            f"pose_topic={pose_topic}, odom_topic={odom_topic}, "
            f"rate={self.get_parameter('publish_rate').get_parameter_value().integer_value} Hz"
        )

    def pose_callback(self, msg: Pose):
        self.prev_pose_ = self.current_pose_
        self.current_pose_ = msg
        self.prev_time_ = self.current_time_
        self.current_time_ = self.get_clock().now()

    def timer_callback(self):
        if self.current_pose_ is None:
            return

        stamp = self.get_clock().now()
        odom_msg = Odometry()
        odom_msg.header.stamp = stamp.to_msg()
        odom_msg.header.frame_id = self.odom_frame_id_
        odom_msg.child_frame_id = self.base_frame_id_

        odom_msg.pose.pose = self.current_pose_

        diag_cov = 1e-3
        odom_msg.pose.covariance = [0.0] * 36
        odom_msg.pose.covariance[0] = diag_cov
        odom_msg.pose.covariance[7] = diag_cov
        odom_msg.pose.covariance[14] = diag_cov
        odom_msg.pose.covariance[21] = diag_cov
        odom_msg.pose.covariance[28] = diag_cov
        odom_msg.pose.covariance[35] = diag_cov

        if self.prev_pose_ is not None and self.prev_time_ is not None and self.current_time_ is not None:
            dt = (self.current_time_ - self.prev_time_).nanoseconds / 1e9
            if dt > 0:
                vx = (self.current_pose_.position.x - self.prev_pose_.position.x) / dt
                vy = (self.current_pose_.position.y - self.prev_pose_.position.y) / dt
                vz = (self.current_pose_.position.z - self.prev_pose_.position.z) / dt

                dq = self.quaternion_diff(
                    self.prev_pose_.orientation, self.current_pose_.orientation
                )
                angular_z = dq / dt if abs(dq) < math.pi else 0.0

                odom_msg.twist.twist.linear.x = vx
                odom_msg.twist.twist.linear.y = vy
                odom_msg.twist.twist.linear.z = vz
                odom_msg.twist.twist.angular.z = angular_z

        self.odom_pub_.publish(odom_msg)

        tf_msg = TransformStamped()
        tf_msg.header.stamp = stamp.to_msg()
        tf_msg.header.frame_id = self.odom_frame_id_
        tf_msg.child_frame_id = self.base_frame_id_
        tf_msg.transform.translation.x = self.current_pose_.position.x
        tf_msg.transform.translation.y = self.current_pose_.position.y
        tf_msg.transform.translation.z = self.current_pose_.position.z
        tf_msg.transform.rotation = self.current_pose_.orientation
        self.tf_broadcaster_.sendTransform(tf_msg)

    @staticmethod
    def quaternion_yaw(q):
        return math.atan2(
            2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )

    @staticmethod
    def quaternion_diff(q1, q2):
        yaw1 = GroundTruthPublisher.quaternion_yaw(q1)
        yaw2 = GroundTruthPublisher.quaternion_yaw(q2)
        d = yaw2 - yaw1
        return math.atan2(math.sin(d), math.cos(d))


def main(args=None):
    rclpy.init(args=args)
    node = GroundTruthPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
