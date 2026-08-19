"""
Запуск Gazebo симуляции с Rust контроллером (quadropted_controller_rust).
Аналог gazebo_multi_nav2_cpp.launch.py, но использует Rust узлы.
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
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node, SetRemap
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    ld = LaunchDescription()

    package_name = 'gazebo_sim'
    pkg_path = get_package_share_directory(package_name)
    robots_file_path = os.path.join(pkg_path, 'config', 'robots.yaml')

    # Загрузка данных из YAML файла
    with open(robots_file_path) as file:
        yaml_data = yaml.safe_load(file)

    robots = yaml_data['robots']

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    declare_use_sim_time = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Использовать симуляционное время'
    )

    enable_rviz = LaunchConfiguration('enable_rviz', default='true')
    declare_enable_rviz = DeclareLaunchArgument(
        name='enable_rviz', default_value=enable_rviz, description='Enable rviz launch'
    )

    camera_fps = LaunchConfiguration('camera_fps', default='10')
    declare_camera_fps = DeclareLaunchArgument(
        name='camera_fps', default_value='10', description='FPS камеры для image bridge'
    )

    ld.add_action(declare_enable_rviz)
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_camera_fps)

    remappings_initial = [
        ("/tf", "tf"),
        ("/tf_static", "tf_static"),
        ("/scan", "scan"),
        ("/odom", "odometry/filtered")
    ]

    map_server = Node(package='nav2_map_server',
                      executable='map_server',
                      name='map_server',
                      output='screen',
                      parameters=[{'yaml_filename': os.path.join(pkg_path, 'maps', 'cambridge.yaml'),
                                   }, ],
                      remappings=remappings_initial)

    map_server_lifecycle = Node(package='nav2_lifecycle_manager',
                                executable='lifecycle_manager',
                                name='lifecycle_manager_map_server',
                                output='screen',
                                parameters=[{'use_sim_time': use_sim_time},
                                            {'autostart': True},
                                            {'node_names': ['map_server']}])

    bridge_params = os.path.join(pkg_path,'config','gz_bridge.yaml')
    ros_gz_bridge_clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )
    ld.add_action(ros_gz_bridge_clock)

    last_action = None

    for i, robot in enumerate(robots):
        namespace = robot['name']
        robot_name = robot['name']
        xacro_file = os.path.join(os.path.join(get_package_share_directory('go2_description')), 'xacro', 'robot.xacro')
        robot_desc = xacro.process_file(xacro_file, mappings={'robot_name': robot_name}).toxml()
        params_robot_state_publisher = {'robot_description': robot_desc, 'use_sim_time': use_sim_time}

        node_robot_state_publisher = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            namespace=namespace,
            parameters=[params_robot_state_publisher],
            remappings=remappings_initial
        )

        spawn_entity = Node(
            package='ros_gz_sim',
            executable='create',
            namespace=namespace,
            arguments=[
                '-topic', f'/{namespace}/robot_description',
                '-name', f'{namespace}_my_bot',
                '-allow_renaming', 'true',
                '-x', robot['x_pose'],
                '-y', robot['y_pose'],
                '-z', robot['z_pose'],
            ],
            output='screen'
        )

        ros_gz_bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            namespace=namespace,
            name='ros_gz_bridge',
            output='screen',
            arguments=[
                f'/{namespace}/imu_plugin/out@sensor_msgs/msg/Imu@gz.msgs.IMU',
                f'/{namespace}/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
                f'/{namespace}/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
                f'/{namespace}/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model',
                f'/{namespace}/color/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
                f'/{namespace}/color/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
                f'/{namespace}/color/image_rect@sensor_msgs/msg/Image@gz.msgs.Image',
            ]
        )
        start_gazebo_ros_image_bridge_cmd = Node(
            package='ros_gz_image',
            executable='image_bridge',
            namespace=namespace,
            arguments=['color/image_raw', 'color/image_rect'],
            output='screen',
        )

        joint_state_broadcaster = Node(
            package='controller_manager',
            executable='spawner',
            namespace=namespace,
            name='joint_state_broadcaster',
            arguments=['joint_state_broadcaster'],
            output='screen',
            remappings=remappings_initial
        )

        joint_group_controller = Node(
            package='controller_manager',
            executable='spawner',
            namespace=namespace,
            name='joint_group_controller',
            arguments=['joint_group_controller'],
            output='screen',
            remappings=remappings_initial
        )

        # ===== RUST CONTROLLER NODE =====
        controller = Node(
            package='quadropted_controller_rust',
            executable='robot_controller_node',
            name='robot_controller_rust',
            namespace=namespace,
            output='screen',
            remappings=[
                ("joint_group_controller/commands", "joint_group_controller/commands"),
                ("robot_mode", "robot_mode"),
                ("robot_velocity", "robot_velocity"),
                ("imu", "imu_plugin/out"),
            ],
        )

        initial_trot_mode = RegisterEventHandler(
            event_handler=OnProcessStart(
                target_action=controller,
                on_start=[
                    ExecuteProcess(
                        cmd=[
                            'ros2', 'topic', 'pub', '-t', '5', '--qos-reliability', 'reliable',
                            f'/{namespace}/robot_mode',
                            'quadropted_msgs/msg/RobotModeCommand',
                            "{mode: 'TROT', robot_id: 1}",
                        ],
                        output='screen'
                    )
                ]
            )
        )

        # ===== RUST ODOMETRY NODE =====
        odom = Node(
            package='quadropted_controller_rust',
            executable='odometry_node',
            name='odometry_rust',
            namespace=namespace,
            output='screen',
            remappings=[
                ("odom", "odom"),
                ("joint_group_controller/commands", "joint_group_controller/commands"),
                ("foot_contact", "foot_contact"),
                ("imu", "imu_plugin/out"),
                ("robot_velocity", "robot_velocity"),
            ],
        )

        nav2_launch_file = os.path.join(pkg_path, 'launch', 'nav2', 'bringup_launch.py')
        map_yaml_file = os.path.join(pkg_path, 'maps', 'cafe_world_map.yaml')
        params_file = os.path.join(pkg_path, 'config', 'nav2_params.yaml')

        message = f"{{header: {{frame_id: map}}, pose: {{pose: {{position: {{x: {robot['x_pose']}, y: {robot['y_pose']}, z: 0.1}}, orientation: {{x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}, }} }}"

        initial_pose_cmd = ExecuteProcess(
            cmd=[
                'ros2', 'topic', 'pub', '-t', '3', '--qos-reliability', 'reliable',
                f'/{namespace}/initialpose',
                'geometry_msgs/PoseWithCovarianceStamped', message
            ],
            output='screen'
        )

        bringup_cmd = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch_file),
            launch_arguments={
                'map': map_yaml_file,
                'use_namespace': 'True',
                'namespace': namespace,
                'params_file': params_file,
                'autostart': 'true',
                'use_sim_time': 'true',
                'log_level': 'warn',
                'map_server': 'True'
            }.items()
        )

        nav2_actions = GroupAction([
            SetRemap(src="/tf", dst="tf"),
            SetRemap(src="/tf_static", dst="tf_static"),
            bringup_cmd,
            initial_pose_cmd,
        ])

        rviz_launch_file = os.path.join(pkg_path, 'launch', 'rviz_launch.py')
        rviz_config_file = os.path.join(pkg_path, 'rviz', 'nav2_default_view.rviz')

        rviz = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(rviz_launch_file),
            launch_arguments={
                "namespace": namespace,
                "use_namespace": 'true',
                "rviz_config": rviz_config_file,
            }.items(),
            condition=IfCondition(enable_rviz)
        )

        cmd_vel_pub = Node(
            package='quadropted_controller_cpp',
            executable='cmd_vel_pub',
            namespace=namespace,
            name='cmd_vel_pub_cpp',
            output='screen',
            remappings=remappings_initial
        )

        fake_bms = ExecuteProcess(
            cmd=[
                'ros2', 'topic', 'pub', f'/{namespace}/battery_state', 'sensor_msgs/msg/BatteryState',
                "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: ''}, voltage: 24.0, percentage: 0.8, capacity: 10.0}",
                '-r', '1'
            ],
            output='log'
        )
        robot_localization_file_path = os.path.join(pkg_path, 'config', 'ekf.yaml')
        # EKF подписывается на /robot1/odom (Rust odometry node). Без ремаппинга
        # odom→odometry/filtered — в отличие от C++-схемы, где odom публиковался
        # сразу на odometry/filtered. Свой выход EKF публикует на odometry/filtered
        # по умолчанию, поэтому Nav2 продолжает работать без изменений.
        ekf_remappings = [
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
            ("/scan", "scan"),
        ]
        start_robot_localization_cmd = Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            namespace=namespace,
            output='screen',
            parameters=[robot_localization_file_path,
            {'use_sim_time': use_sim_time}],
            remappings=ekf_remappings)

        robot_control = GroupAction([
            SetRemap(src="/tf", dst="tf"),
            SetRemap(src="/tf_static", dst="tf_static"),
            joint_state_broadcaster,
            joint_group_controller,
            controller,  # <-- Rust controller node
            initial_trot_mode,
            cmd_vel_pub,
            odom,
            start_robot_localization_cmd,
            fake_bms,
        ])

        robot_group = GroupAction([
            node_robot_state_publisher,
            spawn_entity,
            ros_gz_bridge,
            start_gazebo_ros_image_bridge_cmd,
            robot_control,
            nav2_actions,
            rviz,
        ])

        if last_action is None:
            ld.add_action(robot_group)
        else:
            spawn_robot_event = RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=last_action,
                    on_exit=[robot_group]
                )
            )
            ld.add_action(spawn_robot_event)

        last_action = joint_group_controller

    return ld
