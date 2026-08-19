import numpy as np
import pytest

from ..backend import GPU_AVAILABLE, xp


class TestCpuKernels:
    def test_polygon_mask_importable(self):
        from ..kernels.custom_kernels import _make_polygon_mask_cpu

        kernel = _make_polygon_mask_cpu(10, 10, 0.2)
        assert kernel is not None

    def test_polygon_mask_basic(self):
        from ..kernels.custom_kernels import polygon_mask_kernel

        n = 10
        center_x = 0.0
        center_y = 0.0
        polygon_n = 3
        polygon = xp.array([[-1, -1], [1, -1], [0, 1]], dtype=xp.float32)
        polygon_bbox = xp.array([-1.0, -1.0, 1.0, 1.0], dtype=xp.float32)
        out = xp.zeros((n, n), dtype=xp.float32)
        resolution = 0.2
        kernel = polygon_mask_kernel(n, n, resolution)
        kernel(polygon, center_x, center_y, polygon_n, polygon_bbox, out)
        assert out.shape == (n, n)
        assert xp.any(out > 0)
