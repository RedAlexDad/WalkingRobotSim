from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    # Определение аргументов запуска
    world = LaunchConfiguration('world')

    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value='empty.sdf',
        description='SDF world file to load in Gazebo'
    )

    # Запуск Gazebo Harmonic
    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-v', '4', '-r', world],
        output='screen'
    )

    # Запуск ROS-GZ моста для передачи данных между ROS 2 и Gazebo
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock'],
        output='screen'
    )

    return LaunchDescription([
        declare_world_cmd,
        gz_sim,
        bridge
    ])