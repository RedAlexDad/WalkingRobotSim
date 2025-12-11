#!/usr/bin/python3
# -*- coding: utf-8 -*-
# go2_run.launch.py

import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    package_description = "go2_description"

    # Package directories
    pkg_ros2_gazebo = get_package_share_directory("ros2_gazebo")
    pkg_gazebo_ros = get_package_share_directory("gazebo_ros")
    pkg_go2_description = get_package_share_directory("go2_description")

    # Process the URDF file
    pkg_path = os.path.join(get_package_share_directory(package_description))
    xacro_file = os.path.join(pkg_path, "xacro", "robot.xacro")
    robot_description = xacro.process_file(xacro_file, mappings={'GAZEBO': 'true', 'CLASSIC': 'true'}).toxml()
    rviz_config_dir = os.path.join(
        # get_package_share_directory(package_description), "rviz", "go2_vis.rviz"
        get_package_share_directory(package_description), "rviz", "go2_control_test.rviz"
    )

    # Launch configurations
    world_file_name = LaunchConfiguration("world_file_name")
    # urdf_file = LaunchConfiguration("urdf_file")
    # x_pos = LaunchConfiguration("x")
    # y_pos = LaunchConfiguration("y")
    z_pos = LaunchConfiguration("z")

    # install_dir = get_package_prefix("go2_description")

    # # Set Gazebo paths
    # gazebo_models_path = os.path.join(pkg_ros2_gazebo, "models")
    # os.environ["GAZEBO_MODEL_PATH"] = (
    #     f"{install_dir}/share:{gazebo_models_path}"
    #     if "GAZEBO_MODEL_PATH" not in os.environ
    #     else f"{os.environ['GAZEBO_MODEL_PATH']}:{install_dir}/share:{gazebo_models_path}"
    # )
    # os.environ["GAZEBO_PLUGIN_PATH"] = (
    #     f"{install_dir}/lib"
    #     if "GAZEBO_PLUGIN_PATH" not in os.environ
    #     else f"{os.environ['GAZEBO_PLUGIN_PATH']}:{install_dir}/lib"
    # )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        name="rviz_node",
        # parameters=[{"use_sim_time": True}],
        arguments=["-d", rviz_config_dir],
    )

    # Normalize world file name
    normalized_world_file = PathJoinSubstitution(
        [
            pkg_ros2_gazebo,
            "worlds",
            PythonExpression(
                [
                    "'",
                    world_file_name,
                    "'",
                    " if '",
                    world_file_name,
                    "'.endswith('.world') else '",
                    world_file_name,
                    ".world'",
                ]
            ),
        ]
    )

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gazebo.launch.py")
        ),
        launch_arguments={"verbose": "false", "world": normalized_world_file}.items(),
    )

    # x_pos_arg = DeclareLaunchArgument(
    #     "x", default_value="0.0", description="X coordinate for robot spawn position"
    # )
    # y_pos_arg = DeclareLaunchArgument(
    #     "y", default_value="0.0", description="Y coordinate for robot spawn position"
    # )
    z_pos_arg = DeclareLaunchArgument(
        "z", 
        default_value="0.6", 
        description="Z coordinate for robot spawn position"
    )

    # Robot spawn parameters
    robot_name = "Go2"
    # orientation = [0.0, 0.0, 0.0]  # [Roll, Pitch, Yaw]

    # Spawn robot
    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        name="spawn_entity",
        output="screen",
        arguments=[
            "-topic",
            "/robot_description",
            "-entity",
            robot_name,
            # "-x",
            # x_pos,
            # "-y",
            # y_pos,
            "-z",
            z_pos,
            # "-R",
            # str(orientation[0]),
            # "-P",
            # str(orientation[1]),
            # "-Y",
            # str(orientation[2]),
        ],
    )

    # Declare launch arguments
    world_file_arg = DeclareLaunchArgument(
        "world_file_name",
        default_value="test_latest.world",
        description="World file name (e.g., 'train' or 'train.world')",
    )
    # urdf_file_arg = DeclareLaunchArgument(
    #     "urdf_file",
    #     default_value="robot.xacro",
    #     description="URDF/XACRO file for the robot",
    # )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[
            {
                'publish_frequency': 20.0,
                'use_tf_static': True,
                'robot_description': robot_description,
                'ignore_timestamp': True
            }
        ],
    )

    # ROS2 control
    launch_ros2_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_go2_description, "launch", "controllers_go2.launch.py")
        )
    )
    
    # # Visualize robot
    # visualize_robot = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         os.path.join(pkg_go2_description, "launch", "go2_visualize.launch.py")
    #     ),
    #     launch_arguments={
    #         "use_joint_state_publisher": "False",
    #         "use_sim_time": "True",
    #         "urdf_file": urdf_file,
    #     }.items(),
    # )

    # Odometry transform publisher ???
    odom_tf_publisher_node = Node(
        package="ros2_odometry",
        executable="nav_tf_publisher",
        name="odom_transform_publisher",
        output="screen",
    )



    return LaunchDescription(
        [
            rviz_node,
            z_pos_arg,
            world_file_arg,
            gazebo,
            robot_state_publisher,
            # urdf_file_arg,
            # x_pos_arg,
            # y_pos_arg,
            spawn_robot,
            odom_tf_publisher_node,
            launch_ros2_control,
            # visualize_robot,
        ]
    )
