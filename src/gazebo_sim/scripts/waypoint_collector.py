#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, PoseArray
from visualization_msgs.msg import Marker, MarkerArray
from nav2_msgs.action import FollowWaypoints
from nav2_simple_commander.robot_navigator import BasicNavigator
from std_msgs.msg import ColorRGBA
from std_srvs.srv import Trigger
from action_msgs.msg import GoalStatus
import threading


class WaypointCollector(Node):
    def __init__(self):
        super().__init__("waypoint_collector")
        self.waypoints = []
        ns = self.get_namespace().lstrip('/')
        self.navigator = BasicNavigator(namespace=ns)

        # Own ActionClient on this node (which is in the executor)
        self._follow_wp_client = ActionClient(
            self, FollowWaypoints, 'follow_waypoints'
        )

        self.navigation_active = False
        self._nav_goal_handle = None
        self._nav_result_future = None

        self.subscription = self.create_subscription(
            PoseStamped, "/custom_goal_pose", self.goal_pose_callback, 10
        )

        self.waypoint_publisher = self.create_publisher(
            PoseArray, "/custom_waypoints", 10
        )

        self.marker_publisher = self.create_publisher(
            MarkerArray, "/waypoint_markers", 10
        )

        self.clear_service = self.create_service(
            Trigger, "/clear_waypoints", self.clear_waypoints_callback
        )

        self.start_service = self.create_service(
            Trigger, "/start_navigation", self.start_navigation_callback
        )

        self.timer = self.create_timer(0.1, self.check_navigation)

        self.nav2_ready = False
        self._start_nav2_wait_thread()

        self.get_logger().info("Waypoint Collector Node started")

    def goal_pose_callback(self, msg):
        self.waypoints.append(msg)
        self.get_logger().info(
            f"Added waypoint: x={msg.pose.position.x}, y={msg.pose.position.y}, total waypoints: {len(self.waypoints)}"
        )
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

            color = ColorRGBA()
            if i % 3 == 0:
                color.r, color.g, color.b, color.a = 1.0, 0.0, 0.0, 1.0
            elif i % 3 == 1:
                color.r, color.g, color.b, color.a = 0.0, 1.0, 0.0, 1.0
            else:
                color.r, color.g, color.b, color.a = 0.0, 0.0, 1.0, 1.0

            marker.color = color
            marker_array.markers.append(marker)

        self.marker_publisher.publish(marker_array)
        self.get_logger().info(
            f"Published {len(self.waypoints)} markers to /waypoint_markers"
        )

    def clear_waypoints_callback(self, request, response):
        try:
            if self.navigation_active:
                self.cancel_navigation()
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

        if not self.nav2_ready:
            self.get_logger().warn("Nav2 is not ready yet, waiting...")
            response.success = False
            response.message = "Nav2 is not ready yet"
            return response

        try:
            pose_array = PoseArray()
            pose_array.header.frame_id = "map"
            pose_array.header.stamp = self.get_clock().now().to_msg()
            pose_array.poses = [wp.pose for wp in self.waypoints]
            self.waypoint_publisher.publish(pose_array)
            self.get_logger().info(
                f"Published {len(self.waypoints)} waypoints to /custom_waypoints"
            )

            self.navigation_active = True
            self._send_goal_async()
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

    def _send_goal_async(self):
        goal_msg = FollowWaypoints.Goal()
        goal_msg.poses = [wp.pose for wp in self.waypoints]

        self._follow_wp_client.wait_for_server(timeout_sec=1.0)
        send_goal_future = self._follow_wp_client.send_goal_async(
            goal_msg, self._feedback_callback
        )
        send_goal_future.add_done_callback(self._goal_response_callback)

    def _feedback_callback(self, feedback_msg):
        self.get_logger().info(
            f"Current waypoint: {feedback_msg.feedback.current_waypoint}"
        )

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("FollowWaypoints goal was rejected")
            self.navigation_active = False
            return

        self._nav_goal_handle = goal_handle
        self.get_logger().info("FollowWaypoints goal accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        result = future.result()
        self._nav_result_future = future
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("Navigation SUCCEEDED")
        elif result.status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error("Navigation FAILED (aborted)")
        elif result.status == GoalStatus.STATUS_CANCELED:
            self.get_logger().info("Navigation CANCELED")
        else:
            self.get_logger().warn(f"Navigation result status: {result.status}")
        self.navigation_active = False

    def cancel_navigation(self):
        if self._nav_goal_handle:
            self._nav_goal_handle.cancel_goal_async()
        self.navigation_active = False

    def check_navigation(self):
        if self.navigation_active and self._nav_result_future:
            if self._nav_result_future.result():
                status = self._nav_result_future.result().status
                if status != GoalStatus.STATUS_SUCCEEDED and status != GoalStatus.STATUS_EXECUTING:
                    self.get_logger().info(f"Navigation completed with status: {status}")
                    self.navigation_active = False

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
