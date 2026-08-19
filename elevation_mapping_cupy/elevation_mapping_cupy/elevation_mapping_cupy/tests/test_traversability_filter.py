import numpy as np
import pytest

from ..backend import xp


class TestTraversabilityFilter:
    def test_importable(self):
        from ..traversability_filter import get_filter_numpy

        assert get_filter_numpy is not None

    def test_init_default(self):
        from ..parameter import Parameter
        from ..traversability_filter import get_filter_numpy

        param = Parameter()
        tf = get_filter_numpy(param.w1, param.w2, param.w3, param.w_out)
        assert callable(tf)

    def test_call_returns_array(self):
        from ..parameter import Parameter
        from ..traversability_filter import get_filter_numpy

        param = Parameter()
        tf = get_filter_numpy(param.w1, param.w2, param.w3, param.w_out)
        n = 20
        elevation = xp.random.randn(n, n).astype(xp.float32)
        result = tf(elevation)
        assert result.shape == (n - 6, n - 6)
        assert xp.all(result >= 0.0)
