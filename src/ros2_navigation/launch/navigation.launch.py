from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration
import os


def generate_launch_description():
    # Получение путей к директориям
    nav2_bringup_dir = get_package_share_directory("nav2_bringup")
    pkg_share = get_package_share_directory("ros2_navigation")

    # Пути к файлам параметров
    default_map_path = os.path.join(pkg_share, "maps", "map_001", "map.yaml")
    default_nav2_params = os.path.join(pkg_share, "params", "navigation.yaml")
    default_rviz_config = os.path.join(pkg_share, "rviz", "navigation.rviz")

    # Конфигурация аргументов
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_file = LaunchConfiguration("map")
    nav2_params_file = LaunchConfiguration("params_file")
    rviz_config_file = LaunchConfiguration("rviz_config")

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_map_file = DeclareLaunchArgument(
        "map",
        default_value=default_map_path,
        description="Full path to the map YAML file to load",
    )

    declare_params_file = DeclareLaunchArgument(
        "params_file",
        default_value=default_nav2_params,
        description="Full path to the Nav2 parameters file",
    )

    declare_rviz_config_file = DeclareLaunchArgument(
        "rviz_config",
        default_value=default_rviz_config,
        description="Full path to the RViz config file",
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "map": map_file,
            "use_sim_time": use_sim_time,
            "params_file": nav2_params_file,
        }.items(),
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config_file],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription(
        [
            declare_map_file,
            declare_params_file,
            declare_use_sim_time,
            nav2_launch,
            declare_rviz_config_file,
            rviz_node,
        ]
    )
