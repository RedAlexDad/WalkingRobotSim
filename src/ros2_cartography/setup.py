from setuptools import find_packages, setup
import os
from glob import glob

package_name = "ros2_cartography"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "params"), glob("params/*.yaml")),
        (os.path.join("share", package_name, "rviz"), glob("rviz/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="RedAlexDad",
    maintainer_email="boss6852@gmail.com",
    description="ROS 2 package for SLAM and mapping with a Unitree robot",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [],
    },
)
