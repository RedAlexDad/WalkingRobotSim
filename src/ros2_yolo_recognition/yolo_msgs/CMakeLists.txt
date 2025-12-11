cmake_minimum_required(VERSION 3.8)
project(yolo_msgs)

# Опция для выбора типа робота
if(NOT DEFINED ROBOT_TYPE)
    set(ROBOT_TYPE "Go1" CACHE STRING "The type of robot, support Go1 and Go2")
    set_property(CACHE ROBOT_TYPE PROPERTY STRINGS Go1 Go2)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Point2D.msg"
  "msg/Vector2.msg"
  "msg/Pose2D.msg"
  "msg/BoundingBox2D.msg"
  "msg/BoundingBox3D.msg"
  "msg/Mask.msg"
  "msg/KeyPoint2D.msg"
  "msg/KeyPoint2DArray.msg"
  "msg/KeyPoint3D.msg"
  "msg/KeyPoint3DArray.msg"
  "msg/Detection.msg"
  "msg/DetectionArray.msg"
  "srv/SetClasses.srv"
  DEPENDENCIES std_msgs geometry_msgs
)

ament_package()
