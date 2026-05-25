##################################################
Elevation Mapping CuPy (ROS 2 Jazzy)
##################################################

This repository contains:

* ``elevation_map_msgs``: message/service definitions (ament_cmake).
* ``elevation_mapping_cupy``: GPU-accelerated elevation mapping node (Python, CuPy).


Supported Surface (Regression-Tested)
-------------------------------------

This Jazzy branch intentionally keeps the supported surface small and deterministic:

* ``sensor_msgs/msg/PointCloud2`` input only.
* One golden-path bring-up:

  * synthetic TF (``map -> base_link``) + synthetic depth-like pointcloud
  * ``elevation_mapping_node.py`` publishes ``grid_map_msgs/msg/GridMap``
  * optional RViz config to visually verify that the map shifts correctly with robot motion

Everything under ``elevation_mapping_cupy/config/experimental`` and
``elevation_mapping_cupy/launch/experimental`` is unverified.

The legacy plane segmentation stack lives under ``plane_segmentation/`` but is disabled by default
(``COLCON_IGNORE``) because it has heavy dependencies and is not part of the supported bring-up path.


Quick Start (Docker)
--------------------

See the repo-level ``README.md`` for the exact commands (Docker build, ``colcon build``, ``colcon test``,
and running the synthetic demo).


Citing
------

If you use Elevation Mapping CuPy, please cite:

* Elevation Mapping for Locomotion and Navigation using GPU (`arXiv:2204.12876 <https://arxiv.org/abs/2204.12876>`_)

.. code-block::

    @misc{mikielevation2022,
        doi = {10.48550/ARXIV.2204.12876},
        author = {Miki, Takahiro and Wellhausen, Lorenz and Grandia, Ruben and Jenelten, Fabian and Homberger, Timon and Hutter, Marco},
        title = {Elevation Mapping for Locomotion and Navigation using GPU},
        publisher = {International Conference on Intelligent Robots and Systems (IROS)},
        year = {2022},
    }
