#!/usr/bin/env python3
"""Демонстрационный издатель для 2D RViz-панели супервизорного контроля.

Публикует:
  /map          nav_msgs/OccupancyGrid
  /plan         nav_msgs/Path
  /waypoints    visualization_msgs/MarkerArray
  /robot        visualization_msgs/MarkerArray
  /events       visualization_msgs/MarkerArray
  /status       visualization_msgs/MarkerArray

Запуск:
  source /opt/ros/lyrical/setup.bash
  python3 demo_publisher.py [--animate]
"""

from __future__ import annotations

import argparse
import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from visualization_msgs.msg import Marker, MarkerArray

MAP_W = 200
MAP_H = 200
RES = 0.05
ORIGIN_X = -5.0
ORIGIN_Y = -5.0

WAYPOINTS = [
    ("A", -3.0, -2.0),
    ("B", 0.0, 0.0),
    ("C", 3.0, 2.0),
]
OBSTACLE = (1.2, 0.8)

COLOR_PATH = (0.0, 0.40, 0.0, 1.0)       # тёмно-зелёный
COLOR_CURRENT = (0.78, 0.39, 0.0, 1.0)  # тёмно-оранжевый
COLOR_NEXT = (0.0, 0.45, 0.95, 1.0)     # синий
COLOR_PASSED = (0.45, 0.45, 0.45, 1.0)  # серый
COLOR_ROBOT = (0.78, 0.0, 0.78, 1.0)    # пурпурный
COLOR_OBSTACLE = (0.78, 0.0, 0.0, 1.0)  # красный
COLOR_TEXT = (0.10, 0.10, 0.10, 1.0)    # почти чёрный
COLOR_EVENT_TEXT = (0.65, 0.0, 0.0, 1.0)


def make_map() -> OccupancyGrid:
    grid = OccupancyGrid()
    grid.header.frame_id = "map"
    grid.info.resolution = RES
    grid.info.width = MAP_W
    grid.info.height = MAP_H
    grid.info.origin.position.x = ORIGIN_X
    grid.info.origin.position.y = ORIGIN_Y
    grid.info.origin.orientation.w = 1.0

    data = [0] * (MAP_W * MAP_H)

    def set_cell(x: int, y: int, value: int = 100) -> None:
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            data[y * MAP_W + x] = value

    # Внешние стены
    for x in range(MAP_W):
        set_cell(x, 0)
        set_cell(x, 1)
        set_cell(x, MAP_H - 1)
        set_cell(x, MAP_H - 2)
    for y in range(MAP_H):
        set_cell(0, y)
        set_cell(1, y)
        set_cell(MAP_W - 1, y)
        set_cell(MAP_W - 2, y)

    # Внутренняя стена: x = 2.0, y = -4.0..1.0
    wall_x = int((2.0 - ORIGIN_X) / RES)
    for y in range(int((-4.0 - ORIGIN_Y) / RES), int((1.0 - ORIGIN_Y) / RES)):
        set_cell(wall_x, y)
        set_cell(wall_x + 1, y)

    # Внутренняя стена: y = -3.0, x = -4.0..-1.0
    wall_y = int((-3.0 - ORIGIN_Y) / RES)
    for x in range(int((-4.0 - ORIGIN_X) / RES), int((-1.0 - ORIGIN_X) / RES)):
        set_cell(x, wall_y)
        set_cell(x, wall_y + 1)

    # Препятствие на пути B -> C
    ox = int((OBSTACLE[0] - ORIGIN_X) / RES)
    oy = int((OBSTACLE[1] - ORIGIN_Y) / RES)
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                set_cell(ox + dx, oy + dy)

    grid.data = data
    return grid


def interpolate_path() -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for (_, x0, y0), (_, x1, y1) in zip(WAYPOINTS, WAYPOINTS[1:]):
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(2, int(dist / 0.05))
        for i in range(steps):
            t = i / steps
            points.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    points.append((WAYPOINTS[-1][1], WAYPOINTS[-1][2]))
    return points


def make_path(points: list[tuple[float, float]], stamp) -> Path:
    path = Path()
    path.header.frame_id = "map"
    path.header.stamp = stamp
    for i, (x, y) in enumerate(points):
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = stamp
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        if i + 1 < len(points):
            dx = points[i + 1][0] - x
            dy = points[i + 1][1] - y
            yaw = math.atan2(dy, dx)
        else:
            yaw = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        path.poses.append(pose)
    return path


def marker_base(frame_id: str, ns: str, mid: int, mtype: int) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.ns = ns
    m.id = mid
    m.type = mtype
    m.action = Marker.ADD
    m.pose.orientation.w = 1.0
    return m


def add_text(
    arr: MarkerArray,
    ns: str,
    mid: int,
    text: str,
    x: float,
    y: float,
    z: float,
    scale: float,
    color: tuple[float, float, float, float],
) -> None:
    m = marker_base("map", ns, mid, Marker.TEXT_VIEW_FACING)
    m.pose.position.x = x
    m.pose.position.y = y
    m.pose.position.z = z
    m.scale.z = scale
    m.color.r, m.color.g, m.color.b, m.color.a = color
    m.text = text
    arr.markers.append(m)


def make_waypoints() -> MarkerArray:
    arr = MarkerArray()
    for i, (label, x, y) in enumerate(WAYPOINTS):
        if label == "B":
            color = COLOR_CURRENT
            scale = 0.40
            text_color = COLOR_CURRENT
        elif label == "C":
            color = COLOR_NEXT
            scale = 0.35
            text_color = COLOR_NEXT
        else:
            color = COLOR_PASSED
            scale = 0.25
            text_color = COLOR_PASSED

        m = marker_base("map", "waypoints", i, Marker.CYLINDER)
        m.pose.position.x = x
        m.pose.position.y = y
        m.pose.position.z = 0.02
        m.scale.x = scale
        m.scale.y = scale
        m.scale.z = 0.04
        m.color.r, m.color.g, m.color.b, m.color.a = color
        arr.markers.append(m)

        add_text(arr, "waypoint_labels", 100 + i, label, x, y + 0.38, 0.15, 0.30, text_color)
    return arr


def make_robot(x: float, y: float, yaw: float) -> MarkerArray:
    arr = MarkerArray()

    disk = marker_base("map", "robot", 0, Marker.CYLINDER)
    disk.pose.position.x = x
    disk.pose.position.y = y
    disk.pose.position.z = 0.03
    disk.scale.x = 0.60
    disk.scale.y = 0.60
    disk.scale.z = 0.05
    disk.color.r, disk.color.g, disk.color.b, disk.color.a = COLOR_ROBOT
    arr.markers.append(disk)

    arrow = marker_base("map", "robot", 1, Marker.ARROW)
    arrow.pose.position.x = x
    arrow.pose.position.y = y
    arrow.pose.position.z = 0.06
    arrow.pose.orientation.z = math.sin(yaw / 2.0)
    arrow.pose.orientation.w = math.cos(yaw / 2.0)
    arrow.scale.x = 0.85
    arrow.scale.y = 0.18
    arrow.scale.z = 0.10
    arrow.color.r = 0.05
    arrow.color.g = 0.05
    arrow.color.b = 0.05
    arrow.color.a = 1.0
    arr.markers.append(arrow)
    return arr


def make_events() -> MarkerArray:
    arr = MarkerArray()

    obs = marker_base("map", "events", 0, Marker.CYLINDER)
    obs.pose.position.x = OBSTACLE[0]
    obs.pose.position.y = OBSTACLE[1]
    obs.pose.position.z = 0.04
    obs.scale.x = 0.55
    obs.scale.y = 0.55
    obs.scale.z = 0.06
    obs.color.r, obs.color.g, obs.color.b, obs.color.a = COLOR_OBSTACLE
    arr.markers.append(obs)

    add_text(
        arr,
        "event_labels",
        1,
        "STUCK_AT_OBSTACLE",
        OBSTACLE[0] + 1.2,
        OBSTACLE[1] + 0.55,
        0.20,
        0.22,
        COLOR_EVENT_TEXT,
    )
    return arr


def make_status() -> MarkerArray:
    arr = MarkerArray()
    lines = [
        "MODE: SUPERVISORY",
        "WP: B -> C",
        "EVENT: STUCK_AT_OBSTACLE",
        "ACTION: REPLAN / CONFIRM 2.5 s",
    ]
    for i, line in enumerate(lines):
        add_text(arr, "status", i, line, -4.55, 4.45 - i * 0.42, 0.20, 0.24, COLOR_TEXT)
    return arr


class DemoPublisher(Node):
    def __init__(self, animate: bool) -> None:
        super().__init__("rviz_supervisory_demo")
        self.animate = animate
        self.points = interpolate_path()
        self.path_len = self._path_length()
        self.t0 = self.get_clock().now()
        self.tick = 0

        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )

        self.map_pub = self.create_publisher(OccupancyGrid, "/map", map_qos)
        self.path_pub = self.create_publisher(Path, "/plan", 10)
        self.wp_pub = self.create_publisher(MarkerArray, "/waypoints", 10)
        self.robot_pub = self.create_publisher(MarkerArray, "/robot", 10)
        self.event_pub = self.create_publisher(MarkerArray, "/events", 10)
        self.status_pub = self.create_publisher(MarkerArray, "/status", 10)

        self.map = make_map()
        self.map.header.stamp = self.get_clock().now().to_msg()
        self.map_pub.publish(self.map)
        self.timer = self.create_timer(0.1, self.on_timer)

    def _path_length(self) -> float:
        total = 0.0
        for (x0, y0), (x1, y1) in zip(self.points, self.points[1:]):
            total += math.hypot(x1 - x0, y1 - y0)
        return total

    def _pose_at(self, distance: float) -> tuple[float, float, float]:
        distance = max(0.0, min(distance, self.path_len))
        run = 0.0
        for (x0, y0), (x1, y1) in zip(self.points, self.points[1:]):
            seg = math.hypot(x1 - x0, y1 - y0)
            if run + seg >= distance:
                t = (distance - run) / max(seg, 1e-9)
                x = x0 + (x1 - x0) * t
                y = y0 + (y1 - y0) * t
                yaw = math.atan2(y1 - y0, x1 - x0)
                return x, y, yaw
            run += seg
        x1, y1 = self.points[-1]
        x0, y0 = self.points[-2]
        return x1, y1, math.atan2(y1 - y0, x1 - x0)

    def on_timer(self) -> None:
        stamp = self.get_clock().now().to_msg()

        if self.animate:
            elapsed = (self.get_clock().now() - self.t0).nanoseconds / 1e9
            distance = (elapsed * 0.5) % self.path_len
        else:
            distance = 1.9

        x, y, yaw = self._pose_at(distance)
        self.path_pub.publish(make_path(self.points, stamp))
        self.wp_pub.publish(make_waypoints())
        self.robot_pub.publish(make_robot(x, y, yaw))
        self.event_pub.publish(make_events())
        self.status_pub.publish(make_status())

        self.tick += 1
        if self.tick % 20 == 0:
            self.map.header.stamp = stamp
            self.map_pub.publish(self.map)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--animate", action="store_true")
    args = parser.parse_args()
    rclpy.init()
    node = DemoPublisher(animate=args.animate)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
