"""Мультироботный запуск через per_robot_bringup на каждого робота.

Читает список роботов из `config/robots.yaml` и поднимает для каждого
свой `per_robot_bringup.launch.py` (Rust-контроллер, Rust-одометрия,
Rust cmd_vel_pub, Nav2 и EKF в собственном namespace).

Gazebo при этом запускается отдельно (`gazebo_multi.launch.py` /
`gazebo_multi_nav2_rust.launch.py`); здесь поднимается только bridge и роботы.

Bridge строится из шаблона `config/gz_bridge.yaml`: записи с `/robot1` —
шаблонные, для каждого робота из `robots.yaml` подставляется его namespace,
а общие записи (`/clock`, `/world_poses_info`) остаются в одном экземпляре.
Так `/robotN/odom_gz`, `/robotN/scan/points` и `/robotN/pose_ground_truth`
поднимаются для всех роботов, а не только для robot1.
"""

import os
import tempfile

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Токены шаблона: имя первого робота в `config/gz_bridge.yaml`.
TEMPLATE_NAMESPACE = "/robot1"
TEMPLATE_MODEL = "robot1_my_bot"


def _expand_entry(entry, robot_name):
    """Подставить namespace модели робота в шаблонную запись bridge."""
    expanded = {}
    for key, value in entry.items():
        if isinstance(value, str):
            value = value.replace(TEMPLATE_NAMESPACE, f"/{robot_name}")
            value = value.replace(TEMPLATE_MODEL, f"{robot_name}_my_bot")
        expanded[key] = value
    return expanded


def _build_bridge_config(template_path, robots):
    """Развернуть шаблон bridge под всех роботов и записать временный YAML.

    Общие записи (без токенов robot1) попадают в конфиг ровно один раз:
    два bridge-узла на один gz-топик создают дублирующихся publisher'ов.
    """
    with open(template_path) as f:
        template = yaml.safe_load(f) or []

    expanded_entries = []
    seen = set()
    for robot in robots:
        for entry in template:
            expanded = _expand_entry(entry, robot["name"])
            fingerprint = yaml.safe_dump(expanded, sort_keys=True)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            expanded_entries.append(expanded)

    bridge_dir = tempfile.mkdtemp(prefix="wrs_gz_bridge_")
    config_path = os.path.join(bridge_dir, "gz_bridge.yaml")
    with open(config_path, "w") as f:
        yaml.safe_dump(expanded_entries, f, sort_keys=False, allow_unicode=True)
    return config_path


def generate_launch_description():
    ld = LaunchDescription()

    pkg_path = get_package_share_directory("gazebo_sim")

    with open(os.path.join(pkg_path, "config", "robots.yaml")) as f:
        robots = yaml.safe_load(f)["robots"]

    bridge_config = _build_bridge_config(
        os.path.join(pkg_path, "config", "gz_bridge.yaml"), robots
    )

    ld.add_action(DeclareLaunchArgument("use_sim_time", default_value="true"))
    ld.add_action(DeclareLaunchArgument("enable_rviz", default_value="true"))
    ld.add_action(DeclareLaunchArgument("camera_fps", default_value="30"))
    ld.add_action(DeclareLaunchArgument("use_elevation", default_value="false"))

    use_sim_time = LaunchConfiguration("use_sim_time")

    ld.add_action(
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "--ros-args",
                "-p",
                f"config_file:={bridge_config}",
            ],
        )
    )

    per_robot_file = os.path.join(pkg_path, "launch", "per_robot_bringup.launch.py")

    for robot in robots:
        ld.add_action(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(per_robot_file),
                launch_arguments={
                    "namespace": robot["name"],
                    "x_pose": robot["x_pose"],
                    "y_pose": robot["y_pose"],
                    "z_pose": robot["z_pose"],
                    "camera_fps": LaunchConfiguration("camera_fps"),
                    "use_sim_time": use_sim_time,
                    "use_elevation": LaunchConfiguration("use_elevation"),
                    "enable_rviz": LaunchConfiguration("enable_rviz"),
                }.items(),
            )
        )

    return ld
