"""
Запуск Gazebo симуляции с Rust контроллером (по умолчанию).
Для C++ контроллера используйте launch_cpp.launch.py (цель make gazebo-cpp).

Поддерживает аргументы как launch_cpp.launch.py:
  use_sim_time:=true  camera_fps:=10  use_elevation:=true
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetParameter


def generate_launch_description():
    ld = LaunchDescription()
    package_name = 'gazebo_sim'
    pkg_path = get_package_share_directory(package_name)

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    camera_fps = LaunchConfiguration('camera_fps', default='10')
    use_elevation = LaunchConfiguration('use_elevation', default='false')
    enable_rviz = LaunchConfiguration('enable_rviz', default='true')

    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='true',
                                       description='Использовать симуляционное время'))
    ld.add_action(DeclareLaunchArgument('camera_fps', default_value='10',
                                       description='FPS камеры для image bridge'))
    ld.add_action(DeclareLaunchArgument('use_elevation', default_value='false',
                                       description='Использовать elevation costmap'))
    ld.add_action(DeclareLaunchArgument('enable_rviz', default_value='true',
                                       description='Включить RViz (false — лёгкий режим, меньше нагрузка на CPU)'))
    ld.add_action(SetParameter(name='use_sim_time', value=use_sim_time))

    world_file = os.path.join(pkg_path, 'world', 'cafe.world')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r -v4 ', world_file], 'on_exit_shutdown': 'true'}.items()
    )
    ld.add_action(gazebo)

    pause = ExecuteProcess(cmd=['sleep', '6'], output='screen')
    ld.add_action(pause)

    # По умолчанию — Rust контроллер (+ Rust odometry node)
    # NOTE: elevation costmap (use_elevation) — отдельная функциональность
    # elevation_mapping_cupy, не связана с контроллером; для неё используйте
    # launch_cpp.launch.py / make gazebo-cpp ELEVATION=true.
    multi_nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, 'launch', 'gazebo_multi_nav2_rust.launch.py')
        ),
        launch_arguments={
            'camera_fps': camera_fps,
            'enable_rviz': enable_rviz,
        }.items(),
    )

    ld.add_action(RegisterEventHandler(
        event_handler=OnProcessExit(target_action=pause, on_exit=[multi_nav2_launch])
    ))

    return ld
