from setuptools import find_packages, setup
import os
from glob import glob

package_name = "ros2_yolo_recognition"

model_files = []
if os.path.exists("models"):
    model_files = [os.path.join("models", f) for f in os.listdir("models")]

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/models", model_files),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="redalexdad",
    maintainer_email="boss6852@gmail.com",
    description="YOLO for ROS 2",
    license="GPL-3",
    # tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "yolo_node = ros2_yolo_recognition.yolo_node:main",
            "debug_node = ros2_yolo_recognition.debug_node:main",
            "tracking_node = ros2_yolo_recognition.tracking_node:main",
            "detect_3d_node = ros2_yolo_recognition.detect_3d_node:main",
            "detect_object = ros2_yolo_recognition.detect_object:main",
        ],
    },
)
