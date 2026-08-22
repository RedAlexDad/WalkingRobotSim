cmake_minimum_required(VERSION 3.8)
project(quadropted_controller_rust)

find_package(ament_cmake REQUIRED)
find_package(quadropted_msgs REQUIRED)

# Install launch files
install(DIRECTORY launch/
    DESTINATION share/${PROJECT_NAME}/launch
)

# Ensure cargo is in PATH
set(ENV{PATH} "$ENV{HOME}/.cargo/bin:$ENV{PATH}")

# Build the Rust workspace
execute_process(
    COMMAND cargo build --release
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE result
)
if(NOT result EQUAL 0)
    message(FATAL_ERROR "cargo build failed: ${result}")
endif()

# Install the specific executables
install(
    PROGRAMS ${CMAKE_CURRENT_SOURCE_DIR}/target/release/robot_controller_node
            ${CMAKE_CURRENT_SOURCE_DIR}/target/release/odometry_node
    DESTINATION lib/${PROJECT_NAME}
)

ament_package()
