#!/usr/bin/env python3
"""
Узел одометрии четвероногого робота (декомпозированная версия).
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion, TransformStamped
from std_msgs.msg import Int64
from rosgraph_msgs.msg import Clock
from builtin_interfaces.msg import Time
import tf_transformations
import tf2_ros
import math
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from quadropted_msgs.msg import RobotVelocity, RobotFootContact
from ForwardKinematics import ForwardKinematics
from std_msgs.msg import Float64MultiArray
from visualization_msgs.msg import Marker, MarkerArray
from collections import deque

from QuadrupedOdometry import OdometryState, update_odometry


class DogOdometry(Node):
    def __init__(self):
        super().__init__('dog_odometry')

        # Параметры узла
        self.declare_parameter('verbose', False)
        self.verbose = self.get_parameter('verbose').get_parameter_value().bool_value
        if self.verbose:
            self.get_logger().info(f"Verbose mode: {self.verbose}")

        self.declare_parameter('publish_rate', 50)
        publish_rate = self.get_parameter('publish_rate').get_parameter_value().integer_value
        if self.verbose:
            self.get_logger().info(f"Publish rate: {publish_rate} Hz")

        self.declare_parameter('has_imu_heading', True)
        self.has_imu_heading = self.get_parameter('has_imu_heading').get_parameter_value().bool_value
        if self.verbose:
            self.get_logger().info(f"Has IMU heading: {self.has_imu_heading}")

        self.declare_parameter('enable_odom_tf', True)
        self.enable_odom_tf = self.get_parameter('enable_odom_tf').get_parameter_value().bool_value
        if self.verbose:
            self.get_logger().info(f"Enable odom TF: {self.enable_odom_tf}")

        self.declare_parameter('base_frame_id', 'base')
        self.base_frame_id = self.get_parameter('base_frame_id').get_parameter_value().string_value
        if self.verbose:
            self.get_logger().info(f"Base frame ID: {self.base_frame_id}")

        self.declare_parameter('odom_frame_id', 'odom')
        self.odom_frame_id = self.get_parameter('odom_frame_id').get_parameter_value().string_value
        if self.verbose:
            self.get_logger().info(f"Odom frame ID: {self.odom_frame_id}")

        self.declare_parameter('is_gazebo', True)
        self.is_gazebo = self.get_parameter('is_gazebo').get_parameter_value().bool_value
        if self.verbose:
            self.get_logger().info(f"Is Gazebo: {self.is_gazebo}")

        self.declare_parameter('clock_topic', '/clock')
        clock_topic = self.get_parameter('clock_topic').get_parameter_value().string_value
        if self.verbose:
            self.get_logger().info(f"Clock Topic: {clock_topic}")

        # Состояние одометрии (декомпозированное)
        self.odom_state = OdometryState(filter_window_size=14)

        self.last_position_time = self.get_clock().now()

        # Коэффициент для коррекции скорости
        self.VELOCITY_COEFFICIENT = 11.66

        # Размеры тела и ног
        body_dimensions = [0.3762, 0.0935]
        leg_dimensions = [0.0, 0.0955, 0.213, 0.213]

        # Инициализация Forward Kinematics
        self.fk_solver = ForwardKinematics(body_dimensions, leg_dimensions)

        # QoS профили
        qos_reliable = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            depth=10,
            history=HistoryPolicy.KEEP_LAST
        )
        qos_best_effort = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10,
            history=HistoryPolicy.KEEP_LAST
        )

        # Паблишер одометрии
        self.odom_pub = self.create_publisher(Odometry, 'odom', qos_reliable)

        # Подписки
        if self.has_imu_heading:
            self.imu_sub = self.create_subscription(
                Imu,
                'imu_plugin/out',
                self.imu_callback,
                qos_reliable
            )

        self.velocity_sub = self.create_subscription(
            RobotVelocity,
            'robot_velocity',
            self.velocity_callback,
            qos_reliable
        )

        self.joint_states_sub = self.create_subscription(
            Float64MultiArray,
            'joint_group_controller/commands',
            self.joint_states_callback,
            qos_reliable
        )

        self.foot_contacts_sub = self.create_subscription(
            RobotFootContact,
            'foot_contact',
            self.foot_contacts_callback,
            qos_best_effort
        )

        # Трансформ-бродкастер
        if self.enable_odom_tf:
            self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # Подписка на clock или encoder_value
        if self.is_gazebo:
            clock_qos = QoSProfile(
                reliability=ReliabilityPolicy.RELIABLE,
                durability=DurabilityPolicy.VOLATILE,
                depth=10,
                history=HistoryPolicy.KEEP_LAST
            )
            self.clock_sub = self.create_subscription(
                Clock,
                clock_topic,
                self.clock_callback,
                clock_qos
            )
            if self.verbose:
                self.get_logger().info("Subscribed to /clock topic with RELIABLE QoS.")
        else:
            encoder_qos = QoSProfile(
                reliability=ReliabilityPolicy.BEST_EFFORT,
                durability=DurabilityPolicy.VOLATILE,
                depth=10,
                history=HistoryPolicy.KEEP_LAST
            )
            self.encoder_sub = self.create_subscription(
                Int64,
                'encoder_value',
                self.encoder_callback,
                encoder_qos
            )
            if self.verbose:
                self.get_logger().info("Subscribed to encoder_value topic with BEST_EFFORT QoS.")

        # Паблишер маркеров
        self.marker_pub = self.create_publisher(MarkerArray, 'foot_markers', qos_reliable)

        # Таймер
        timer_period = 1.0 / publish_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info("Dog Odometry Node has been started.")

        self.MAX_LINEAR_VELOCITY_X = 0.035
        self.MAX_LINEAR_VELOCITY_Y = 0.012
        self.MAX_ANGULAR_VELOCITY = 1.0

    # ================================================================
    # Callbacks
    # ================================================================

    def velocity_callback(self, msg):
        self.odom_state.linear_velocity_x = msg.cmd_vel.linear.x
        self.odom_state.linear_velocity_y = msg.cmd_vel.linear.y
        if self.verbose:
            self.get_logger().info(
                f"Robot Velocity - Linear X: {self.odom_state.linear_velocity_x:.6f} m/s, "
                f"Linear Y: {self.odom_state.linear_velocity_y:.6f} m/s"
            )

    def joint_states_callback(self, msg):
        if len(msg.data) != 12:
            self.get_logger().error(f"Unexpected number of joint angles: {len(msg.data)}. Expected 12.")
            return
        self.odom_state.joint_positions = list(msg.data)
        if self.verbose:
            self.get_logger().info(f"Joint Positions: {self.odom_state.joint_positions}")

    def foot_contacts_callback(self, msg):
        if self.verbose:
            self.get_logger().info(f"Received foot_contacts message: {msg}")

        if len(msg.contacts) != 4:
            self.get_logger().error(f"Unexpected number of contacts: {len(msg.contacts)}. Expected 4.")
            self.odom_state.foot_contacts = [False, False, False, False]
            return

        self.odom_state.foot_contacts = list(msg.contacts)
        if self.verbose:
            self.get_logger().info(f"Foot Contacts: {self.odom_state.foot_contacts}")

    def imu_callback(self, msg):
        orientation_q = msg.orientation
        orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
        (roll, pitch, yaw) = tf_transformations.euler_from_quaternion(orientation_list)

        self.odom_state.theta = yaw
        self.odom_state.imu_angular_velocity = -msg.angular_velocity.z

        if self.verbose:
            self.get_logger().info(f"IMU Yaw: {self.odom_state.theta:.6f} rad")
            self.get_logger().info(f"IMU Angular Velocity: {self.odom_state.imu_angular_velocity:.6f} rad/s")

    def clock_callback(self, msg):
        self.odom_state.gazebo_clock_sec = msg.clock.sec
        self.odom_state.gazebo_clock_nanosec = msg.clock.nanosec
        if self.verbose:
            self.get_logger().info(f"Received Gazebo Clock: {self.odom_state.gazebo_clock_sec}.{self.odom_state.gazebo_clock_nanosec}")

    def encoder_callback(self, msg):
        self.odom_state.encoder_pos = msg.data
        if self.verbose:
            self.get_logger().info(f"Received Encoder Position: {self.odom_state.encoder_pos}")

    # ================================================================
    # Core logic
    # ================================================================

    def calculate_foot_positions(self):
        """Вычислить позиции лап через FK."""
        if len(self.odom_state.joint_positions) != 12:
            self.get_logger().error(f"Incorrect number of joint positions: {len(self.odom_state.joint_positions)}. Expected 12.")
            return

        try:
            foot_positions = self.fk_solver.forward_kinematics_all_legs(self.odom_state.joint_positions)
            self.odom_state.foot_positions = foot_positions
        except Exception as e:
            self.get_logger().error(f"Error in forward kinematics: {e}")
            self.odom_state.foot_positions = [(0.0, 0.0, 0.0)] * 4
            return

        if self.verbose:
            for i, pos in enumerate(self.odom_state.foot_positions):
                leg = ['FR', 'FL', 'RR', 'RL'][i]
                self.get_logger().info(f"{leg} Foot Position: x={pos[0]:.4f}, y={pos[1]:.4f}, z={pos[2]:.4f}")

    def update_odometry_step(self):
        """Обновить одометрию (делегирование к чистой функции)."""
        current_time = self.get_clock().now()
        dt = (current_time - self.last_position_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        update_odometry(self.odom_state, dt)

        if self.verbose:
            self.get_logger().info(f"Odometry updated: x={self.odom_state.x:.6f}, y={self.odom_state.y:.6f}, theta={self.odom_state.theta:.6f}")

        self.last_position_time = current_time

    def publish_odometry(self):
        """Опубликовать сообщение Odometry и TF."""
        odom = Odometry()
        if self.is_gazebo:
            stamp = Time(sec=self.odom_state.gazebo_clock_sec, nanosec=self.odom_state.gazebo_clock_nanosec)
        else:
            stamp = self.get_clock().now().to_msg()

        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.base_frame_id

        odom.pose.pose.position.x = self.odom_state.x
        odom.pose.pose.position.y = self.odom_state.y
        odom.pose.pose.position.z = 0.0

        quaternion = tf_transformations.quaternion_from_euler(0, 0, self.odom_state.theta)
        odom.pose.pose.orientation = Quaternion(
            x=quaternion[0],
            y=quaternion[1],
            z=quaternion[2],
            w=quaternion[3]
        )

        odom.twist.twist.linear.x = self.odom_state.linear_velocity_x
        odom.twist.twist.linear.y = self.odom_state.linear_velocity_y
        odom.twist.twist.angular.z = self.odom_state.imu_angular_velocity

        self.odom_pub.publish(odom)

        if self.enable_odom_tf:
            t = TransformStamped()
            t.header.stamp = stamp
            t.header.frame_id = self.odom_frame_id
            t.child_frame_id = self.base_frame_id

            t.transform.translation.x = self.odom_state.x
            t.transform.translation.y = self.odom_state.y
            t.transform.translation.z = 0.0
            t.transform.rotation = Quaternion(
                x=quaternion[0],
                y=quaternion[1],
                z=quaternion[2],
                w=quaternion[3]
            )

            self.tf_broadcaster.sendTransform(t)

    def publish_markers(self):
        """Опубликовать маркеры для визуализации лап."""
        marker_array = MarkerArray()
        for i, pos in enumerate(self.odom_state.foot_positions):
            marker = Marker()
            marker.header.frame_id = self.base_frame_id
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "foot_markers"
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose.position.x = pos[0]
            marker.pose.position.y = pos[1]
            marker.pose.position.z = pos[2]
            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.05
            marker.scale.y = 0.05
            marker.scale.z = 0.05
            marker.color.a = 1.0
            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker_array.markers.append(marker)
        self.marker_pub.publish(marker_array)

    def timer_callback(self):
        self.calculate_foot_positions()
        self.update_odometry_step()
        self.publish_odometry()
        self.publish_markers()

        if self.verbose:
            self.get_logger().info(
                f"Position Updated: x={self.odom_state.x:.6f} m, "
                f"y={self.odom_state.y:.6f} m, "
                f"theta={self.odom_state.theta:.6f} rad"
            )


def main(args=None):
    rclpy.init(args=args)
    try:
        node = DogOdometry()
    except Exception as e:
        print(f"Exception during node initialization: {e}")
        rclpy.shutdown()
        return
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
