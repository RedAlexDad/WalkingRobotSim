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
    default_rtabmap_params = os.path.join(cartography_dir, "params", "rtabmap.yaml")
    default_rviz_config = os.path.join(cartography_dir, "rviz", "rtabmap.rviz")

    # Конфигурация аргументов
    use_sim_time = LaunchConfiguration("use_sim_time")
    rtabmap_params_file = LaunchConfiguration("rtabmap_params_file")
    rviz_config_file = LaunchConfiguration("rviz_config_file")

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_rtabmap_params_file_cmd = DeclareLaunchArgument(
        "rtabmap_params_file",
        default_value=default_rtabmap_params,
        description="Full path to the RTAB-Map parameter file",
    )

    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        "rviz_config_file",
        default_value=default_rviz_config,
        description="Full path to the RViz config file to use",
    )

    # Установка переменной окружения для вывода логов
    set_log_envvar = SetEnvironmentVariable("RCUTILS_LOGGING_BUFFERED_STREAM", "1")

    # Узел RTAB-Map (SLAM)
    rtabmap_node = Node(
        package="rtabmap_slam",
        executable="rtabmap",
        name="rtabmap",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            rtabmap_params_file,
            {"frame_id": "base_link"},
            {"subscribe_depth": True},
            {"subscribe_rgb": True},
        ],
        remappings=[
            ("rgb/image", "/rgb_cam/image_raw"),
            ("rgb/camera_info", "/rgb_cam/camera_info"),
            ("depth/image", "/depth_cam/depth/image_raw"),
            ("odom", "/odom"),
        ],
    )

    # Узел визуализации RTAB-Map
    rtabmap_viz_node = Node(
        package="rtabmap_viz",
        executable="rtabmap_viz",
        name="rtabmap_viz",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            rtabmap_params_file,
            {"frame_id": "base_link"},
            {"subscribe_depth": True},
            {"subscribe_rgb": True},
        ],
        remappings=[
            ("rgb/image", "/rgb_cam/image_raw"),
            ("rgb/camera_info", "/rgb_cam/camera_info"),
            ("depth/image", "/depth_cam/depth/image_raw"),
            ("odom", "/odom"),
        ],
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
            declare_rtabmap_params_file_cmd,
            declare_rviz_config_file_cmd,
            rtabmap_node,
            rtabmap_viz_node,
            rviz_node,
        ]
    )
