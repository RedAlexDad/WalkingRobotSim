"""Мультироботный запуск: Gazebo + bridge + per-robot bringup на Rust-нодах.

Точка входа для `make gazebo-multi`. Поднимает только физику (`gz sim`),
а через `startup_delay` передаёт управление
`gazebo_multi_nav2_per_robot.launch.py`: тот читает `config/robots.yaml`
и стартует `per_robot_bringup.launch.py` для каждого робота (Rust-контроллер,
Rust-одометрия, Rust cmd_vel_pub, Nav2 и EKF в собственном namespace).

Отличие от `launch.launch.py`: там Gazebo включает монолитный
`gazebo_multi_nav2_rust.launch.py`, который сам спавнит роботов из
`robots.yaml`. Здесь спавн делает per-robot bringup, поэтому подключать
монолитный launch нельзя — роботы заспавнились бы дважды.

Аргументы: world, gui (false — headless `gz sim -s`), use_sim_time,
camera_fps, enable_rviz, use_elevation, startup_delay.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():
    ld = LaunchDescription()

    pkg_path = get_package_share_directory('gazebo_sim')

    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    use_sim_time = LaunchConfiguration('use_sim_time')
    camera_fps = LaunchConfiguration('camera_fps')
    enable_rviz = LaunchConfiguration('enable_rviz')
    use_elevation = LaunchConfiguration('use_elevation')
    startup_delay = LaunchConfiguration('startup_delay')

    ld.add_action(DeclareLaunchArgument(
        'world', default_value='cafe.world',
        description='Файл мира в gazebo_sim/world'))
    ld.add_action(DeclareLaunchArgument(
        'gui', default_value='true',
        description='Gazebo GUI (false — headless, только сервер gz sim -s)'))
    ld.add_action(DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Использовать симуляционное время'))
    ld.add_action(DeclareLaunchArgument(
        'camera_fps', default_value='10',
        description='FPS камеры для image bridge'))
    ld.add_action(DeclareLaunchArgument(
        'enable_rviz', default_value='true',
        description='RViz на каждого робота (false — headless)'))
    ld.add_action(DeclareLaunchArgument(
        'use_elevation', default_value='false',
        description='Слой elevation costmap в Nav2'))
    ld.add_action(DeclareLaunchArgument(
        'startup_delay', default_value='6.0',
        description='Пауза перед спавном роботов, с (gz sim должен подняться)'))

    world_file = PathJoinSubstitution([pkg_path, 'world', world])
    gz_sim_launch = os.path.join(
        get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')

    # gz sim: GUI-окно либо headless-сервер (-s).
    gazebo_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={
            'gz_args': ['-r -v4 ', world_file],
            'on_exit_shutdown': 'true',
        }.items(),
        condition=IfCondition(gui),
    )
    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={
            'gz_args': ['-s -r -v4 ', world_file],
            'on_exit_shutdown': 'true',
        }.items(),
        condition=UnlessCondition(gui),
    )
    ld.add_action(gazebo_gui)
    ld.add_action(gazebo_headless)

    # Bridge (/clock из gz_bridge.yaml) + per-robot bringup по robots.yaml.
    robots = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, 'launch',
                         'gazebo_multi_nav2_per_robot.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'camera_fps': camera_fps,
            'enable_rviz': enable_rviz,
            'use_elevation': use_elevation,
        }.items(),
    )
    ld.add_action(TimerAction(period=startup_delay, actions=[robots]))

    return ld
