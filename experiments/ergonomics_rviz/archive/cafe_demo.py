#!/usr/bin/env python3
"""2D RViz demo for the ergonomics KR: cafe map + waypoint route.

Publishes:
  /map        nav_msgs/OccupancyGrid  (cafe_world_map.pgm)
  /plan       nav_msgs/Path           (points 1..5 from default.yaml)
  /waypoints  visualization_msgs/MarkerArray
  /robot      visualization_msgs/MarkerArray
  /events     visualization_msgs/MarkerArray
  /status     visualization_msgs/MarkerArray

Run:
  source /opt/ros/lyrical/setup.bash
  python3 cafe_demo.py
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path as FsPath

import numpy as np
import rclpy
import yaml
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from PIL import Image
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from visualization_msgs.msg import Marker, MarkerArray

REPO = FsPath(__file__).resolve().parents[2]
MAP_YAML = REPO / "src/gazebo_sim/maps/cafe_world_map.yaml"
WAYPOINT_YAML = REPO / "src/gazebo_sim/config/waypoints/default.yaml"

# Ready points 1..5 from default.yaml (all segments are free on the cafe map).
WAYPOINT_IDS = [1, 2, 3, 4, 5]
CURRENT_ID = 4
NEXT_ID = 5
OBSTACLE = (-1.93, -1.00)

COLOR_PATH = (0.0, 0.40, 0.0, 1.0)
COLOR_CURRENT = (0.78, 0.39, 0.0, 1.0)
COLOR_NEXT = (0.0, 0.45, 0.95, 1.0)
COLOR_PASSED = (0.45, 0.45, 0.45, 1.0)
COLOR_FUTURE = (0.65, 0.65, 0.65, 1.0)
COLOR_ROBOT = (0.78, 0.0, 0.78, 1.0)
COLOR_OBSTACLE = (0.78, 0.0, 0.0, 1.0)
COLOR_TEXT = (0.10, 0.10, 0.10, 1.0)
COLOR_EVENT_TEXT = (0.65, 0.0, 0.0, 1.0)
COLOR_PANEL = (0.90, 0.90, 0.90, 0.98)


def load_map() -> tuple[OccupancyGrid, dict]:
    meta = yaml.safe_load(MAP_YAML.read_text(encoding="utf-8"))
    image_path = MAP_YAML.parent / meta["image"]
    img = np.array(Image.open(image_path).convert("L"))
    # PGM row 0 is top; OccupancyGrid row 0 is bottom.
    img = np.flipud(img)
    occ = (255.0 - img) / 255.0 if not meta.get("negate", 0) else img / 255.0

    data: list[int] = []
    for row in occ:
        for value in row:
            if value > meta["occupied_thresh"]:
                data.append(100)
            elif value < meta["free_thresh"]:
                data.append(0)
            else:
                data.append(-1)

    grid = OccupancyGrid()
    grid.header.frame_id = "map"
    grid.info.resolution = float(meta["resolution"])
    grid.info.width = int(occ.shape[1])
    grid.info.height = int(occ.shape[0])
    grid.info.origin.position.x = float(meta["origin"][0])
    grid.info.origin.position.y = float(meta["origin"][1])
    grid.info.origin.position.z = 0.0
    grid.info.origin.orientation.w = 1.0
    grid.data = data
    return grid, meta


def load_waypoints() -> list[dict]:
    raw = yaml.safe_load(WAYPOINT_YAML.read_text(encoding="utf-8"))
    # default.yaml is a list of dicts; support both list and {waypoints: [...]}.
    if isinstance(raw, dict):
        raw = raw.get("waypoints", [])
    by_id = {i: p for i, p in enumerate(raw)}
    return [{"id": i, **by_id[i]} for i in WAYPOINT_IDS]


def interpolate(points: list[dict]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for a, b in zip(points, points[1:]):
        x0, y0 = float(a["x"]), float(a["y"])
        x1, y1 = float(b["x"]), float(b["y"])
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(2, int(dist / 0.05))
        for i in range(steps):
            t = i / steps
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append((float(points[-1]["x"]), float(points[-1]["y"])))
    return out


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
            yaw = math.atan2(points[i + 1][1] - y, points[i + 1][0] - x)
        else:
            yaw = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        path.poses.append(pose)
    return path


def marker(frame_id: str, ns: str, mid: int, mtype: int) -> Marker:
    m = Marker()
    m.header.frame_id = frame_id
    m.ns = ns
    m.id = mid
    m.type = mtype
    m.action = Marker.ADD
    m.pose.orientation.w = 1.0
    return m


def text(
    arr: MarkerArray,
    ns: str,
    mid: int,
    value: str,
    x: float,
    y: float,
    z: float,
    scale: float,
    color: tuple[float, float, float, float],
) -> None:
    m = marker("map", ns, mid, Marker.TEXT_VIEW_FACING)
    m.pose.position.x = x
    m.pose.position.y = y
    m.pose.position.z = z
    m.scale.z = scale
    m.color.r, m.color.g, m.color.b, m.color.a = color
    m.text = value
    arr.markers.append(m)


def make_waypoints(points: list[dict]) -> MarkerArray:
    arr = MarkerArray()
    for i, p in enumerate(points):
        pid = int(p["id"])
        x, y = float(p["x"]), float(p["y"])
        if pid == CURRENT_ID:
            color, scale = COLOR_CURRENT, 0.45
        elif pid == NEXT_ID:
            color, scale = COLOR_NEXT, 0.40
        elif pid < CURRENT_ID:
            color, scale = COLOR_PASSED, 0.28
        else:
            color, scale = COLOR_FUTURE, 0.28

        m = marker("map", "waypoints", i, Marker.CYLINDER)
        m.pose.position.x = x
        m.pose.position.y = y
        m.pose.position.z = 0.02
        m.scale.x = scale
        m.scale.y = scale
        m.scale.z = 0.04
        m.color.r, m.color.g, m.color.b, m.color.a = color
        arr.markers.append(m)

        text(arr, "waypoint_labels", 100 + i, str(pid), x, y + 0.42, 0.15, 0.34, color)
    return arr


def make_robot(x: float, y: float, yaw: float) -> MarkerArray:
    arr = MarkerArray()

    disk = marker("map", "robot", 0, Marker.CYLINDER)
    disk.pose.position.x = x
    disk.pose.position.y = y
    disk.pose.position.z = 0.03
    disk.scale.x = 0.60
    disk.scale.y = 0.60
    disk.scale.z = 0.05
    disk.color.r, disk.color.g, disk.color.b, disk.color.a = COLOR_ROBOT
    arr.markers.append(disk)

    arrow = marker("map", "robot", 1, Marker.ARROW)
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

    obs = marker("map", "events", 0, Marker.CYLINDER)
    obs.pose.position.x = OBSTACLE[0]
    obs.pose.position.y = OBSTACLE[1]
    obs.pose.position.z = 0.04
    obs.scale.x = 0.55
    obs.scale.y = 0.55
    obs.scale.z = 0.06
    obs.color.r, obs.color.g, obs.color.b, obs.color.a = COLOR_OBSTACLE
    arr.markers.append(obs)

    text(
        arr,
        "event_labels",
        1,
        "STUCK_AT_OBSTACLE",
        OBSTACLE[0] + 0.9,
        OBSTACLE[1] - 0.55,
        0.20,
        0.30,
        COLOR_EVENT_TEXT,
    )
    return arr


def make_status() -> MarkerArray:
    arr = MarkerArray()

    # Light panel outside the cafe map, dark text on it.
    panel = marker("map", "status_panel", 0, Marker.CUBE)
    panel.pose.position.x = 7.6
    panel.pose.position.y = -7.8
    panel.pose.position.z = 0.01
    panel.scale.x = 5.6
    panel.scale.y = 2.4
    panel.scale.z = 0.02
    panel.color.r, panel.color.g, panel.color.b, panel.color.a = COLOR_PANEL
    arr.markers.append(panel)

    lines = [
        "MODE: SUPERVISORY",
        f"WP: {CURRENT_ID} -> {NEXT_ID}",
        "EVENT: STUCK_AT_OBSTACLE",
        "ACTION: REPLAN / CONFIRM 2.5 s",
    ]
    for i, line in enumerate(lines):
        text(arr, "status_text", 10 + i, line, 5.55, -7.05 - i * 0.48, 0.05, 0.30, COLOR_TEXT)
    return arr


class CafeDemo(Node):
    def __init__(self) -> None:
        super().__init__("cafe_rviz_supervisory_demo")
        self.map, self.meta = load_map()
        self.waypoints = load_waypoints()
        self.path_points = interpolate(self.waypoints)
        self.map.header.stamp = self.get_clock().now().to_msg()

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

        self.map_pub.publish(self.map)
        self.timer = self.create_timer(0.1, self.on_timer)

    def on_timer(self) -> None:
        stamp = self.get_clock().now().to_msg()
        self.path_pub.publish(make_path(self.path_points, stamp))
        self.wp_pub.publish(make_waypoints(self.waypoints))
        self.robot_pub.publish(make_robot(*self._robot_pose()))
        self.event_pub.publish(make_events())
        self.status_pub.publish(make_status())

    def _robot_pose(self) -> tuple[float, float, float]:
        current = next(p for p in self.waypoints if int(p["id"]) == CURRENT_ID)
        nxt = next(p for p in self.waypoints if int(p["id"]) == NEXT_ID)
        x, y = float(current["x"]), float(current["y"])
        yaw = math.atan2(float(nxt["y"]) - y, float(nxt["x"]) - x)
        return x, y, yaw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="publish once and exit")
    args = parser.parse_args()
    rclpy.init()
    node = CafeDemo()
    try:
        if args.once:
            node.map_pub.publish(node.map)
            node.on_timer()
        else:
            rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
