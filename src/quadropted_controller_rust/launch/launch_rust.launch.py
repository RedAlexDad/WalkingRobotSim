"""Launch file for Gazebo simulation with Rust controller.

Delegates to gazebo_sim's launch.launch.py which runs the Rust controller
(and the Rust odometry node) by default.
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    gazebo_sim = get_package_share_directory('gazebo_sim')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_sim, 'launch', 'launch.launch.py')
            ),
        ),
    ])
