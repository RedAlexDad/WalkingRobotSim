#!/usr/bin/env python3
import math
import struct

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, PointCloud2, PointField


class LaserToPointCloud(Node):
    def __init__(self):
        super().__init__("laser_to_pointcloud")

        self.declare_parameter("input_scan", "/robot1/scan")
        self.declare_parameter("output_cloud", "/robot1/scan/points")
        self.declare_parameter("vertical_samples", 16)
        self.declare_parameter("vertical_angle_min", -0.26)
        self.declare_parameter("vertical_angle_max", 0.26)
        self.declare_parameter("range_max", 12.0)

        self.v_samples = self.get_parameter("vertical_samples").value
        self.v_angle_min = self.get_parameter("vertical_angle_min").value
        self.v_angle_max = self.get_parameter("vertical_angle_max").value
        self.range_max = self.get_parameter("range_max").value

        self.sub = self.create_subscription(LaserScan, self.get_parameter("input_scan").value, self.scan_callback, 10)

        self.pub = self.create_publisher(PointCloud2, self.get_parameter("output_cloud").value, 10)

        self._scan_count = 0
        self.get_logger().info(
            f"LaserScan -> PointCloud2 converter started: "
            f"{self.get_parameter('input_scan').value} -> "
            f"{self.get_parameter('output_cloud').value}, "
            f"v_samples={self.v_samples}"
        )

    def scan_callback(self, msg):
        self._scan_count += 1
        if self._scan_count == 1:
            self.get_logger().info(
                f"First scan received: {len(msg.ranges)} ranges, "
                f"angle=[{msg.angle_min:.2f},{msg.angle_max:.2f}], "
                f"range=[{msg.range_min:.2f},{msg.range_max:.2f}]"
            )
        h_samples = len(msg.ranges) // self.v_samples

        points = []
        for vi in range(self.v_samples):
            v_angle = self.v_angle_min + vi * (self.v_angle_max - self.v_angle_min) / max(self.v_samples - 1, 1)
            for hi in range(h_samples):
                idx = vi * h_samples + hi
                if idx >= len(msg.ranges):
                    break
                r = msg.ranges[idx]
                if r < msg.range_min or r > self.range_max:
                    continue
                h_angle = msg.angle_min + hi * msg.angle_increment
                x = r * math.cos(v_angle) * math.cos(h_angle)
                y = r * math.cos(v_angle) * math.sin(h_angle)
                z = r * math.sin(v_angle)
                points.append([x, y, z])

        if not points:
            return

        cloud = PointCloud2()
        cloud.header = msg.header
        cloud.header.frame_id = "laser_frame"
        cloud.height = 1
        cloud.width = len(points)
        cloud.fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        cloud.point_step = 12
        cloud.row_step = cloud.point_step * cloud.width
        cloud.is_bigendian = False
        cloud.is_dense = True

        buf = struct.pack(f"<{3 * len(points)}f", *np.array(points).flatten())
        cloud.data = buf

        self.pub.publish(cloud)


def main(args=None):
    rclpy.init(args=args)
    node = LaserToPointCloud()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
