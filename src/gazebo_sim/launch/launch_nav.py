"""Навигация (сервис wrs-nav): map_server + Nav2/SLAM + initial pose.

Ядро (wrs-core) должно быть уже запущено (есть odom/TF/scan).
"""
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetRemap


def generate_launch_description():
    ld = LaunchDescription()
    pkg_path = get_package_share_directory('gazebo_sim')
    with open(os.path.join(pkg_path, 'config', 'robots.yaml')) as file:
        robots = yaml.safe_load(file)['robots']

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='true'))

    slam_arg = LaunchConfiguration('slam', default='True')
    ld.add_action(DeclareLaunchArgument('slam', default_value='True'))

    remappings_initial = [
        ("/tf", "tf"), ("/tf_static", "tf_static"),
        ("/scan", "scan"), ("/odom", "odometry/filtered"),
    ]

    map_server = Node(
        package='nav2_map_server', executable='map_server', name='map_server',
        output='screen',
        parameters=[{'yaml_filename': os.path.join(pkg_path, 'maps', 'cambridge.yaml')}],
        remappings=remappings_initial)
    map_server_lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_map_server', output='screen',
        parameters=[{'use_sim_time': use_sim_time}, {'autostart': True},
                    {'node_names': ['map_server']}])
    ld.add_action(map_server)
    ld.add_action(map_server_lifecycle)

    for robot in robots:
        namespace = robot['name']
        nav2_launch_file = os.path.join(pkg_path, 'launch', 'nav2', 'bringup_launch.py')
        map_yaml_file = os.path.join(pkg_path, 'maps', 'cafe_world_map.yaml')
        params_file = os.path.join(pkg_path, 'config', 'nav2_params.yaml')
        message = f"{{header: {{frame_id: map}}, pose: {{pose: {{position: {{x: {robot['x_pose']}, y: {robot['y_pose']}, z: 0.1}}, orientation: {{x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}, }} }}"
        initial_pose_cmd = ExecuteProcess(cmd=[
            'ros2', 'topic', 'pub', '-t', '3', '--qos-reliability', 'reliable',
            f'/{namespace}/initialpose', 'geometry_msgs/PoseWithCovarianceStamped', message],
            output='screen')
        bringup_cmd = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch_file),
            launch_arguments={
                'map': map_yaml_file, 'use_namespace': 'True', 'namespace': namespace,
                'params_file': params_file, 'autostart': 'true', 'use_sim_time': 'true',
                'log_level': 'warn', 'map_server': 'True', 'slam': slam_arg,
            }.items())
        ld.add_action(GroupAction([
            SetRemap(src="/tf", dst="tf"),
            SetRemap(src="/tf_static", dst="tf_static"),
            bringup_cmd,
            initial_pose_cmd,
        ]))

    return ld
