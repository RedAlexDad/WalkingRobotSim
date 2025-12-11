Unitree robot ROS2 support

[TOC]

# Introduction

Unitree SDK2 implements an easy-to-use robot communication mechanism based on Cyclonedds, which enable developers to achieve robot communication and control (**Supports Unitree Go2 and H1**). See: https://github.com/unitreerobotics/unitree_sdk2

DDS is alos used in ROS2 as a communication mechanism. Therefore, the underlying layers of Unitree Go2 and H1 robots can be compatible with ROS2. ROS2 msg can be direct used for communication and control of Unitree robot without wrapping the SDK interface.

# Configuration

## System requirements

Tested systems and ROS2 distro
|systems|ROS2 distro|
|--|--|
|Ubuntu 20.04|foxy|
|Ubuntu 22.04|humble (recommend)|

If you want to directly use the `Docker development environment`, you can refer to the `Dockerfile` related content in the `.devcontainer` folder.
You can also use the `Dev Container feature of VSCode` or other IDEs to create a development environment, or use `Github's codespace` to quickly create a development environment.
If you do encounter compilation issues, you can refer to the compilation scripts in `. github/workflows/` or ask questions in `issues`.

##Install Unitree Robot Ros2 Feature Pack

Taking ROS2 foxy as an example, if you need another version of ROS2, replace "foxy" with the current ROS2 version name in the corresponding place:

The installation of ROS2 foxy can refer to: https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html

ctrl+alt+T open the terminal, clone the repository: https://github.com/unitreerobotics/unitree_ros2

```bash
git clone https://github.com/unitreerobotics/unitree_ros2
```

where:

- **cyclonedds_ws**: The workspace of Unitree ros2 package. The msg for Unitree robot are supplied in the subfolder cyclonedds*ws/unitree/unitree_go and cyclonedds* ws/unitree/unitree_api.
- **example**: The workspace of some examples.

## Install Unitree ROS2 package

### 1. Dependencies

```bash
sudo apt install ros-foxy-rmw-cyclonedds-cpp
sudo apt install ros-foxy-rosidl-generator-dds-idl
sudo apt install libyaml-cpp-dev
```

### 2. Compile cyclone dds (If using Humble, this step can be skipped)

The cyclonedds version of Unitree robot is 0.10.2. To communicate with Unitree robots using ROS2, it is necessary to change the dds implementation. See：https://docs.ros.org/en/foxy/Concepts/About-Different-Middleware-Vendors.html

Before compiling cyclonedds, please ensure that ros2 environment has **NOT** been sourced when starting the terminal. Otherwise, it may cause errors in compilation.

If "source/opt/ros/foxy/setup. bash" has been added to the ~/.bashrc file when installing ROS2, it needs to be commented out:

```bash
sudo apt install gedit
sudo gedit ~/.bashrc
```

```bash
# source /opt/ros/foxy/setup.bash
```

Compile cyclone-dds

```bash
cd ~/unitree_ros2/cyclonedds_ws/src
git clone https://github.com/ros2/rmw_cyclonedds -b foxy
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd ..
# If build failed, try run: `export LD_LIBRARY_PATH=/opt/ros/foxy/lib` first.
colcon build --packages-select cyclonedds #Compile cyclone-dds package
```

### 3. Compile unitree_go and unitree_api packages

After compiling cyclone-dds, ROS2 dependencies is required for compilation of the unitree_go and unitree_api packages. Therefore, before compiling, it is necessary to source the environment of ROS2.

```bash
source /opt/ros/foxy/setup.bash # source ROS2 environment
colcon build # Compile all packages in the workspace
```
