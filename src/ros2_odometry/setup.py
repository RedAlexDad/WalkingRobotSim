from setuptools import find_packages, setup
import os
from glob import glob

package_name = "ros2_odometry"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="RedAlexDad",
    maintainer_email="boss6852@gmail.com",
    description="ROS 2 package for odometry and TF publishing for a Unitree robot",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "nav_tf_publisher = ros2_odometry.tf_publisher:main",
            "static_map_publisher = ros2_odometry.static_map_publisher:main",
            "cmd_vel_bridge = ros2_odometry.cmd_vel_bridge:main",
        ],
    },
)
