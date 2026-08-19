.. _tutorial:

Tutorial
******************************************************************

Golden-path demo (synthetic TF + synthetic PointCloud2)
==================================================================

The demo starts:

* a deterministic TF publisher (``map -> base_link`` moving in a square)
* a deterministic depth-like pointcloud publisher on ``/camera/depth/points``
* the elevation mapping node

Run it (headless):

.. code-block:: bash

  ros2 launch elevation_mapping_cupy synthetic_depth_demo.launch.py launch_rviz:=false

Expected ROS interfaces:

* TF: ``map -> base_link``
* PointCloud2: ``/camera/depth/points``
* GridMap: ``/elevation_mapping_node/elevation_map``

Tip: if you run ``ros2 topic echo`` from a *second* container, set
``FASTDDS_BUILTIN_TRANSPORTS=UDPv4`` to avoid FastDDS shared-memory issues between containers.


Robot Config Launch (e.g. Menzi)
==================================================================

The generic launch file loads ``config/core/core_param.yaml`` and a setup YAML from
``config/setups/<robot_config>``:

.. code-block:: bash

  ros2 launch elevation_mapping_cupy elevation_mapping.launch.py robot_config:=menzi/base.yaml

