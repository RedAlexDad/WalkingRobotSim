.. _installation:

Installation
******************************************************************

This repository targets:

* ROS 2 Jazzy (Ubuntu 24.04)
* NVIDIA GPU + CUDA (CuPy kernels)

The recommended setup is Docker, because it pins a known-good ROS/CUDA/Python environment.


Docker (Recommended)
==================================================================

Build the image:

.. code-block:: bash

  cd <your_ros2_ws>/src/elevation_mapping_cupy
  docker build -f docker/Dockerfile.x64 -t elevation_mapping_cupy:jazzy .

Build + test the packages inside a mounted workspace:

.. code-block:: bash

  docker run --rm --gpus all --net=host \
    -v <your_ros2_ws>:/ws -w /ws elevation_mapping_cupy:jazzy bash -lc '
      set -e
      source /opt/ros/jazzy/setup.bash
      colcon build --symlink-install \
        --build-base build_jazzy --install-base install_jazzy \
        --packages-select elevation_map_msgs elevation_mapping_cupy
      source install_jazzy/setup.bash
      colcon test --packages-select elevation_mapping_cupy \
        --build-base build_jazzy --install-base install_jazzy \
        --event-handlers console_direct+
      colcon test-result --verbose --test-result-base build_jazzy
    '


Native (Not Recommended)
==================================================================

Native installs are possible, but you must provide CUDA-capable Python wheels yourself
(CuPy + torch) and ensure your ROS 2 Jazzy environment has the required ROS/system dependencies.
