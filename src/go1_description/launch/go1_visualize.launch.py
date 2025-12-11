import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.conditions import IfCondition

import xacro


def generate_launch_description():
    # urdf_file = 'moonbotX.urdf'
    # Название пакета
    package_description = "go1_description"

    # Аргументы запуска
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_joint_state_publisher = LaunchConfiguration("use_joint_state_publisher")

    # Объявление аргументов
    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_jsp = DeclareLaunchArgument(
        "use_joint_state_publisher",
        default_value="True",
        description="Start joint_state_publisher",
    )

    declare_urdf_file = DeclareLaunchArgument(
        "urdf_file",
        default_value=os.path.join(
            get_package_share_directory(package_description), "xacro", "robot.xacro"
        ),
        description="Absolute path to robot urdf or xacro file",
    )

    # Обработка URDF через xacro
    pkg_path = os.path.join(get_package_share_directory(package_description))
    xacro_file = os.path.join(pkg_path, "xacro", "robot.xacro")
    robot_description_config = xacro.process_file(xacro_file)

    params = {
        "robot_description": robot_description_config.toxml(),
        "use_sim_time": use_sim_time,
    }

    # Узел robot_state_publisher
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher_node",
        output="screen",
        emulate_tty=True,
        parameters=[params],
    )

    # Узел joint_state_publisher
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        output="screen",
        condition=IfCondition(use_joint_state_publisher),
    )

    # Узел RViz
    rviz_config_dir = os.path.join(
        get_package_share_directory(package_description), "rviz", "go1_vis.rviz"
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz_node",
        output="screen",
        arguments=["-d", rviz_config_dir],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            declare_use_sim_time,
            declare_jsp,
            declare_urdf_file,
            joint_state_publisher_node,
            robot_state_publisher_node,
            rviz_node,
        ]
    )
