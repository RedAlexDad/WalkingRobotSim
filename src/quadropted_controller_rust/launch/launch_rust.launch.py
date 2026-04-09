"""Launch file for Gazebo simulation with Rust controller (placeholder).

Currently runs C++ controller. To switch to Rust controller:
1. Build the Rust node: cd src/quadropted_controller_rust && cargo build --release
2. Replace 'robot_controller_node' in this file with 'robot_controller_node' from Rust package
3. Run: ros2 launch quadropted_controller_rust launch_rust.launch.py
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    gazebo_sim = get_package_share_directory('gazebo_sim')
    quadropted_cpp = get_package_share_directory('quadropted_controller_cpp')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_sim, 'launch', 'launch_cpp.launch.py')
            ),
        ),
    ])
