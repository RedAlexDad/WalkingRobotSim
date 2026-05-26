#!/usr/bin/env python3
import numpy as np
import rclpy
from elevation_mapping_cupy.gridmap_utils import decode_multiarray_to_rows_cols
from grid_map_msgs.msg import GridMap
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node


class ElevationToCostmapNode(Node):
    def __init__(self):
        super().__init__("elevation_to_costmap_node")

        self.declare_parameter(
            "elevation_map_topic", "/elevation_mapping_node/elevation_map"
        )
        self.declare_parameter("costmap_topic", "/elevation_costmap")
        self.declare_parameter("cost_layer_name", "cost")
        self.declare_parameter("free_threshold", 0.3)
        self.declare_parameter("occupied_threshold", 0.5)

        sub_topic = self.get_parameter("elevation_map_topic").value
        pub_topic = self.get_parameter("costmap_topic").value
        self._layer_name = self.get_parameter("cost_layer_name").value
        self._free_thresh = float(self.get_parameter("free_threshold").value)
        self._occ_thresh = float(self.get_parameter("occupied_threshold").value)

        self._sub = self.create_subscription(GridMap, sub_topic, self._cb, 10)
        self._pub = self.create_publisher(OccupancyGrid, pub_topic, 10)

        self.get_logger().info(
            f"Bridge: {sub_topic}:{self._layer_name} -> {pub_topic} "
            f"(free<={self._free_thresh}, occ>={self._occ_thresh})"
        )

    def _cb(self, msg: GridMap) -> None:
        try:
            idx = msg.layers.index(self._layer_name)
        except ValueError:
            return

        cost = decode_multiarray_to_rows_cols(self._layer_name, msg.data[idx])
        rows, cols = cost.shape

        occ = np.full((rows, cols), -1, dtype=np.int8)
        valid = ~np.isnan(cost)

        occ[valid & (cost <= self._free_thresh)] = 0
        occ[valid & (cost >= self._occ_thresh)] = 100

        interp = valid & (cost > self._free_thresh) & (cost < self._occ_thresh)
        if interp.any():
            occ[interp] = (
                (cost[interp] - self._free_thresh)
                / (self._occ_thresh - self._free_thresh)
                * 100
            ).astype(np.int8)
            occ[interp] = np.clip(occ[interp], 1, 99)

        out = OccupancyGrid()
        out.header = msg.header
        out.header.stamp = self.get_clock().now().to_msg()
        out.info.resolution = msg.info.resolution
        out.info.width = cols
        out.info.height = rows
        out.info.origin = msg.info.pose
        out.info.origin.position.z = 0.0
        out.info.origin.orientation.x = 0.0
        out.info.origin.orientation.y = 0.0
        out.info.origin.orientation.z = 0.0
        out.info.origin.orientation.w = 1.0
        out.data = occ.flatten(order="C").tolist()

        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ElevationToCostmapNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
