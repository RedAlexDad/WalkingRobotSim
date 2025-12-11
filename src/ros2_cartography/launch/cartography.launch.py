import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Получение путей к директориям
    cartography_dir = get_package_share_directory("ros2_cartography")

    # Пути к файлам параметров
    default_slam_params = os.path.join(cartography_dir, "params", "slam.yaml")
    default_rviz_config = os.path.join(cartography_dir, "rviz", "slam.rviz")

    # Конфигурация аргументов
    use_sim_time = LaunchConfiguration("use_sim_time")
    slam_params_file = LaunchConfiguration("slam_params_file")
    rviz_config_file = LaunchConfiguration("rviz_config_file")

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_slam_params_file_cmd = DeclareLaunchArgument(
        "slam_params_file",
        default_value=default_slam_params,
        description="Full path to the SLAM Toolbox parameter file",
    )

    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        "rviz_config_file",
        default_value=default_rviz_config,
        description="Full path to the RViz config file to use",
    )

    # Установка переменной окружения для вывода логов
    set_log_envvar = SetEnvironmentVariable("RCUTILS_LOGGING_BUFFERED_STREAM", "1")

    slam_toolbox_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            slam_params_file,
        ],
        remappings=[("scan", "/scan")],
    )

    # Узел RViz
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            set_log_envvar,
            declare_use_sim_time_cmd,
            declare_rviz_config_file_cmd,
            declare_slam_params_file_cmd,
            slam_toolbox_node,
            rviz_node,
        ]
    )
