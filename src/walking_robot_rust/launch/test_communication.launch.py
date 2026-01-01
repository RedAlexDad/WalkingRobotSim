#!/usr/bin/env python3

"""
Launch file for testing Rust ROS2 communication
"""

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Rust sender node
        Node(
            package='walking_robot_rust',
            executable='sender',
            name='rust_sender',
            output='screen',
            emulate_tty=True,
        ),
        
        # Rust receiver node
        Node(
            package='walking_robot_rust',
            executable='receiver',
            name='rust_receiver',
            output='screen',
            emulate_tty=True,
        ),
        
        # Rust service server
        Node(
            package='walking_robot_rust',
            executable='service_server',
            name='rust_service_server',
            output='screen',
            emulate_tty=True,
        ),
        
        # Rust service client
        Node(
            package='walking_robot_rust',
            executable='service_client',
            name='rust_service_client',
            output='screen',
            emulate_tty=True,
        ),
        
        # Rust action server
        Node(
            package='walking_robot_rust',
            executable='action_server',
            name='rust_action_server',
            output='screen',
            emulate_tty=True,
        ),
        
        # Rust action client
        Node(
            package='walking_robot_rust',
            executable='action_client',
            name='rust_action_client',
            output='screen',
            emulate_tty=True,
        ),
    ])
