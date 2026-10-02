"""Симулятор (сервис wrs-sim): Gazebo Sim + мир + мост /clock.

Только физика и мир. Робота спавнит ядро (wrs-core) через ros_gz_sim create.
Healthcheck сервиса: топик /clock.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_path = get_package_share_directory('gazebo_sim')

    ld = LaunchDescription()
    world = LaunchConfiguration('world', default='cafe.world')
    ld.add_action(DeclareLaunchArgument(
        'world', default_value='cafe.world',
        description='Файл мира в gazebo_sim/world'))
    world_file = PathJoinSubstitution([pkg_path, 'world', world])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-s -r -v4 ', world_file],
                          'on_exit_shutdown': 'true'}.items())
    ld.add_action(gazebo)

    # Проброс /clock: ROS-время для всех сервисов (healthcheck + use_sim_time).
    # ВАЖНО: только GZ->ROS ('['), иначе мост создаёт gz-публишера на /clock,
    # и gz-sim перестаёт публиковать глобальный /clock
    # (SimulationRunner: "Found additional publishers on /clock").
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )
    ld.add_action(clock_bridge)

    return ld
