"""
Минимальный запуск Gazebo (gz-sim) для замеров RL/IK:
мир + Unitree Go2 + контроллеры суставов. БЕЗ Nav2/SLAM/RViz и без
камеры/лидара (только imu, joint_states, tf) — чтобы поднять RTF.

Запуск:
    ros2 launch gazebo_sim sim_minimal.launch.py world:=terrain_test.world
    ros2 launch gazebo_sim sim_minimal.launch.py gui:=true   # с окном Gazebo
"""
import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()
    pkg = get_package_share_directory('gazebo_sim')
    robot_name = 'robot1'
    namespace = robot_name

    world = LaunchConfiguration('world')
    use_sim_time = LaunchConfiguration('use_sim_time')
    policy = LaunchConfiguration('policy')
    mode = LaunchConfiguration('mode')
    vx = LaunchConfiguration('vx')
    gui = LaunchConfiguration('gui')
    ld.add_action(DeclareLaunchArgument('gui', default_value='false',
                                        description='Gazebo GUI (иначе headless)'))
    ld.add_action(DeclareLaunchArgument('world', default_value='flat.world'))
    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='true'))
    ld.add_action(DeclareLaunchArgument('policy', default_value='true',
                                        description='Запустить RL-политику (go2_policy_gz.py)'))
    ld.add_action(DeclareLaunchArgument('mode', default_value='effort',
                                        description='position | effort'))
    ld.add_action(DeclareLaunchArgument('vx', default_value='0.3'))

    world_file = PathJoinSubstitution([pkg, 'world', world])

    # ── Gazebo: headless (-s) или GUI ──
    gz_launch = os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
    gazebo_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={'gz_args': ['-r -v3 ', world_file], 'on_exit_shutdown': 'true'}.items(),
        condition=IfCondition(gui),
    )
    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={'gz_args': ['-s -r -v3 ', world_file], 'on_exit_shutdown': 'true'}.items(),
        condition=UnlessCondition(gui),
    )
    ld.add_action(gazebo_gui)
    ld.add_action(gazebo_headless)

    # ── clock (GZ→ROS) ──
    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='clock_bridge', output='screen',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
    )
    ld.add_action(clock_bridge)

    # ── робот ──
    xacro_file = os.path.join(
        get_package_share_directory('go2_description'), 'xacro', 'robot.xacro')
    robot_desc = xacro.process_file(xacro_file, mappings={'robot_name': robot_name}).toxml()
    rsp = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        namespace=namespace, output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': use_sim_time}],
    )
    spawn = Node(
        package='ros_gz_sim', executable='create', namespace=namespace, output='screen',
        arguments=['-topic', f'/{namespace}/robot_description',
                   '-name', f'{namespace}_my_bot', '-allow_renaming', 'false',
                   '-z', '0.30'],
    )

    # ── мосты только для нужных топиков (без камеры/лидара) ──
    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        namespace=namespace, name='ros_gz_bridge', output='screen',
        arguments=[
            f'/{namespace}/imu_plugin/out@sensor_msgs/msg/Imu@gz.msgs.IMU',
            f'/{namespace}/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model',
            f'/{namespace}/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
            f'/model/{namespace}_my_bot/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
        ],
    )

    # ── контроллеры ──
    jsb = Node(package='controller_manager', executable='spawner',
               namespace=namespace, name='joint_state_broadcaster',
               arguments=['joint_state_broadcaster'], output='screen')
    jgec = Node(package='controller_manager', executable='spawner',
                namespace=namespace, name='joint_group_effort_controller',
                arguments=['joint_group_effort_controller'], output='screen')

    # ── RL-узел (стартует вместе со спавном, держит стойку с самого начала) ──
    policy_script = os.path.join(pkg, 'scripts', 'go2_policy_gz.py')
    rl_node = ExecuteProcess(
        condition=IfCondition(policy),
        cmd=['python3', policy_script, '--ros-args',
             '-p', 'namespace:=robot1',
             '-p', 'use_sim_time:=true',
             '-p', ['control_mode:=', mode],
             '-p', ['vx:=', vx],
             '-p', 'odom_topic:=/model/robot1_my_bot/odometry'],
        output='screen')

    ld.add_action(rsp)
    # Дать gz sim подняться, затем спавн робота, контроллеры и RL-узел.
    delayed = TimerAction(period=6.0, actions=[spawn, bridge, jsb, jgec, rl_node])
    ld.add_action(delayed)
    return ld
