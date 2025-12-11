#!/usr/bin/python3
# go2_run_harmonic.launch.py

import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # Пути к пакетам
    pkg_ros2_gazebo = get_package_share_directory("ros2_gazebo")
    pkg_go2_description = get_package_share_directory("go2_description")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # Аргументы запуска
    world_arg = DeclareLaunchArgument(
        "world_file_name",
        default_value="test.sdf",
        description="World file name (e.g., empty.world, train.world, etc.)",
    )
    urdf_file_arg = DeclareLaunchArgument(
        "urdf_file", default_value="robot.xacro", description="URDF/XACRO file"
    )
    x_arg = DeclareLaunchArgument("x", default_value="0.0")
    y_arg = DeclareLaunchArgument("y", default_value="0.0")
    z_arg = DeclareLaunchArgument("z", default_value="0.6")

    # Путь к world SDF
    world_path = PathJoinSubstitution(
        [pkg_ros2_gazebo, "worlds", LaunchConfiguration("world_file_name")]
    )

    # Путь к xacro файлу робота
    xacro_file = PathJoinSubstitution(
        [pkg_go2_description, "xacro", LaunchConfiguration("urdf_file")]
    )

    # Установка путей для ресурсов (модели, плагины)
    set_gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=[
            os.path.join(pkg_go2_description, "meshes"),
            os.path.join(pkg_go2_description, "dae"),
            os.path.join(pkg_ros2_gazebo, "models"),
        ],
    )

    # Запуск Gazebo Harmonic (server + GUI)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": ["-r ", world_path]
        }.items(),
    )

    # Публикация robot_description (конвертирует xacro в URDF)
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
                "use_sim_time": True,
            }
        ],
    )

    # Спавн робота из /robot_description
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            "Go2",
            "-topic",
            "/robot_description",
            "-x",
            LaunchConfiguration("x"),
            "-y",
            LaunchConfiguration("y"),
            "-z",
            LaunchConfiguration("z"),
        ],
        output="screen",
    )

    # Загрузка контроллеров ros2_control
    launch_ros2_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_go2_description, "launch", "controllers_go2.launch.py")
        ),
        launch_arguments={
            "use_sim_time": "True",
        }.items(),
    )

    # Визуализация (RViz + joint_state_publisher)
    visualize_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_go2_description, "launch", "go2_visualize.launch.py")
        ),
        launch_arguments={
            "use_sim_time": "True",
            "urdf_file": LaunchConfiguration("urdf_file"),
        }.items(),
    )

    # Odometry TF
    odom_tf_publisher_node = Node(
        package="ros2_odometry",
        executable="nav_tf_publisher",
        name="odom_transform_publisher",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription(
        [
            world_arg,
            urdf_file_arg,
            x_arg,
            y_arg,
            z_arg,
            set_gz_resource_path,
            gz_sim,
            robot_description_node,
            spawn_robot,
            launch_ros2_control,
            visualize_robot,
            odom_tf_publisher_node,
        ]
    )
