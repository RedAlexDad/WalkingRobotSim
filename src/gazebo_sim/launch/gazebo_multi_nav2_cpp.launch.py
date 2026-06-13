import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    pkg_path = get_package_share_directory("gazebo_sim")

    with open(os.path.join(pkg_path, "config", "robots.yaml")) as f:
        robots = yaml.safe_load(f)["robots"]

    ld.add_action(DeclareLaunchArgument("use_sim_time", default_value="true"))
    ld.add_action(DeclareLaunchArgument("enable_rviz", default_value="true"))
    ld.add_action(DeclareLaunchArgument("camera_fps", default_value="30"))
    ld.add_action(DeclareLaunchArgument("use_elevation", default_value="false"))

    use_sim_time = LaunchConfiguration("use_sim_time")

    ld.add_action(
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "--ros-args",
                "-p",
                f"config_file:={os.path.join(pkg_path, 'config', 'gz_bridge.yaml')}",
            ],
        )
    )

    per_robot_file = os.path.join(pkg_path, "launch", "per_robot_bringup.launch.py")

    for robot in robots:
        ld.add_action(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(per_robot_file),
                launch_arguments={
                    "namespace": robot["name"],
                    "x_pose": robot["x_pose"],
                    "y_pose": robot["y_pose"],
                    "z_pose": robot["z_pose"],
                    "camera_fps": LaunchConfiguration("camera_fps"),
                    "use_sim_time": use_sim_time,
                    "use_elevation": LaunchConfiguration("use_elevation"),
                    "enable_rviz": LaunchConfiguration("enable_rviz"),
                }.items(),
            )
        )

    return ld
