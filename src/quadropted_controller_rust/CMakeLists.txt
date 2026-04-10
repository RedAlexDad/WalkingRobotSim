cmake_minimum_required(VERSION 3.8)
project(quadropted_controller_rust)

find_package(ament_cmake REQUIRED)

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

# Install all binaries
install(
    DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/target/release/
    DESTINATION lib/${PROJECT_NAME}
    USE_SOURCE_PERMISSIONS
    PATTERN ".cargo*" EXCLUDE
    PATTERN "*.d" EXCLUDE
    PATTERN "build" EXCLUDE
    PATTERN "deps" EXCLUDE
    PATTERN "examples" EXCLUDE
    PATTERN "incremental" EXCLUDE
    PATTERN "*.rlib" EXCLUDE
    PATTERN "*.dSYM" EXCLUDE
)

ament_package()
