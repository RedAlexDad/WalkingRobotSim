cmake_minimum_required(VERSION 3.8)
project(elevation_mapping_cupy)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(grid_map_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

set(dependencies
  rclpy
  std_msgs
  sensor_msgs
  nav_msgs
  geometry_msgs
  grid_map_msgs
  tf2_ros
)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  scripts/elevation_mapping_node.py
  scripts/elevation_to_costmap_node.py
  scripts/synthetic_pointcloud_tf_publisher.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch config rviz
  DESTINATION share/${PROJECT_NAME}
)

# Install test files for integration tests
install(
  DIRECTORY test
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(ament_cmake_ros REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)

  set(_COV_SITE_PACKAGES "")
  if(DEFINED ENV{COV_CORE_CONFIG})
    set(_COV_SITE_PACKAGES "PYTHONPATH=$ENV{COV_CORE_CONFIG}:$ENV{PYTHONPATH}")
  endif()

  macro(add_unit_test name path)
    ament_add_pytest_test(${name}
      ${CMAKE_CURRENT_SOURCE_DIR}/${PROJECT_NAME}/${path}
      TIMEOUT 180
      APPEND_ENV PATH=${_COV_SITE_PACKAGES}
      ENV PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
    )
  endmacro()

  # Unit tests (run via pytest, no ROS dependencies)
  add_unit_test(test_map_shifting tests/test_map_shifting.py)
  add_unit_test(test_map_services tests/test_map_services.py)
  add_unit_test(test_gridmap_layout tests/test_gridmap_layout.py)
  add_unit_test(test_parameter tests/test_parameter.py)
  add_unit_test(test_repo_config_sanity tests/test_repo_config_sanity.py)
  add_unit_test(test_kernel_compile_smoke tests/test_kernel_compile_smoke.py)
  add_unit_test(test_backend tests/test_backend.py)
  add_unit_test(test_plugin_manager tests/test_plugin_manager.py)
  add_unit_test(test_plugin_implementations tests/test_plugin_implementations.py)
  add_unit_test(test_traversability_filter tests/test_traversability_filter.py)
  add_unit_test(test_cpu_kernels tests/test_cpu_kernels.py)
  add_unit_test(test_semantic_kernels tests/test_semantic_kernels.py)

  # Define isolated launch test function for unique ROS_DOMAIN_ID per test
  # See: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Integration.html
  function(add_ros_isolated_launch_test path)
    set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
    add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
  endfunction()

  # Integration test (launches ROS nodes)
  # DDS fixes:
  #   FASTDDS_BUILTIN_TRANSPORTS=UDPv4: Avoid FastDDS shared memory discovery issues
  #   See: https://answers.ros.org/question/407025/
  # SKIP_DDS_FLAKES=1: In CI, skip (not fail) on known DDS discovery issues.
  # Locally, tests fail loudly to catch real regressions.
  add_ros_isolated_launch_test(test/test_tf_gridmap_integration.py
    TIMEOUT 180
    ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4
  )

  add_ros_isolated_launch_test(test/test_map_save_load_services.py
    TIMEOUT 240
    ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4
  )

  # Smoke-test the actual golden-path launch file (without RViz).
  add_ros_isolated_launch_test(test/test_synthetic_demo_launch.py
    TIMEOUT 180
    ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4
  )
endif()

ament_export_dependencies(${dependencies})
ament_package()
