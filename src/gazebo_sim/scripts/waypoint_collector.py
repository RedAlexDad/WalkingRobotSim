#!/usr/bin/env python3
"""
Waypoint Collector Node
Подписывается на /custom_goal_pose для добавления waypoints без автоматической навигации.
Запускает навигацию по waypoints только по вызову сервиса /start_navigation.
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from geometry_msgs.msg import PoseStamped, PoseArray
from visualization_msgs.msg import Marker, MarkerArray
from nav2_simple_commander.robot_navigator import BasicNavigator
from std_msgs.msg import ColorRGBA
from std_srvs.srv import Trigger
import tf_transformations
import threading


class WaypointCollector(Node):
    def __init__(self):
        super().__init__("waypoint_collector")
        self.waypoints = []  # Список для хранения waypoints
        # Используем тот же namespace, что и у этой ноды (например, /robot1),
        # чтобы BasicNavigator искал action серверы в правильном namespace
        ns = self.get_namespace().lstrip('/')
        self.navigator = BasicNavigator(namespace=ns)
        self.navigation_active = False  # Флаг активной навигации

        # Подписка на /custom_goal_pose (вместо /goal_pose)
        self.subscription = self.create_subscription(
            PoseStamped, "/custom_goal_pose", self.goal_pose_callback, 10
        )

        # Публикация в /custom_waypoints
        self.waypoint_publisher = self.create_publisher(
            PoseArray, "/custom_waypoints", 10
        )

        # Публикация маркеров для визуализации waypoints
        self.marker_publisher = self.create_publisher(
            MarkerArray, "/waypoint_markers", 10
        )

        # Сервис для очистки waypoints
        self.clear_service = self.create_service(
            Trigger, "/clear_waypoints", self.clear_waypoints_callback
        )

        # Сервис для запуска навигации
        self.start_service = self.create_service(
            Trigger, "/start_navigation", self.start_navigation_callback
        )

        # Таймер для проверки навигации
        self.timer = self.create_timer(0.1, self.check_navigation)
        # Таймер для спина BasicNavigator (global executor свободен, т.к. main() использует свой executor)
        self.create_timer(0.5, self._spin_basic_navigator)

        # Запуск ожидания Nav2 в отдельном потоке, чтобы не блокировать конструктор
        self.nav2_ready = False
        self._start_nav2_wait_thread()

        self.get_logger().info("Waypoint Collector Node started")

    def goal_pose_callback(self, msg):
        # Добавление новой позы в список waypoints
        self.waypoints.append(msg)
        self.get_logger().info(
            f"Added waypoint: x={msg.pose.position.x}, y={msg.pose.position.y}, total waypoints: {len(self.waypoints)}"
        )
        # Публикация маркеров сразу после добавления новой точки
        self.publish_markers()

    def publish_markers(self):
        marker_array = MarkerArray()

        for i, wp in enumerate(self.waypoints):
            marker = Marker()
            marker.header.frame_id = "map"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "waypoints"
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose = wp.pose
            marker.scale.x = 0.2
            marker.scale.y = 0.2
            marker.scale.z = 0.2

            # Назначение цветов
            color = ColorRGBA()
            if i % 3 == 0:
                color.r, color.g, color.b, color.a = 1.0, 0.0, 0.0, 1.0  # Красный
            elif i % 3 == 1:
                color.r, color.g, color.b, color.a = 0.0, 1.0, 0.0, 1.0  # Зелёный
            else:
                color.r, color.g, color.b, color.a = 0.0, 0.0, 1.0, 1.0  # Синий

            marker.color = color
            marker_array.markers.append(marker)

        self.marker_publisher.publish(marker_array)
        self.get_logger().info(
            f"Published {len(self.waypoints)} markers to /waypoint_markers"
        )

    def clear_waypoints_callback(self, request, response):
        # Немедленная очистка waypoints и маркеров
        try:
            if self.navigation_active:
                self.navigator.cancelTask()
                self.get_logger().info("Canceled active navigation task")
        except Exception as e:
            self.get_logger().error(f"Failed to cancel navigation task: {str(e)}")

        self.waypoints = []
        self.navigation_active = False
        marker_array = MarkerArray()
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "waypoints"
        marker.id = 0
        marker.action = Marker.DELETEALL
        marker_array.markers.append(marker)
        self.marker_publisher.publish(marker_array)
        self.get_logger().info("Waypoints and markers cleared via service call")
        response.success = True
        response.message = "Waypoints cleared successfully"
        return response

    def start_navigation_callback(self, request, response):
        # Запуск навигации по текущему списку waypoints
        if not self.waypoints:
            self.get_logger().warn("No waypoints available to start navigation")
            response.success = False
            response.message = "No waypoints to navigate"
            return response

        if self.navigation_active:
            self.get_logger().warn("Navigation is already active")
            response.success = False
            response.message = "Navigation is already active"
            return response

        try:
            # Публикация waypoints в /custom_waypoints
            pose_array = PoseArray()
            pose_array.header.frame_id = "map"
            pose_array.header.stamp = self.get_clock().now().to_msg()
            pose_array.poses = [wp.pose for wp in self.waypoints]
            self.waypoint_publisher.publish(pose_array)
            self.get_logger().info(
                f"1111 Published {len(self.waypoints)} waypoints to /custom_waypoints"
            )

            # Асинхронный запуск навигации
            self.navigation_active = True
            self.navigator.followWaypoints(self.waypoints)
            self.get_logger().info(
                f"Sent {len(self.waypoints)} waypoints to FollowWaypoints action"
            )
            response.success = True
            response.message = "Navigation started successfully"
        except Exception as e:
            self.get_logger().error(f"Failed to start navigation: {str(e)}")
            self.navigation_active = False
            response.success = False
            response.message = f"Failed to start navigation: {str(e)}"
        return response

    def _spin_basic_navigator(self):
        rclpy.spin_once(self.navigator, timeout_sec=0)

    def _start_nav2_wait_thread(self):
        thread = threading.Thread(target=self._wait_for_nav2, daemon=True)
        thread.start()

    def _wait_for_nav2(self):
        try:
            self.get_logger().info("Waiting for Nav2 to become active...")
            self.navigator.waitUntilNav2Active()
            self.nav2_ready = True
            self.get_logger().info("Nav2 is active")
        except Exception as e:
            self.get_logger().error(f"Failed to activate Nav2: {str(e)}")

    def check_navigation(self):
        # Проверка завершения навигации
        if self.navigation_active and self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                self.get_logger().info(f"Current waypoint: {feedback.current_waypoint}")
            result = self.navigator.getResult()
            self.get_logger().info(f"Navigation result: {result}")
            self.navigation_active = False
            self.get_logger().info("Navigation completed, ready for new start command")


def main(args=None):
    rclpy.init(args=args)
    node = WaypointCollector()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
