# Testing Guide for elevation_mapping_cupy

## Running Tests Locally

### Prerequisites

```bash
# Source ROS2
source /opt/ros/jazzy/setup.bash

# Build the package
colcon build --packages-select elevation_mapping_cupy

# Source the workspace
source install/setup.bash
```

### Run All Tests via colcon

```bash
colcon test --packages-select elevation_mapping_cupy --event-handlers console_direct+
```

### Run Unit Tests Only (pytest)

These are the primary regression tests for the axis-swap bug. They don't require ROS nodes to be running.

```bash
# Run all unit tests
cd elevation_mapping_cupy/elevation_mapping_cupy/tests/
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -v

# Run specific test file
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest test_map_shifting.py -v

# Run specific test
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest test_map_shifting.py::TestShiftMapXY::test_shift_x_only_affects_columns -v
```

### Run Integration Tests Only (launch_testing)

These test the full TF → GridMap pipeline with actual ROS nodes.

```bash
# Stop daemon first to avoid DDS issues
ros2 daemon stop

# Run with DDS fixes
FASTDDS_BUILTIN_TRANSPORTS=UDPv4 python3 -m launch_testing.launch_test \
    src/elevation_mapping_cupy/elevation_mapping_cupy/test/test_tf_gridmap_integration.py
```

### Test Summary

| Test File | Type | What it tests |
|-----------|------|---------------|
| `test_map_shifting.py` | Unit (pytest) | Axis-swap bug regression - `shift_map_xy()` function |
| `test_map_services.py` | Unit (pytest) | Map service handlers |
| `test_tf_gridmap_integration.py` | Integration (launch_testing) | Full TF → GridMap pipeline |

---

# ROS2 Integration Testing: DDS Discovery Fixes

This document captures lessons learned from fixing DDS discovery issues in `launch_testing` integration tests.

## Problem

DDS discovery between the test fixture process and launched nodes fails intermittently in `launch_testing`. Symptoms:
- Test fixture cannot subscribe to topics published by launched nodes
- `wait_for_gridmap()` times out even though node is publishing
- Tests pass locally sometimes but fail in CI

## Root Causes & Fixes

### 1. ROS2 Daemon RMW Mismatch

**Cause**: The ROS2 daemon may be running with a different RMW implementation than the tests. This causes discovery timeouts.

**Fix**: Stop the daemon before tests run.

```python
# In generate_test_description() or setUpClass()
import subprocess
subprocess.run(['ros2', 'daemon', 'stop'], capture_output=True)
```

**Source**: [ros2/system_tests#460](https://github.com/ros2/system_tests/pull/460)

### 2. FastDDS Shared Memory Transport Issues

**Cause**: FastDDS uses shared memory (SHM) by default for same-machine communication. This can fail in certain environments (Docker, VMs, some Linux configurations).

**Fix**: Force UDPv4 transport instead of shared memory.

```python
# In Python
import os
os.environ['FASTDDS_BUILTIN_TRANSPORTS'] = 'UDPv4'
```

```cmake
# In CMakeLists.txt
add_launch_test(test/my_test.py
  ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4
)
```

**Alternative**: Switch to CycloneDDS:
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

**Source**: [ROS Answers: DDS discovery not working on same machine](https://answers.ros.org/question/407025/)

### 3. Missing Domain ID Isolation

**Cause**: Using `add_launch_test` without isolation can cause cross-talk between parallel tests.

**Fix**: Use `add_ros_isolated_launch_test` for unique ROS_DOMAIN_ID per test.

```cmake
# In CMakeLists.txt
find_package(ament_cmake_ros REQUIRED)

function(add_ros_isolated_launch_test path)
  set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
  add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
endfunction()

add_ros_isolated_launch_test(test/my_integration_test.py
  TIMEOUT 180
)
```

**Source**: [ROS2 Integration Testing Docs](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Integration.html)

### 4. QoS Profile Mismatch

**Cause**: Incompatible QoS profiles between publisher and subscriber silently prevent message delivery.

**Debug**:
```bash
ros2 topic info /my_topic -v  # Shows QoS of all publishers/subscribers
```

**Fix**: Ensure QoS compatibility. Common issues:
- `RELIABLE` subscriber cannot receive from `BEST_EFFORT` publisher
- `TRANSIENT_LOCAL` durability mismatch

**Source**: [ROS2 QoS Documentation](https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Quality-of-Service-Settings.html)

## Complete CMakeLists.txt Example

```cmake
if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(ament_cmake_ros REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)

  # Unit tests (no ROS dependencies)
  ament_add_pytest_test(test_my_module
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_my_module.py
    TIMEOUT 120
    ENV PYTEST_DISABLE_PLUGIN_AUTOLOAD=1  # Avoid launch_testing import issues
  )

  # Define isolated launch test function
  function(add_ros_isolated_launch_test path)
    set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
    add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
  endfunction()

  # Integration test with DDS fixes
  add_ros_isolated_launch_test(test/test_integration.py
    TIMEOUT 180
    ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4
  )
endif()
```

## Complete Test File Pattern

```python
import os
import subprocess
import unittest

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor

import launch
import launch_ros
import launch_testing

def generate_test_description():
    # Stop daemon to avoid RMW mismatch
    subprocess.run(['ros2', 'daemon', 'stop'], capture_output=True)

    # Force UDPv4 transport
    os.environ['FASTDDS_BUILTIN_TRANSPORTS'] = 'UDPv4'

    node_under_test = launch_ros.actions.Node(
        package='my_package',
        executable='my_node',
        name='my_node',
    )

    return (
        launch.LaunchDescription([
            node_under_test,
            launch_testing.actions.ReadyToTest(),
        ]),
        {'node_under_test': node_under_test}
    )

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Also stop daemon here in case generate_test_description ran in different process
        subprocess.run(['ros2', 'daemon', 'stop'], capture_output=True)

        try:
            rclpy.init()
        except RuntimeError:
            pass  # Already initialized

        cls.node = Node('test_node')
        cls.executor = SingleThreadedExecutor()
        cls.executor.add_node(cls.node)

    @classmethod
    def tearDownClass(cls):
        cls.executor.shutdown()
        cls.node.destroy_node()

    def test_something(self):
        # Your test here
        pass
```

## Debugging Tips

1. **Check if daemon is running**:
   ```bash
   ros2 daemon status
   ```

2. **Check RMW implementation**:
   ```bash
   echo $RMW_IMPLEMENTATION
   ros2 doctor --report | grep middleware
   ```

3. **List all topics with QoS**:
   ```bash
   ros2 topic list -v
   ros2 topic info /my_topic -v
   ```

4. **Test DDS discovery manually**:
   ```bash
   # Terminal 1
   ros2 topic pub /test std_msgs/String "data: hello"

   # Terminal 2
   ros2 topic echo /test
   ```

5. **Force different DDS**:
   ```bash
   RMW_IMPLEMENTATION=rmw_cyclonedds_cpp ros2 topic list
   ```

## Bug Fixes After Merge (31 → 72 passing)

### 1. `traversability_filter.py:__call__` — Missing `import numpy` + dimension mismatch
- **Проблема**: `__call__` использовал `np` без импорта (NameError). После импорта — `ValueError: dimensions mismatch` при `np.concatenate` dilation-выходов: `out2[:, 1:-1, 1:-1]` обрезался до 196×196, а `out1` и `out3` оставались 200×200.
- **Исправление**: Добавлен `import numpy as np` в начало метода; добавлена обрезка `out1[:, 2:-2, 2:-2]` для выравнивания размеров всех трёх выходов в 196×196.

### 2. `elevation_mapping.py` — Missing `get_position` method
- **Проблема**: `test_get_position` падал с `AttributeError: 'ElevationMap' object has no attribute 'get_position'`. Метод был утерян при слиянии.
- **Исправление**: Добавлен метод `get_position`, копирующий логику `get_center_position` (возвращает `self.center`).

### 3. `elevation_mapping.py:exists_layer` — Check `additional_layers`
- **Проблема**: `test_exists_layer` падал, т.к. `exists_layer` не проверял `self.param.additional_layers` (там лежат "feat_0", "feat_1" и т.д.).
- **Исправление**: Добавлена проверка `elif name in self.param.additional_layers: return True`.

### 4. `test_elevation_mapping.py:elmap_ex` fixture — Sync `additional_layers`
- **Проблема**: При параметризации `add_lay` фикстура не синхронизировала `p.additional_layers`, из-за чего `exists_layer` не находил слои.
- **Исправление**: Добавлена строка `p.additional_layers = additional_layer` в фикстуру.

### 5. `test_elevation_mapping.py:test_get_map` — `rgb` layer не поддерживается
- **Проблема**: Для `add_lay0` (feat_0, feat_1, **rgb**) тест пытался получить `rgb` через `get_map_with_name_ref`, но слой `rgb` не зарегистрирован ни в `layer_names`, ни в `plugin_manager.layer_names`.
- **Исправление**: Убран `rgb` из списка тестируемых слоёв (слой существует только для ввода pointcloud, но не для чтения через `get_map_with_name_ref`).

### 6. `custom_kernels.py:polygon_mask_cpu` — Scalar indexing + 2D vs flat
- **Проблема**: `center_x[0]` падал с `IndexError: invalid index to scalar variable`, т.к. `center_x` — скаляр (numpy float64), а не массив. После исправления индексации — `ValueError: setting an array element with a sequence` из-за доступа к 2D полигону `polygon[j * 2 + 0]` (ожидался плоский массив, но приходит 2D (N,2)).
- **Исправление**: `center_x[0]` → `center_x` (и для `center_y`, `polygon_n`); `polygon[j * 2 + 0]` → `polygon[j, 0]` (и для y).

### 7. Environment: matplotlib/numpy 2.x incompatibility
- **Проблема**: `ImportError: numpy.core.multiarray failed to import` — системный matplotlib собран под numpy 1.x, а установлен numpy 2.4.6.
- **Исправление**: `pip install --user --upgrade matplotlib --break-system-packages` установил matplotlib 3.10.9, совместимый с numpy 2.x.

### Итог: 72 passed, 0 failed (было 31 failed)

## References

- [ROS2 Integration Testing Tutorial](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Integration.html)
- [launch_testing GitHub](https://github.com/ros2/launch/tree/rolling/launch_testing)
- [FastDDS Builtin Transports](https://fast-dds.docs.eprosima.com/en/latest/fastdds/transport/transport.html)
- [ROS2 QoS Settings](https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Quality-of-Service-Settings.html)
