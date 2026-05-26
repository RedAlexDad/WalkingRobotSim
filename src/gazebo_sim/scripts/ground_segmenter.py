#!/usr/bin/env python3
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import PointCloud2, PointField


def _read_xyz32(msg):
    offsets = {f.name: f.offset for f in msg.fields}
    n = msg.width * msg.height
    raw = np.frombuffer(msg.data, dtype=np.uint8).reshape(n, msg.point_step)
    x = raw[:, offsets["x"] : offsets["x"] + 4].copy().ravel().view(np.float32)
    y = raw[:, offsets["y"] : offsets["y"] + 4].copy().ravel().view(np.float32)
    z = raw[:, offsets["z"] : offsets["z"] + 4].copy().ravel().view(np.float32)
    xyz = np.column_stack([x, y, z])
    mask = np.isfinite(xyz).all(axis=1)
    return xyz[mask]


def _make_cloud(header, xyz):
    msg = PointCloud2()
    msg.header = header
    msg.height = 1
    msg.width = len(xyz)
    msg.fields = [
        PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
    ]
    msg.is_bigendian = False
    msg.point_step = 12
    msg.row_step = msg.point_step * msg.width
    msg.is_dense = False
    msg.data = xyz.astype(np.float32).tobytes()
    return msg


class GroundSegmenter(Node):
    def __init__(self):
        super().__init__("ground_segmenter")

        self.declare_parameter("input_topic", "/robot1/scan/points")
        self.declare_parameter("ground_topic", "/ground_cloud")
        self.declare_parameter("obstacle_topic", "/obstacle_cloud")
        self.declare_parameter("num_lpr", 20)
        self.declare_parameter("num_iterations", 3)
        self.declare_parameter("dist_threshold", 0.15)
        self.declare_parameter("height_margin", 0.05)

        input_topic = self.get_parameter("input_topic").value
        ground_topic = self.get_parameter("ground_topic").value
        obstacle_topic = self.get_parameter("obstacle_topic").value
        self._num_lpr = self.get_parameter("num_lpr").value
        self._num_iter = self.get_parameter("num_iterations").value
        self._dist_thresh = self.get_parameter("dist_threshold").value
        self._height_margin = self.get_parameter("height_margin").value

        self._sub = self.create_subscription(
            PointCloud2,
            input_topic,
            self._callback,
            QoSPresetProfiles.SENSOR_DATA.value,
        )

        self._pub_ground = self.create_publisher(PointCloud2, ground_topic, 10)
        self._pub_obstacle = self.create_publisher(PointCloud2, obstacle_topic, 10)

        self.get_logger().info(
            f"Ground segmenter ready: {input_topic} -> {ground_topic}, {obstacle_topic}"
        )

    def _estimate_plane(self, points):
        center = points.mean(axis=0)
        try:
            _, _, Vt = np.linalg.svd(points - center, full_matrices=False)
        except np.linalg.LinAlgError:
            return None, None
        normal = Vt[2, :]
        return normal, center

    def _point_distance(self, points, normal, center):
        return np.abs(np.dot(points - center, normal))

    def _callback(self, msg):
        try:
            points = _read_xyz32(msg)
        except Exception:
            self.get_logger().warn("Failed to parse PointCloud2", throttle_duration=5.0)
            return

        if len(points) < self._num_lpr:
            return

        idx = np.argsort(points[:, 2])
        seed = points[idx[: self._num_lpr]]

        ground_mask = None
        for _ in range(self._num_iter):
            if len(seed) < 3:
                break
            normal, center = self._estimate_plane(seed)
            if normal is None:
                break
            dist = self._point_distance(points, normal, center)
            ground_mask = dist < self._dist_thresh
            seed = points[ground_mask]

        if ground_mask is not None and ground_mask.any():
            mean_z = points[ground_mask, 2].mean()
            too_high = (points[:, 2] - mean_z) > self._height_margin
            ground_mask = ground_mask & ~too_high
            ground_pts = points[ground_mask]
            obstacle_pts = points[~ground_mask]

            if len(ground_pts):
                self._pub_ground.publish(_make_cloud(msg.header, ground_pts))
            if len(obstacle_pts):
                self._pub_obstacle.publish(_make_cloud(msg.header, obstacle_pts))


def main(args=None):
    rclpy.init(args=args)
    node = GroundSegmenter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
