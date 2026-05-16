# Unitree go2, go1 simulation in Gazebo Sim

This repository allows you to run dog robots in the GAZEBO simulator. The robot can walk, rotate with 12 degrees of freedom, and features a `robot_msgs` interface. The robot moves using inverse kinematics, and its odometry is based on direct kinematics. Additionally, all functionalities are developed in Python.

## Run from docker

> **Note:** BUILDED AND TESTED WITH NVIDIA GPU.

### setup docker, docker compose and nvidia container toolkit

[docker install](https://docs.docker.com/engine/install/ubuntu/)

[nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### build docker :

```bash
mkdir -p ~/go_sim/src
cd ~/go_sim/src/docker
docker compose -f compose.yml build simulator
xhost +local:docker
docker compose -f compose.yml up simulator
```

## Run from source

> **Note:** BUILDED AND TESTED FROM ROS2 JAZZY, UBUNTU 22.04.

> **Note:** Before launching, ensure that you install all dependencies and build the project using `colcon build`.

---

## Setup and Installation

### Clone the Repository and Build

```bash
mkdir -p ~/go_sim/src
cd ~/go_sim/src
git clone https://github.com/abutalipovvv/go_sim_py.git .
cd ..
colcon build --symlink-install
```

### Install Dependencies

```bash
cd ~/go_sim
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

## Environment Configuration

### Export Gazebo Models Path

Before running the simulation, export the path to your Gazebo models:

```bash
export GZ_SIM_RESOURCE_PATH=~/go_sim/src/gazebo_sim/models
```

(Replace with the correct path to your models.)

### Configure CycloneDDS

To support multiple topics, configure CycloneDDS by creating a configuration file (e.g., cyclonedds.xml) with the following content:

```bash
<CycloneDDS>
  <Domain>
    <General>
      <Interfaces>
        <NetworkInterface name="lo" multicast="true" />
      </Interfaces>
      <DontRoute>true</DontRoute>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>100</MaxAutoParticipantIndex>
    </Discovery>
  </Domain>
</CycloneDDS>
```

Then, set the environment variable to point to this file:

```bash
export CYCLONEDDS_URI=file://path_to_cyclonedds.xml
```

(Replace `path_to_cyclonedds.xml` with the actual file path.)

## Running the Simulation

```bash
#Navigate to the project directory:

cd ~/go_sim

#Source the environment setup:

source install/local_setup.bash

#Launch the simulation:

ros2 launch gazebo_sim launch.py
```

## Controlling the Robot

### Moving the Robot

The robot moves by publishing velocity commands to the `<robot_namespace>/cmd_vel` topic. By default, the robot is named robot1.

Example using `teleop_twist_keyboard`:

```bash
source install/local_setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

![](./media/robot_move.gif)

Robot Modes

The robot supports several modes:

    REST – Default position in which the robot cannot move.
    STAND – Mode in which the robot can rotate in place.
    TROT – Walking mode.

The robot operates with 12 degrees of freedom. To enable rotation, switch the mode to "STAND" by publishing to the robot_mode topic.

Example (for a robot with namespace `robot1`):

```bash
ros2 topic pub /robot1/robot_mode quadropted_msgs/msg/RobotModeCommand "{mode: 'STAND', robot_id: 1}"
```

After switching modes, control the robot using velocity commands:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

![](./media/move1.gif)

### Changing Robot Behavior

The robot can sit and stand using the `robot_behavior_command` service.

Example command:

```bash
ros2 service call /robot1/robot_behavior_command quadropted_msgs/srv/RobotBehaviorCommand "{command: 'walk'}"
```

Possible commands:

    walk – The robot stands up (REST) and can walk (TROT).
    up – The robot stands up (REST) and locks movement.
    sit – The robot sits down (STAND).

![](./media/sitUp.gif)

## Multi-Robot Setup and Model Switching

### Changing Robot Models

You can change between robot models (e.g., go2, go1) in gazebo_multi_nav2_world.launch.py file 102 str:

![](./media/switch.png)

for go2: use "go2_description"
for go1: use "go1_description"

Running Multiple Robots Simultaneously
![](./media/go1multi.png)
![](./media/go2multi.png)

### The repository supports simultaneous operation of multiple robots. Each robot has access to nav2. In the robot.config file, add the robot’s namespace and spawn coordinates in the world.

![](./media/robot_config.png)

### NAV2 work demonstration:

![](./media/robot-nav2.gif)

## Credits, thaks for all

    mike4192: (SpotMicro)[https://github.com/mike4192/spotMicro]
    Unitree Robotics: (A1 ROS)[https://github.com/unitreerobotics/a1_ros]
    QUADRUPED ROBOTICS: (Quadruped)[https://quadruped.de]
    lnotspotl: (GitHub)[https://github.com/lnotspotl]
    anujjain-dev: (Unitree-go2 ROS2)[https://github.com/anujjain-dev/unitree-go2-ros2]

## Docker Compose v2 и устранение проблем с кэшем

### Проблема с cache_from

При использовании Docker Compose v2 может возникать ошибка:

```
ERROR: failed to configure registry cache importer: pull access denied, repository does not exist or may require authorization
```

Эта ошибка возникает из-за секции `cache_from` в файле `compose.yml`, которая пытается загрузить образы `walking_robot_sim:*` из Docker Hub, но эти образы не существуют или недоступны.

### Решение

1. **Удаление секции cache_from** (реализовано в текущей версии):
   - Секция `cache_from` была удалена из `compose.yml`
   - Docker теперь использует локальный кэш сборки автоматически

2. **Сборка без кэша** (при необходимости):

   ```bash
   make deploy-no-cache
   ```

   или

   ```bash
   docker compose -f src/docker/compose.yml build --no-cache simulator
   ```

3. **Альтернативное решение - использование локальных образов**:
   Если хотите использовать кэширование, можно предварительно собрать образы с тегами:
   ```bash
   docker build -t walking_robot_sim:base-system --target base-system -f src/docker/Dockerfile ../..
   ```

### Стандарт Docker Compose v2

- Docker Compose v2 использует синтаксис `docker compose` (без дефиса)
- Поддерживает многостадийные сборки с кэшированием
- Секция `cache_from` предназначена для указания источников кэша из реестра
- Для локальной разработки рекомендуется использовать локальный кэш Docker

### Рекомендации

1. Для первой сборки используйте `make deploy-no-cache`
2. Для последующих сборок используйте `make deploy` (будет использоваться локальный кэш)
3. При изменении зависимостей ROS очищайте кэш: `docker builder prune`

## TODO

    Add Gazebo Classic support (physics and inertial parameters for URDF).
    Perform odometry calibration
