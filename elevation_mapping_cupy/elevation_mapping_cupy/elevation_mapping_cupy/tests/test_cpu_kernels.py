import numpy as np
import pytest

from ..backend import GPU_AVAILABLE, xp


class TestCpuKernels:
    def test_polygon_mask_importable(self):
        from ..custom_kernels import polygon_mask_cpu
        assert polygon_mask_cpu is not None

    def test_polygon_mask_basic(self):
        from ..custom_kernels import polygon_mask_cpu
        n = 10
        center_x = 0.0
        center_y = 0.0
        polygon_n = 3
        polygon = xp.array([[-1, -1], [1, -1], [0, 1]], dtype=xp.float32)
        out = xp.zeros((n, n), dtype=xp.float32)
        resolution = 0.2
        result = polygon_mask_cpu(center_x, center_y, polygon_n, polygon, out, resolution)
        assert result.shape == (n, n)
