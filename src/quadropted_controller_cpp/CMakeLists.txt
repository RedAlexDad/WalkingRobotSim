cmake_minimum_required(VERSION 3.28)
project(quadropted_controller_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -O3 -march=native)
  cmake_policy(SET CMP0069 NEW)
  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2 REQUIRED)
find_package(quadropted_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(Eigen3 REQUIRED)
include_directories(${EIGEN3_INCLUDE_DIR})

# ════════════════════════════════════════════════════════════
# Библиотека
# ════════════════════════════════════════════════════════════

file(GLOB _SRCS CONFIGURE_DEPENDS
  src/utils/*.cpp src/kinematics/*.cpp src/odometry/*.cpp src/states/*.cpp
  src/controllers/*.cpp src/controllers/trot/*.cpp src/controllers/crawl/*.cpp
  src/nodes/*_control.cpp)
add_library(${PROJECT_NAME} SHARED ${_SRCS})

target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

ament_target_dependencies(${PROJECT_NAME}
  rclcpp geometry_msgs nav_msgs sensor_msgs tf2_ros tf2 visualization_msgs quadropted_msgs Eigen3)

install(TARGETS ${PROJECT_NAME}
  EXPORT export_${PROJECT_NAME}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
  INCLUDES DESTINATION include)

# ════════════════════════════════════════════════════════════
# Исполняемые файлы (ROS 2 узлы)
# ════════════════════════════════════════════════════════════

add_executable(odometry_node src/nodes/odometry_node.cpp)
ament_target_dependencies(odometry_node visualization_msgs rclcpp nav_msgs sensor_msgs geometry_msgs tf2_ros quadropted_msgs Eigen3)
target_link_libraries(odometry_node ${PROJECT_NAME})

add_executable(robot_controller_node src/nodes/robot_controller_node.cpp)
ament_target_dependencies(robot_controller_node rclcpp std_msgs sensor_msgs tf2_ros quadropted_msgs Eigen3)
target_link_libraries(robot_controller_node ${PROJECT_NAME})

add_executable(cmd_vel_pub src/nodes/cmd_vel_pub.cpp)
ament_target_dependencies(cmd_vel_pub rclcpp geometry_msgs quadropted_msgs)
target_link_libraries(cmd_vel_pub ${PROJECT_NAME})

install(TARGETS odometry_node robot_controller_node cmd_vel_pub DESTINATION lib/${PROJECT_NAME})

# ════════════════════════════════════════════════════════════
# Тесты
# ════════════════════════════════════════════════════════════

if(BUILD_TESTING)
  find_package(ament_cmake_gmock REQUIRED)
  foreach(_t test_rotation_matrices test_homogeneous_transforms test_fk test_ik
            test_odometry test_pid test_gait test_message_builders
            test_cross_validation test_base_link_roll test_ik_with_roll test_step_trot
            test_fast_math test_stand_controller test_edge_cases)
    ament_add_gmock(${_t} test/${_t}.cpp)
    target_link_libraries(${_t} ${PROJECT_NAME})
  endforeach()
endif()

# ════════════════════════════════════════════════════════════
# Benchmark (standalone, no ROS dependencies)
# ════════════════════════════════════════════════════════════

file(GLOB _BENCH_SRCS CONFIGURE_DEPENDS benchmark/*.cpp)
add_executable(benchmark ${_BENCH_SRCS})
target_link_libraries(benchmark ${PROJECT_NAME})
install(TARGETS benchmark DESTINATION lib/${PROJECT_NAME})

# ════════════════════════════════════════════════════════════
# Установка
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# Документация (Doxygen)
# ════════════════════════════════════════════════════════════

find_package(Doxygen QUIET)
if(Doxygen_FOUND)
  configure_file(doc/Doxyfile.in ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile @ONLY)
  add_custom_target(doc
    COMMAND ${DOXYGEN_EXECUTABLE} ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    COMMENT "Generating API documentation with Doxygen"
    VERBATIM)
endif()

install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY config/ DESTINATION share/${PROJECT_NAME}/config)
install(DIRECTORY launch/ DESTINATION share/${PROJECT_NAME}/launch)

ament_export_include_directories(include)
ament_export_libraries(${PROJECT_NAME})
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(visualization_msgs rclcpp geometry_msgs nav_msgs sensor_msgs tf2_ros tf2 quadropted_msgs Eigen3)
ament_package()
