cmake_minimum_required(VERSION 3.8)
project(ros2_rust_pubsub_test)

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

# Install release binaries
install(
    FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/target/release/pub
    ${CMAKE_CURRENT_SOURCE_DIR}/target/release/sub
    ${CMAKE_CURRENT_SOURCE_DIR}/target/release/rclrs_check
    PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    DESTINATION lib/${PROJECT_NAME}
)

ament_package()
