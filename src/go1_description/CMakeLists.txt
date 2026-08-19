cmake_minimum_required(VERSION 3.28)
project(go1_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY meshes config xacro launch DESTINATION share/${PROJECT_NAME}/)

ament_package()
