from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="elevation_mapping_cupy",
                executable="elevation_to_costmap_node.py",
                name="elevation_to_costmap_node",
                output="screen",
            )
        ]
    )
