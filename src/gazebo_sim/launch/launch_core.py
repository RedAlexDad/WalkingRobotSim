"""Ядро (сервис wrs-core): мост GZ↔ROS, spawn робота, ros2_control,
Rust-контроллер (TROT/CRAWL/STAND), Rust-одометрия, EKF, cmd_vel_pub.

Симулятор (wrs-sim) должен быть уже запущен (идёт /clock). Навигация и RViz —
отдельные сервисы.
"""
import os

import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetRemap


def generate_launch_description():
    ld = LaunchDescription()
    package_name = 'gazebo_sim'
    pkg_path = get_package_share_directory(package_name)
    with open(os.path.join(pkg_path, 'config', 'robots.yaml')) as file:
        robots = yaml.safe_load(file)['robots']

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='true'))

    remappings_initial = [
        ("/tf", "tf"),
        ("/tf_static", "tf_static"),
        ("/scan", "scan"),
        ("/odom", "odometry/filtered"),
    ]

    # Мост мира: ground-truth поза, world poses, scan→points (config gz_bridge.yaml)
    bridge_params = os.path.join(pkg_path, 'config', 'gz_bridge.yaml')
    ld.add_action(Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name='world_bridge',
        arguments=['--ros-args', '-p', f'config_file:={bridge_params}'],
        output='screen',
    ))

    for robot in robots:
        namespace = robot['name']
        _add_robot(ld, pkg_path, namespace, robot, use_sim_time, remappings_initial)

    return ld


def _add_robot(ld, pkg_path, namespace, robot, use_sim_time, remappings_initial):
    xacro_file = os.path.join(get_package_share_directory('go2_description'),
                              'xacro', 'robot.xacro')
    robot_desc = xacro.process_file(xacro_file, mappings={'robot_name': namespace}).toxml()

    node_robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        output='screen', namespace=namespace,
        parameters=[{'robot_description': robot_desc, 'use_sim_time': use_sim_time}],
        remappings=remappings_initial)

    spawn_entity = Node(
        package='ros_gz_sim', executable='create', namespace=namespace,
        arguments=['-topic', f'/{namespace}/robot_description',
                   '-name', f'{namespace}_my_bot', '-allow_renaming', 'true',
                   '-x', robot['x_pose'], '-y', robot['y_pose'], '-z', robot['z_pose']],
        output='screen')

    ros_gz_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        namespace=namespace, name='ros_gz_bridge', output='screen',
        arguments=[
            f'/{namespace}/imu_plugin/out@sensor_msgs/msg/Imu@gz.msgs.IMU',
            f'/{namespace}/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            f'/{namespace}/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
            f'/{namespace}/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model',
            f'/{namespace}/color/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            f'/{namespace}/color/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            f'/{namespace}/color/image_rect@sensor_msgs/msg/Image@gz.msgs.Image',
        ])

    image_bridge = Node(
        package='ros_gz_image', executable='image_bridge', namespace=namespace,
        arguments=['color/image_raw', 'color/image_rect'], output='screen')

    joint_state_broadcaster = Node(
        package='controller_manager', executable='spawner', namespace=namespace,
        name='joint_state_broadcaster', arguments=['joint_state_broadcaster'],
        output='screen', remappings=remappings_initial)
    joint_group_controller = Node(
        package='controller_manager', executable='spawner', namespace=namespace,
        name='joint_group_controller', arguments=['joint_group_controller'],
        output='screen', remappings=remappings_initial)

    controller = Node(
        package='quadropted_controller_rust', executable='robot_controller_node',
        name='robot_controller_rust', namespace=namespace, output='screen',
        remappings=[('imu', f'/{namespace}/imu_plugin/out')])

    initial_trot_mode = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller,
            on_start=[ExecuteProcess(cmd=[
                'ros2', 'topic', 'pub', '-t', '5', '--qos-reliability', 'reliable',
                f'/{namespace}/robot_mode', 'quadropted_msgs/msg/RobotModeCommand',
                "{mode: 'TROT', robot_id: 1}"], output='screen')]))

    odom = Node(
        package='quadropted_controller_rust', executable='odometry_node',
        name='odometry_rust', namespace=namespace, output='screen',
        parameters=[{'publish_rate': 50, 'has_imu_heading': True, 'is_gazebo': True,
                     'base_frame_id': 'base_link', 'odom_frame_id': 'odom',
                     'enable_odom_tf': False, 'filter_window_size': 14,
                     'stall_window': 20, 'stall_ang_vel_threshold': 0.05,
                     'stall_exit_ang_vel_threshold': 0.1}],
        remappings=[('imu', f'/{namespace}/imu_plugin/out')])

    cmd_vel_pub = Node(
        package='quadropted_controller_cpp', executable='cmd_vel_pub',
        namespace=namespace, name='cmd_vel_pub_cpp', output='screen',
        remappings=remappings_initial)

    ekf = Node(
        package='robot_localization', executable='ekf_node',
        name='ekf_filter_node', namespace=namespace, output='screen',
        parameters=[os.path.join(pkg_path, 'config', 'ekf.yaml'),
                    {'use_sim_time': use_sim_time}],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static'), ('/scan', 'scan')])

    fake_bms = ExecuteProcess(cmd=[
        'ros2', 'topic', 'pub', f'/{namespace}/battery_state',
        'sensor_msgs/msg/BatteryState',
        "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: ''}, voltage: 24.0, "
        "percentage: 0.8, capacity: 10.0}", '-r', '1'], output='log')

    ld.add_action(GroupAction([
        SetRemap(src="/tf", dst="tf"),
        SetRemap(src="/tf_static", dst="tf_static"),
        node_robot_state_publisher,
        spawn_entity,
        ros_gz_bridge,
        image_bridge,
        joint_state_broadcaster,
        joint_group_controller,
        controller,
        initial_trot_mode,
        cmd_vel_pub,
        odom,
        ekf,
        fake_bms,
    ]))
