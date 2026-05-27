#!/usr/bin/env python3
import numpy as np
import rclpy
from elevation_mapping_cupy.gridmap_utils import decode_multiarray_to_rows_cols
from grid_map_msgs.msg import GridMap
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy


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
        self.declare_parameter("invert_cost", True)

        sub_topic = self.get_parameter("elevation_map_topic").value
        pub_topic = self.get_parameter("costmap_topic").value
        self._layer_name = self.get_parameter("cost_layer_name").value
        self._free_thresh = float(self.get_parameter("free_threshold").value)
        self._occ_thresh = float(self.get_parameter("occupied_threshold").value)
        self._invert = bool(self.get_parameter("invert_cost").value)

        self._msg_count = 0
        self._warn_timer = self.create_timer(5.0, self._warn_if_no_data)

        sub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._sub = self.create_subscription(GridMap, sub_topic, self._cb, sub_qos)
        latched_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._pub = self.create_publisher(OccupancyGrid, pub_topic, latched_qos)

        mode = "inverted" if self._invert else "direct"
        self.get_logger().info(
            f"Bridge: {sub_topic}:{self._layer_name} -> {pub_topic} "
            f"(free<={self._free_thresh}, occ>={self._occ_thresh}, mode={mode})"
        )

    def _warn_if_no_data(self) -> None:
        if self._msg_count == 0:
            self.get_logger().warn(
                "No elevation map messages received yet. "
                "Check that elevation_mapping_node is publishing."
            )

    def _cb(self, msg: GridMap) -> None:
        if self._msg_count == 0:
            self.get_logger().info(
                f"First elevation map received: frame={msg.header.frame_id}, "
                f"layers={msg.layers}, shape={msg.data[0].layout.dim}"
            )
        self._msg_count += 1

        try:
            idx = msg.layers.index(self._layer_name)
        except ValueError:
            return

        cost = decode_multiarray_to_rows_cols(self._layer_name, msg.data[idx])
        rows, cols = cost.shape

        occ = np.full((rows, cols), -1, dtype=np.int8)
        valid = ~np.isnan(cost)

        if self._invert:
            lo = 1.0 - self._occ_thresh
            hi = 1.0 - self._free_thresh
            occ[valid & (cost >= hi)] = 0
            occ[valid & (cost <= lo)] = 100
            interp = valid & (cost > lo) & (cost < hi)
            if interp.any():
                occ[interp] = (
                    (1.0 - cost[interp] - self._free_thresh)
                    / (self._occ_thresh - self._free_thresh)
                    * 100
                ).astype(np.int8)
                occ[interp] = np.clip(occ[interp], 1, 99)
        else:
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
