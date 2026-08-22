cmake_minimum_required(VERSION 3.8)
project(std_msgs_rs)

find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)

# Ensure cargo is in PATH
set(ENV{PATH} "$ENV{HOME}/.cargo/bin:$ENV{PATH}")

# Build the Rust library
execute_process(
    COMMAND cargo build --release
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE result
)
if(NOT result EQUAL 0)
    message(FATAL_ERROR "cargo build failed: ${result}")
endif()

ament_package()
