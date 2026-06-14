.. _cuda_installation:

CUDA Setup Notes
******************************************************************

This Jazzy branch is tested via the provided Docker image (Ubuntu 24.04 + ROS 2 Jazzy + CUDA base).

If you want to run natively (not recommended), you need:

* a recent NVIDIA driver on the host
* a CUDA-capable CuPy wheel (e.g. ``cupy-cuda12x``)
* a matching torch installation (CUDA wheels vary by CUDA/driver)

For most users, using Docker is the simplest path.
