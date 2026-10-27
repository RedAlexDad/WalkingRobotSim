#!/usr/bin/env python3
"""Operator IM demo for the RViz configuration.

Publishes:
  /cafe_map       nav_msgs/OccupancyGrid  static cafe map
  /im_path        nav_msgs/Path           current -> next leg
  /im_waypoints   visualization_msgs/MarkerArray
  /im_robot       visualization_msgs/MarkerArray
  /im_status      visualization_msgs/MarkerArray  status + legend
  /im_event       visualization_msgs/MarkerArray  event + obstacle
  /im_confirm     visualization_msgs/MarkerArray  confirm/cancel buttons

State is changed with std_msgs/String on /im_state:
  normal | confirm | confirmed | cancelled | stuck

The confirmation buttons are visual markers only. Clicking requires a
custom RViz panel or an external control node; see README_im_operator.md.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path as FsPath

import numpy as np
import rclpy
import yaml
from PIL import Image
from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray

try:
    REPO = FsPath(__file__).resolve().parents[2]
except IndexError:  # running as /tmp/im_publisher.py in the container
    REPO = FsPath(__file__).resolve().parent
DEFAULT_MAP = REPO / "src/gazebo_sim/maps/cafe_world_map.yaml"
DEFAULT_WP = REPO / "src/gazebo_sim/config/waypoints/default.yaml"
CONTAINER_MAP = FsPath(
    "/root/ws/install/gazebo_sim/share/gazebo_sim/maps/cafe_world_map.yaml"
)
CONTAINER_WP = FsPath(
    "/root/ws/install/gazebo_sim/share/gazebo_sim/config/waypoints/default.yaml"
)

COLOR_PATH = (0.0, 0.40, 0.0, 1.0)
COLOR_CURRENT = (0.78, 0.39, 0.0, 1.0)
COLOR_NEXT = (0.0, 0.50, 1.0, 1.0)
COLOR_FUTURE = (0.55, 0.55, 0.55, 1.0)
COLOR_LABEL = (0.02, 0.02, 0.02, 1.0)
COLOR_ARROW = (0.02, 0.02, 0.02, 1.0)
COLOR_PANEL = (0.06, 0.06, 0.06, 0.97)
COLOR_EVENT_BAD = (0.32, 0.02, 0.02, 0.97)
COLOR_EVENT_OK = (0.0, 0.30, 0.0, 0.97)
COLOR_EVENT_WARN = (0.38, 0.22, 0.0, 0.97)
COLOR_CONFIRM = (0.0, 0.35, 0.0, 0.98)
COLOR_CANCEL = (0.45, 0.0, 0.0, 0.98)
COLOR_WHITE = (1.0, 1.0, 1.0, 1.0)
COLOR_BORDER = (0.75, 0.75, 0.75, 1.0)
MAX_WP = 64
COLOR_LEGEND = (0.08, 0.08, 0.08, 0.97)
COLOR_OBS_FILL = (0.62, 0.05, 0.05, 0.92)
COLOR_OBS_EDGE = (0.05, 0.05, 0.05, 1.0)

STATE_CONFIG = {
    "normal": {
        "event": "SYSTEM NOMINAL",
        "panel": COLOR_EVENT_OK,
        "cause": "NONE",
        "action": "NONE",
        "deadline": "N/A",
        "robot": "READY",
        "buttons": False,
        "advance": False,
        "obstacle": False,
    },
    "confirm": {
        "event": "CONFIRMATION_REQUIRED",
        "panel": COLOR_EVENT_BAD,
        "cause": "REPLAN NEEDED",
        "action": "OK / NO",
        "deadline": "2.5 s",
        "robot": "WAITING",
        "buttons": True,
        "advance": False,
        "obstacle": False,
    },
    "confirmed": {
        "event": "CONFIRMED",
        "panel": COLOR_EVENT_OK,
        "cause": "OPERATOR",
        "action": "NEXT LEG",
        "deadline": "N/A",
        "robot": "CONFIRMED",
        "buttons": False,
        "advance": False,
        "obstacle": False,
    },
    "cancelled": {
        "event": "CANCELLED",
        "panel": COLOR_EVENT_WARN,
        "cause": "OPERATOR",
        "action": "HOLD",
        "deadline": "N/A",
        "robot": "HOLD",
        "buttons": False,
        "advance": False,
        "obstacle": False,
    },
    "stuck": {
        "event": "STUCK_AT_OBSTACLE",
        "panel": COLOR_EVENT_BAD,
        "cause": "OBSTACLE",
        "action": "OK / NO",
        "deadline": "2.5 s",
        "robot": "BLOCKED",
        "buttons": True,
        "advance": False,
        "obstacle": True,
    },
}


def resolve(path: FsPath, fallback: FsPath) -> FsPath:
    if path.exists():
        return path
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"not found: {path} and {fallback}")


def load_map(yaml_path: FsPath) -> OccupancyGrid:
    meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    image_path = yaml_path.parent / meta["image"]
    img = np.array(Image.open(image_path).convert("L"))
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
    return grid


def marker(frame: str, ns: str, mid: int, mtype: int) -> Marker:
    m = Marker()
    m.header.frame_id = frame
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


def add_box(
    arr: MarkerArray,
    ns: str,
    mid: int,
    cx: float,
    cy: float,
    w: float,
    h: float,
    color: tuple[float, float, float, float],
    z: float = 0.01,
) -> None:
    m = marker("map", ns, mid, Marker.CUBE)
    m.pose.position.x = cx
    m.pose.position.y = cy
    m.pose.position.z = z
    m.scale.x = w
    m.scale.y = h
    m.scale.z = 0.02
    m.color.r, m.color.g, m.color.b, m.color.a = color
    arr.markers.append(m)


def add_border(
    arr: MarkerArray,
    ns: str,
    mid: int,
    cx: float,
    cy: float,
    w: float,
    h: float,
    alpha: float = 1.0,
) -> None:
    m = marker("map", ns, mid, Marker.LINE_STRIP)
    m.pose.position.z = 0.03
    m.scale.x = 0.04
    m.color.r = COLOR_BORDER[0]
    m.color.g = COLOR_BORDER[1]
    m.color.b = COLOR_BORDER[2]
    m.color.a = alpha
    corners = [
        (cx - w / 2, cy - h / 2),
        (cx + w / 2, cy - h / 2),
        (cx + w / 2, cy + h / 2),
        (cx - w / 2, cy + h / 2),
        (cx - w / 2, cy - h / 2),
    ]
    for x, y in corners:
        m.points.append(Point(x=x, y=y, z=0.03))
    arr.markers.append(m)


def add_footprint(
    arr: MarkerArray,
    ns: str,
    mid: int,
    x: float,
    y: float,
    yaw: float,
    width: float,
    color: tuple[float, float, float, float],
) -> None:
    # Conservative Nav2 footprint: front +0.35, back -0.38, half-width 0.18.
    corners = [
        (0.35, 0.18),
        (0.35, -0.18),
        (-0.38, -0.18),
        (-0.38, 0.18),
        (0.35, 0.18),
    ]
    m = marker("map", ns, mid, Marker.LINE_STRIP)
    m.pose.position.z = 0.04
    m.scale.x = width
    m.color.r, m.color.g, m.color.b, m.color.a = color
    for px, py in corners:
        wx = x + px * math.cos(yaw) - py * math.sin(yaw)
        wy = y + px * math.sin(yaw) + py * math.cos(yaw)
        m.points.append(Point(x=wx, y=wy, z=0.04))
    arr.markers.append(m)


class IMPublisher(Node):
    def __init__(self, map_yaml: FsPath, waypoints_yaml: FsPath) -> None:
        super().__init__("im_publisher")
        self.declare_parameter("text_scale", 0.76)
        self.declare_parameter("current_id", 8)
        self.declare_parameter("next_id", 1)
        self.declare_parameter("state", "normal")

        self.text_scale = float(self.get_parameter("text_scale").value)
        self.current_id = int(self.get_parameter("current_id").value)
        self.next_id = int(self.get_parameter("next_id").value)
        self.state = str(self.get_parameter("state").value).lower()
        if self.state not in STATE_CONFIG:
            self.state = "normal"

        self.map = load_map(map_yaml)
        raw = yaml.safe_load(waypoints_yaml.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("waypoints", [])
        self.points = raw

        qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.map_pub = self.create_publisher(OccupancyGrid, "/cafe_map", qos)
        self.path_pub = self.create_publisher(Path, "/im_path", 10)
        self.wp_pub = self.create_publisher(MarkerArray, "/im_waypoints", qos)
        self.robot_pub = self.create_publisher(MarkerArray, "/im_robot", qos)
        self.status_pub = self.create_publisher(MarkerArray, "/im_status", qos)
        self.event_pub = self.create_publisher(MarkerArray, "/im_event", qos)
        self.confirm_pub = self.create_publisher(MarkerArray, "/im_confirm", qos)
        self.state_sub = self.create_subscription(
            String, "/im_state", self.on_state, 10
        )
        # The robot symbol must show the measured pose, never a waypoint.
        self.declare_parameter("odom_topic", "/robot1/odom")
        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.odom_pose: tuple[float, float, float] | None = None
        self.odom_stamp: float | None = None
        self.odom_warned = False
        self.create_subscription(Odometry, self.odom_topic, self.on_odom, 10)
        # Waypoints are taken from the collector, not from this file. The
        # "demo" source exists only for offline figures and is never used in
        # the simulation: otherwise the IM would show a plan that does not
        # exist in the system.
        self.declare_parameter("source", "ros")
        self.source = str(self.get_parameter("source").value).lower()
        self.live: dict | None = None
        if self.source == "ros":
            self.create_subscription(String, "/waypoint_state", self.on_waypoints, 10)

        self.active_current = self.current_id
        self.active_next = self.next_id
        self.publish_map()
        self.publish_all()
        # The cafe map is static: publish once with TRANSIENT_LOCAL QoS.
        # Re-publishing it every few seconds makes RViz reload the texture
        # and can look like flicker, especially with software GL.
        self.create_timer(1.0, self.publish_all)
        self.get_logger().info(
            f"IM publisher: {len(self.points)} waypoints, state={self.state}, "
            f"current={self.current_id}, next={self.next_id}, "
            f"text_scale={self.text_scale}"
        )

    def on_waypoints(self, msg: String) -> None:
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warning("bad /waypoint_state payload")
            return
        if isinstance(data, dict):
            self.live = data

    def on_odom(self, msg: Odometry) -> None:
        q = msg.pose.pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        self.odom_pose = (msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)
        self.odom_stamp = self.get_clock().now().nanoseconds * 1e-9

    def robot_pose(self) -> tuple[float, float, float]:
        if self.odom_pose is not None and self.odom_stamp is not None:
            age = self.get_clock().now().nanoseconds * 1e-9 - self.odom_stamp
            if age < 2.0:
                return self.odom_pose
        if not self.odom_warned:
            self.get_logger().warning(
                f"no fresh odom on {self.odom_topic}: "
                "robot marker falls back to the current target or origin"
            )
            self.odom_warned = True
        if self.active_current is not None:
            x, y = self.point(self.active_current)
            return x, y, 0.0
        return 0.0, 0.0, 0.0

    def on_state(self, msg: String) -> None:
        state = msg.data.strip().lower()
        if state not in STATE_CONFIG:
            self.get_logger().warning(f"unknown state: {state}")
            return
        self.state = state
        self.get_logger().info(f"state -> {state}")
        self.publish_all()

    def point(self, one_based_id: int) -> tuple[float, float]:
        for i, x, y in self.wp_items():
            if i == one_based_id:
                return x, y
        raise KeyError(f"waypoint {one_based_id} not found")
    def refresh_targets(self) -> None:
        if self.source == "demo":
            self.active_current = self.current_id
            self.active_next = self.next_id
            return
        live = self.live
        if not live or int(live.get("count", 0)) == 0 or not live.get("active"):
            self.active_current = None
            self.active_next = None
            return
        count = int(live["count"])
        cur = int(live["current"]) % count
        self.active_current = cur + 1
        self.active_next = (cur + 1) % count + 1

    def wp_items(self) -> list[tuple[int, float, float]]:
        if self.source == "demo":
            return [
                (i, float(p["x"]), float(p["y"]))
                for i, p in enumerate(self.points, start=1)
            ]
        if not self.live:
            return []
        return [
            (i, float(w["x"]), float(w["y"]))
            for i, w in enumerate(self.live.get("waypoints", []), start=1)
        ]
    def publish_map(self) -> None:
        self.map.header.stamp = self.get_clock().now().to_msg()
        self.map_pub.publish(self.map)

    def publish_all(self) -> None:
        self.refresh_targets()
        stamp = self.get_clock().now().to_msg()
        self.publish_path(stamp)
        self.publish_waypoints()
        self.publish_robot()
        self.publish_status()
        self.publish_event()
        self.publish_confirm()

    def publish_path(self, stamp) -> None:
        path = Path()
        path.header.frame_id = "map"
        path.header.stamp = stamp
        if self.active_current is not None and self.active_next is not None:
            if self.source == "demo":
                x0, y0 = self.point(self.active_current)
                x1, y1 = self.point(self.active_next)
            else:
                x0, y0, _ = self.robot_pose()
                x1, y1 = self.point(self.active_current)
            steps = 40
            yaw = math.atan2(y1 - y0, x1 - x0)
            for i in range(steps + 1):
                t = i / steps
                pose = PoseStamped()
                pose.header.frame_id = "map"
                pose.header.stamp = stamp
                pose.pose.position.x = x0 + (x1 - x0) * t
                pose.pose.position.y = y0 + (y1 - y0) * t
                pose.pose.position.z = 0.0
                pose.pose.orientation.z = math.sin(yaw / 2.0)
                pose.pose.orientation.w = math.cos(yaw / 2.0)
                path.poses.append(pose)
        self.path_pub.publish(path)
    def publish_waypoints(self) -> None:
        arr = MarkerArray()
        # Clear every possible id: the collector list can shrink or vanish.
        for i in range(1, MAX_WP + 1):
            for ns, mid, mtype in (
                ("im_waypoints", i, Marker.SPHERE),
                ("im_waypoint_labels", 100 + i, Marker.TEXT_VIEW_FACING),
            ):
                m = marker("map", ns, mid, mtype)
                m.action = Marker.DELETE
                arr.markers.append(m)
        for i, x, y in self.wp_items():
            m = marker("map", "im_waypoints", i, Marker.SPHERE)
            m.pose.position.x = x
            m.pose.position.y = y
            m.pose.position.z = 0.05
            if i == self.active_current:
                color = COLOR_CURRENT
            elif i == self.active_next:
                color = COLOR_NEXT
            else:
                color = COLOR_FUTURE
            m.scale.x = 0.45
            m.scale.y = 0.45
            m.scale.z = 0.45
            m.color.r, m.color.g, m.color.b, m.color.a = color
            arr.markers.append(m)

            accent = i in (self.active_current, self.active_next)
            scale = self.text_scale if accent else self.text_scale * 0.85
            add_text(
                arr,
                "im_waypoint_labels",
                100 + i,
                str(i),
                x + 0.35,
                y + 0.30,
                0.12,
                scale,
                COLOR_LABEL,
            )
        self.wp_pub.publish(arr)
    def publish_robot(self) -> None:
        arr = MarkerArray()
        x, y, yaw = self.robot_pose()
        add_footprint(arr, "im_robot", 0, x, y, yaw, 0.07, COLOR_CURRENT)
        arrow = marker("map", "im_robot", 1, Marker.ARROW)
        arrow.pose.position.x = x
        arrow.pose.position.y = y
        arrow.pose.position.z = 0.06
        arrow.pose.orientation.z = math.sin(yaw / 2.0)
        arrow.pose.orientation.w = math.cos(yaw / 2.0)
        arrow.scale.x = 0.55
        arrow.scale.y = 0.05
        arrow.scale.z = 0.18
        arrow.color.r, arrow.color.g, arrow.color.b, arrow.color.a = COLOR_ARROW
        arr.markers.append(arrow)
        self.robot_pub.publish(arr)

    def publish_status(self) -> None:
        arr = MarkerArray()
        cx, cy, w, h = 10.8, -8.2, 9.6, 5.0
        add_box(arr, "im_status", 0, cx, cy, w, h, COLOR_PANEL)
        add_border(arr, "im_status", 1, cx, cy, w, h)
        items = self.wp_items()
        if self.active_current is None:
            wp_line = f"WP: {len(items)} LOADED" if items else "WP: NONE"
        else:
            wp_line = f"WP: {self.active_current} -> {self.active_next}"
        lines = [
            "MODE: SUPERVISORY",
            wp_line,
            f"STATE: {self.state.upper()}",
            f"ROBOT: {STATE_CONFIG[self.state]['robot']}",
            "LINK: OK",
        ]
        for i, line in enumerate(lines):
            add_text(
                arr,
                "im_status_text",
                10 + i,
                line,
                cx,
                -6.3 - i * 0.8,
                0.08,
                self.text_scale,
                COLOR_WHITE,
            )
        self.publish_legend(arr)
        self.status_pub.publish(arr)

    def publish_legend(self, arr: MarkerArray) -> None:
        cx, cy, w, h = 10.8, 4.3, 9.6, 5.0
        add_box(arr, "im_legend", 0, cx, cy, w, h, COLOR_LEGEND)
        add_border(arr, "im_legend", 1, cx, cy, w, h)
        add_text(
            arr,
            "im_legend_text",
            2,
            "LEGEND",
            cx,
            6.25,
            0.08,
            self.text_scale * 0.75,
            COLOR_WHITE,
        )
        items = [
            ("CURRENT", COLOR_CURRENT),
            ("NEXT", COLOR_NEXT),
            ("OTHER", COLOR_FUTURE),
            ("PATH", COLOR_PATH),
            ("OBSTACLE", COLOR_OBS_FILL),
        ]
        for i, (label, color) in enumerate(items):
            y = 5.2 - i * 0.78
            add_box(arr, "im_legend_swatch", 10 + i, 7.9, y, 0.42, 0.42, color, z=0.03)
            add_text(
                arr,
                "im_legend_label",
                20 + i,
                label,
                10.6,
                y,
                0.08,
                self.text_scale * 0.8,
                COLOR_WHITE,
            )

    def publish_event(self) -> None:
        cfg = STATE_CONFIG[self.state]
        arr = MarkerArray()
        for ns, ids in (
            ("im_obstacle", tuple(range(0, 12))),
            ("im_obstacle_label", (0, 1, 2, 3)),
        ):
            for mid in ids:
                dead = marker("map", ns, mid, Marker.SPHERE)
                dead.action = Marker.DELETE
                arr.markers.append(dead)
        cx, cy, w, h = 10.8, -1.95, 9.6, 4.1
        add_box(arr, "im_event", 0, cx, cy, w, h, cfg["panel"])
        add_border(arr, "im_event", 1, cx, cy, w, h)
        lines = [
            "EVENT",
            cfg["event"],
            f"CAUSE: {cfg['cause']}",
            f"ACTION: {cfg['action']}",
            f"DEADLINE: {cfg['deadline']}",
        ]
        for i, line in enumerate(lines):
            add_text(
                arr,
                "im_event_text",
                10 + i,
                line,
                cx,
                -0.45 - i * 0.68,
                0.08,
                self.text_scale,
                COLOR_WHITE,
            )
        if cfg["obstacle"]:
            # Obstacles are drawn as their contour, never as a point: a dot has
            # zero area and cannot convey clearance for a 0.73 x 0.36 m robot.
            # Demo object is an L-shaped cart (0.90 x 0.55 m overall).
            ox, oy, oyaw = 0.60, -0.97, -0.58
            c, sn = math.cos(oyaw), math.sin(oyaw)

            def to_world(px: float, py: float) -> tuple[float, float]:
                return (ox + px * c - py * sn, oy + px * sn + py * c)

            parts = (
                (0.0, -0.1125, 0.90, 0.325),
                (-0.175, 0.1625, 0.55, 0.225),
            )
            for i, (lx, ly, w, h) in enumerate(parts):
                wx, wy = to_world(lx, ly)
                body = marker("map", "im_obstacle", i, Marker.CUBE)
                body.pose.position.x = wx
                body.pose.position.y = wy
                body.pose.position.z = 0.06
                body.pose.orientation.z = math.sin(oyaw / 2.0)
                body.pose.orientation.w = math.cos(oyaw / 2.0)
                body.scale.x = w
                body.scale.y = h
                body.scale.z = 0.02
                body.color.r = COLOR_OBS_FILL[0]
                body.color.g = COLOR_OBS_FILL[1]
                body.color.b = COLOR_OBS_FILL[2]
                body.color.a = COLOR_OBS_FILL[3]
                arr.markers.append(body)

            contour = (
                (-0.45, -0.275),
                (0.45, -0.275),
                (0.45, 0.05),
                (0.10, 0.05),
                (0.10, 0.275),
                (-0.45, 0.275),
            )
            edge = marker("map", "im_obstacle", 10, Marker.LINE_STRIP)
            edge.pose.position.z = 0.08
            edge.scale.x = 0.04
            edge.color.r = COLOR_OBS_EDGE[0]
            edge.color.g = COLOR_OBS_EDGE[1]
            edge.color.b = COLOR_OBS_EDGE[2]
            edge.color.a = COLOR_OBS_EDGE[3]
            for lx, ly in list(contour) + [contour[0]]:
                wx, wy = to_world(lx, ly)
                edge.points.append(Point(x=wx, y=wy, z=0.08))
            arr.markers.append(edge)

            add_text(
                arr,
                "im_obstacle_label",
                1,
                "OBSTACLE",
                2.55,
                -1.00,
                0.10,
                self.text_scale * 0.8,
                COLOR_OBS_FILL,
            )
        self.event_pub.publish(arr)

    def publish_confirm(self) -> None:
        cfg = STATE_CONFIG[self.state]
        active = bool(cfg["buttons"])
        arr = MarkerArray()
        buttons = [
            ("CONFIRM", 8.7, -4.85, COLOR_CONFIRM),
            ("CANCEL", 12.9, -4.85, COLOR_CANCEL),
        ]
        for i, (label, cx, cy, color) in enumerate(buttons):
            c = (color[0], color[1], color[2], color[3] if active else 0.0)
            add_box(arr, "im_confirm", i, cx, cy, 3.8, 1.5, c)
            add_border(
                arr,
                "im_confirm_border",
                10 + i,
                cx,
                cy,
                3.8,
                1.5,
                alpha=1.0 if active else 0.0,
            )
            add_text(
                arr,
                "im_confirm_text",
                20 + i,
                label,
                cx,
                cy,
                0.10,
                self.text_scale,
                (1.0, 1.0, 1.0, 1.0 if active else 0.0),
            )
        self.confirm_pub.publish(arr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map-yaml", type=FsPath, default=DEFAULT_MAP)
    parser.add_argument("--waypoints-yaml", type=FsPath, default=DEFAULT_WP)
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    node = IMPublisher(
        resolve(args.map_yaml, CONTAINER_MAP),
        resolve(args.waypoints_yaml, CONTAINER_WP),
    )
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
