#!/usr/bin/python3
# -*- coding: utf-8 -*-
# go1_run.launch.py - Gazebo Harmonic (ros_gz) version

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Package directories
    pkg_ros2_gazebo = get_package_share_directory("ros2_gazebo")
    pkg_go1_description = get_package_share_directory("go1_description")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # Launch configurations
    world_file_name = LaunchConfiguration("world_file_name")
    urdf_file = LaunchConfiguration("urdf_file")
    x_pos = LaunchConfiguration("x")
    y_pos = LaunchConfiguration("y")
    z_pos = LaunchConfiguration("z")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Declare launch arguments
    world_file_arg = DeclareLaunchArgument(
        "world_file_name",
        default_value="test.sdf",
        description="World file name (e.g., empty.world, train.world, etc.)",
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
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="True",
        description="Use simulation (Gazebo) time instead of system time",
    )

    # Path to xacro file
    xacro_file = PathJoinSubstitution(
        [pkg_go1_description, "xacro", urdf_file]
    )

    # Set Gazebo Harmonic resource paths
    set_gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=[
            os.path.join(pkg_go1_description, "meshes"),
            os.path.join(pkg_ros2_gazebo, "models"),
        ],
    )

    # Launch Gazebo Harmonic
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r ", world_path]
        }.items(),
    )

    # Robot state publisher (publishes robot_description)
    robot_description_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            {
                "robot_description": ParameterValue(
                    Command(
                        [
                            "xacro ",
                            xacro_file,
                        ]
                    ),
                    value_type=str
                ),
                "use_sim_time": use_sim_time,
            }
        ],
    )

    # Spawn robot in Gazebo
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "Go1",
            "-topic",
            "/robot_description",
            "-x",
            x_pos,
            "-y",
            y_pos,
            "-z",
            z_pos,
        ],
        output="screen",
    )

    # Odometry transform publisher
    odom_tf_publisher_node = Node(
        package="ros2_odometry",
        executable="nav_tf_publisher",
        name="odom_transform_publisher",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Visualize robot
    visualize_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_go1_description, "launch", "go1_visualize.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "urdf_file": urdf_file,
        }.items(),
    )

    # ROS2 control
    launch_ros2_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_go1_description, "launch", "controllers_go1.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
    )

    return LaunchDescription(
        [
            world_file_arg,
            urdf_file_arg,
            x_pos_arg,
            y_pos_arg,
            z_pos_arg,
            use_sim_time_arg,
            set_gz_resource_path,
            gz_sim,
            robot_description_node,
            spawn_robot,
            launch_ros2_control,
            visualize_robot,
            odom_tf_publisher_node,
        ]
    )
