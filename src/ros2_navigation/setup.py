from setuptools import find_packages, setup
import os
from glob import glob

package_name = "ros2_navigation"


# Функция для рекурсивного поиска файлов в директории
def recursive_data_files(directory):
    data_files = []
    for path, _, files in os.walk(directory):
        if files:
            install_path = os.path.join("share", package_name, path)
            source_files = [os.path.join(path, f) for f in files]
            data_files.append((install_path, source_files))
    return data_files


setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "params"), glob("params/*.yaml")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "rviz"), glob("rviz/*.rviz")),
        (os.path.join("share", package_name, "xml"), glob("xml/*.xml")),
    ]
    + recursive_data_files("maps"),
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="RedAlexDad",
    maintainer_email="boss6852@gmail.com",
    description="Navigation package for Go1 robot",
    license="Apache-2.0",
    # tests_require=["pytest"],
    entry_points={
        "console_scripts": [],
    },
)
