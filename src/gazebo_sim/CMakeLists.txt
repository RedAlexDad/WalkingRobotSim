cmake_minimum_required(VERSION 3.8)
project(gazebo_sim)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(urdf REQUIRED)
find_package(xacro REQUIRED)
find_package(std_msgs REQUIRED)

# Gazebo vendor cmake (ROS 2 Jazzy harmonic bundles)
list(APPEND CMAKE_PREFIX_PATH
  /opt/ros/jazzy/opt/gz_msgs_vendor
  /opt/ros/jazzy/opt/gz_transport_vendor
  /opt/ros/jazzy/opt/gz_math_vendor
  /opt/ros/jazzy/opt/gz_utils_vendor
)
find_package(gz-msgs10 REQUIRED)
find_package(gz-transport13 REQUIRED)
find_package(gz-math7 REQUIRED)
find_package(gz-utils2 REQUIRED)

add_executable(laser_to_cloud_converter
  src/laser_to_cloud_converter.cpp
)
target_link_libraries(laser_to_cloud_converter
  gz-msgs10::gz-msgs10
  gz-transport13::gz-transport13
  gz-math7::gz-math7
  gz-utils2::gz-utils2
)

install(DIRECTORY
  config
  launch
  world
  maps
  rviz
  models
  src
  scripts
  DESTINATION share/${PROJECT_NAME}/
)

install(TARGETS
  laser_to_cloud_converter
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  src/test_action.py
  scripts/waypoint_collector.py
  scripts/experiment_logger.py
  scripts/laser_to_pointcloud.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  PROGRAMS
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
