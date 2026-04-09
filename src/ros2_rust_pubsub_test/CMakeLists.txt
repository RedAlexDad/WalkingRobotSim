cmake_minimum_required(VERSION 3.8)
project(ros2_rust_pubsub_test)

# Find colcon-ros-cargo support
find_package(ament_cmake REQUIRED)

# Build the Rust code
execute_process(
    COMMAND cargo build --release
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE result
)
if(NOT result EQUAL 0)
    message(FATAL_ERROR "cargo build failed: ${result}")
endif()

# Install the binary
install(
    DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/target/release/
    DESTINATION lib/${PROJECT_NAME}
    USE_SOURCE_PERMISSIONS
)

ament_package()
