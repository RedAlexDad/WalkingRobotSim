cmake_minimum_required(VERSION 3.5)
project(quadropted_perception)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

ament_python_install_package(
  ${PROJECT_NAME}
  PACKAGE_DIR quadropted_perception
)

install(PROGRAMS
  quadropted_perception/yolo_detector.py
  quadropted_perception/visualizer.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  models
  DESTINATION share/${PROJECT_NAME}/
)

install(FILES
  resource/quadropted_perception
  DESTINATION share/${PROJECT_NAME}/resource
)

ament_package()
