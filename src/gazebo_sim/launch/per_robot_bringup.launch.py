import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node, SetRemap


def _robot_state_publisher(
    context, xacro_file, robot_name, camera_fps, use_sim_time, namespace, remappings
):
    fps = camera_fps.perform(context)
    mappings = {"robot_name": robot_name, "camera_fps": fps}
    robot_desc = xacro.process_file(xacro_file, mappings=mappings).toxml()
    params = {"robot_description": robot_desc, "use_sim_time": use_sim_time}
    return [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            namespace=namespace,
            parameters=[params],
            remappings=remappings,
        )
    ]


def generate_launch_description():
    pkg_path = get_package_share_directory("gazebo_sim")

    args = {
        "namespace": "robot1",
        "x_pose": "0.0",
        "y_pose": "0.0",
        "z_pose": "0.0",
        "camera_fps": "30",
        "use_sim_time": "true",
        "use_elevation": "false",
        "enable_rviz": "true",
    }

    ld = LaunchDescription(
        [DeclareLaunchArgument(k, default_value=v) for k, v in args.items()]
    )

    ns = LaunchConfiguration("namespace")

    remaps = [
        ("/tf", "tf"),
        ("/tf_static", "tf_static"),
        ("/scan", "scan"),
        ("/odom", "odometry/filtered"),
    ]

    state_publisher = OpaqueFunction(
        function=_robot_state_publisher,
        args=[
            os.path.join(
                get_package_share_directory("go2_description"), "xacro", "robot.xacro"
            ),
            ns,
            LaunchConfiguration("camera_fps"),
            LaunchConfiguration("use_sim_time"),
            ns,
            remaps,
        ],
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=ns,
        arguments=[
            "-topic",
            PythonExpression(["'/' + '", ns, "' + '/robot_description'"]),
            "-name",
            PythonExpression([ns, "' + '_my_bot'"]),
            "-allow_renaming",
            "true",
            "-x",
            LaunchConfiguration("x_pose"),
            "-y",
            LaunchConfiguration("y_pose"),
            "-z",
            LaunchConfiguration("z_pose"),
        ],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=ns,
        name="ros_gz_bridge",
        output="screen",
        arguments=[
            PythonExpression(
                ["'/' + '", ns, "' + '/imu_plugin/out@sensor_msgs/msg/Imu@gz.msgs.IMU'"]
            ),
            PythonExpression(
                [
                    "'/' + '",
                    ns,
                    "' + '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan'",
                ]
            ),
            PythonExpression(
                ["'/' + '", ns, "' + '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V'"]
            ),
            PythonExpression(
                [
                    "'/' + '",
                    ns,
                    "' + '/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model'",
                ]
            ),
            PythonExpression(
                [
                    "'/' + '",
                    ns,
                    "' + '/color/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo'",
                ]
            ),
            PythonExpression(
                [
                    "'/' + '",
                    ns,
                    "' + '/color/image_raw@sensor_msgs/msg/Image@gz.msgs.Image'",
                ]
            ),
            PythonExpression(
                [
                    "'/' + '",
                    ns,
                    "' + '/color/image_rect@sensor_msgs/msg/Image@gz.msgs.Image'",
                ]
            ),
        ],
    )

    image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        namespace=ns,
        arguments=["color/image_raw", "color/image_rect"],
        output="screen",
    )

    jnt_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        namespace=ns,
        name="joint_state_broadcaster",
        arguments=["joint_state_broadcaster"],
        output="screen",
        remappings=remaps,
    )

    jnt_group_ctrl = Node(
        package="controller_manager",
        executable="spawner",
        namespace=ns,
        name="joint_group_controller",
        arguments=["joint_group_controller"],
        output="screen",
        remappings=remaps,
    )

    controller = Node(
        package="quadropted_controller_cpp",
        executable="robot_controller_node",
        name="robot_controller_cpp",
        namespace=ns,
        output="screen",
        remappings=remaps,
    )

    odom = Node(
        package="quadropted_controller_cpp",
        executable="odometry_node",
        name="odometry_cpp",
        namespace=ns,
        output="screen",
        parameters=[
            {
                "verbose": False,
                "publish_rate": 50,
                "open_loop": False,
                "has_imu_heading": True,
                "is_gazebo": True,
                "imu_topic": PythonExpression(["'/' + '", ns, "' + '/imu_plugin/out'"]),
                "base_frame_id": "base_link",
                "odom_frame_id": "odom",
                "clock_topic": "/clock",
                "enable_odom_tf": False,
            }
        ],
        remappings=remaps,
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, "launch", "nav2", "bringup_launch.py")
        ),
        launch_arguments={
            "map": os.path.join(pkg_path, "maps", "cafe_world_map.yaml"),
            "use_namespace": "True",
            "namespace": ns,
            "use_elevation": LaunchConfiguration("use_elevation"),
            "autostart": "true",
            "use_sim_time": "true",
            "log_level": "warn",
            "map_server": "True",
        }.items(),
    )

    initial_pose = ExecuteProcess(
        cmd=[
            "ros2",
            "topic",
            "pub",
            "-t",
            "3",
            "--qos-reliability",
            "reliable",
            PythonExpression(["'/' + '", ns, "' + '/initialpose'"]),
            "geometry_msgs/PoseWithCovarianceStamped",
            PythonExpression(
                [
                    "'{header: {frame_id: map}, pose: {pose: {position: {x: '",
                    LaunchConfiguration("x_pose"),
                    "', y: '",
                    LaunchConfiguration("y_pose"),
                    "', z: 0.1}}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}} }'",
                ]
            ),
        ],
        output="screen",
    )

    nav2_group = GroupAction(
        [
            SetRemap(src="/tf", dst="tf"),
            SetRemap(src="/tf_static", dst="tf_static"),
            nav2,
            initial_pose,
        ]
    )

    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, "launch", "rviz_launch.py")
        ),
        launch_arguments={
            "namespace": ns,
            "use_namespace": "true",
            "rviz_config": os.path.join(
                pkg_path, "rviz", "multi_nav2_default_view.rviz"
            ),
        }.items(),
    )

    cmd_vel = Node(
        package="quadropted_controller_cpp",
        executable="cmd_vel_pub",
        namespace=ns,
        name="cmd_vel_pub_cpp",
        output="screen",
        remappings=remaps,
    )

    fake_bms = ExecuteProcess(
        cmd=[
            "ros2",
            "topic",
            "pub",
            PythonExpression(["'/' + '", ns, "' + '/battery_state'"]),
            "sensor_msgs/msg/BatteryState",
            "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: ''}, voltage: 24.0, percentage: 0.8, capacity: 10.0}",
            "-r",
            "1",
        ],
        output="log",
    )

    ekf = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        namespace=ns,
        output="screen",
        parameters=[
            os.path.join(pkg_path, "config", "ekf.yaml"),
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
        remappings=remaps,
    )

    ctrl_group = GroupAction(
        [
            SetRemap(src="/tf", dst="tf"),
            SetRemap(src="/tf_static", dst="tf_static"),
            jnt_broadcaster,
            jnt_group_ctrl,
            controller,
            cmd_vel,
            odom,
            ekf,
            fake_bms,
        ]
    )

    ground_truth = Node(
        package="gazebo_sim",
        executable="ground_truth_publisher.py",
        namespace=ns,
        name="ground_truth_publisher",
        output="screen",
        parameters=[
            {
                "publish_rate": 50,
                "base_frame_id": "base_link_gt",
                "odom_frame_id": "gt_odom",
                "pose_topic": "pose_ground_truth",
                "odom_topic": "ground_truth/odom",
            }
        ],
        remappings=remaps,
    )

    waypoints = Node(
        package="gazebo_sim",
        executable="waypoint_collector.py",
        namespace=ns,
        name="waypoint_collector",
        output="screen",
        remappings=remaps,
    )

    robot_group = GroupAction(
        [
            state_publisher,
            spawn,
            bridge,
            image_bridge,
            ctrl_group,
            nav2_group,
            waypoints,
            ground_truth,
            rviz,
        ]
    )

    ld.add_action(robot_group)
    return ld
