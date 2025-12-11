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


def generate_launch_description():
    # Package directories
    pkg_ros2_gazebo = get_package_share_directory("ros2_gazebo")
    pkg_gazebo_ros = get_package_share_directory("gazebo_ros")
    pkg_go2_description = get_package_share_directory("go2_description")
    install_dir = get_package_prefix("go2_description")

    # Set Gazebo paths
    gazebo_models_path = os.path.join(pkg_ros2_gazebo, "models")
    os.environ["GAZEBO_MODEL_PATH"] = (
        f"{install_dir}/share:{gazebo_models_path}"
        if "GAZEBO_MODEL_PATH" not in os.environ
        else f"{os.environ['GAZEBO_MODEL_PATH']}:{install_dir}/share:{gazebo_models_path}"
    )
    os.environ["GAZEBO_PLUGIN_PATH"] = (
        f"{install_dir}/lib"
        if "GAZEBO_PLUGIN_PATH" not in os.environ
        else f"{os.environ['GAZEBO_PLUGIN_PATH']}:{install_dir}/lib"
    )

    # Launch configurations
    world_file_name = LaunchConfiguration("world_file_name")
    urdf_file = LaunchConfiguration("urdf_file")
    x_pos = LaunchConfiguration("x")
    y_pos = LaunchConfiguration("y")
    z_pos = LaunchConfiguration("z")

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

    # Declare launch arguments
    world_file_arg = DeclareLaunchArgument(
        "world_file_name",
        default_value="test_latest.world",
        description="World file name (e.g., 'train' or 'train.world')",
    )
    urdf_file_arg = DeclareLaunchArgument(
        "urdf_file",
        default_value="robot.xacro",
        description="URDF/XACRO file for the robot",
    )
    x_pos_arg = DeclareLaunchArgument(
        "x", default_value="0.0", description="X coordinate for robot spawn position"
    )
    y_pos_arg = DeclareLaunchArgument(
        "y", default_value="0.0", description="Y coordinate for robot spawn position"
    )
    z_pos_arg = DeclareLaunchArgument(
        "z", default_value="0.6", description="Z coordinate for robot spawn position"
    )

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gazebo.launch.py")
        ),
        launch_arguments={"verbose": "true", "world": normalized_world_file}.items(),
    )

    # Robot spawn parameters
    robot_name = "Go2"
    orientation = [0.0, 0.0, 0.0]  # [Roll, Pitch, Yaw]

    # Spawn robot
    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        name="spawn_entity",
        output="screen",
        arguments=[
            "-entity",
            robot_name,
            "-x",
            x_pos,
            "-y",
            y_pos,
            "-z",
            z_pos,
            "-R",
            str(orientation[0]),
            "-P",
            str(orientation[1]),
            "-Y",
            str(orientation[2]),
            "-topic",
            "/robot_description",
        ],
    )

    # Odometry transform publisher
    odom_tf_publisher_node = Node(
        package="ros2_odometry",
        executable="nav_tf_publisher",
        name="odom_transform_publisher",
        output="screen",
    )

    # Visualize robot
    visualize_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_go2_description, "launch", "go2_visualize.launch.py")
        ),
        launch_arguments={
            "use_joint_state_publisher": "False",
            "use_sim_time": "True",
            "urdf_file": urdf_file,
        }.items(),
    )

    # ROS2 control
    launch_ros2_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_go2_description, "launch", "controllers_go2.launch.py")
        )
    )

    return LaunchDescription(
        [
            world_file_arg,
            urdf_file_arg,
            x_pos_arg,
            y_pos_arg,
            z_pos_arg,
            gazebo,
            spawn_robot,
            launch_ros2_control,
            visualize_robot,
            odom_tf_publisher_node,
        ]
    )
