#!/usr/bin/env python3

"""
Launch file for Rust-ROS2 bridge testing
"""

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Rust bridge node
        Node(
            package='walking_robot_rust',
            executable='rust_bridge.py',
            name='rust_bridge',
            output='screen',
            emulate_tty=True,
            parameters=[{
                'use_sim_time': True,
            }],
        ),
        
        # Test publisher node
        Node(
            package='walking_robot_rust',
            executable='rust_bridge.py',
            name='test_publisher',
            output='screen',
            emulate_tty=True,
            parameters=[{
                'use_sim_time': True,
                'mode': 'publisher_only',
            }],
        ),
    ])
