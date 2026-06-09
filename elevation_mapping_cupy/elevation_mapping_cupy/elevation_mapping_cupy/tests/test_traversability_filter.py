import numpy as np
import pytest

from ..backend import xp


class TestTraversabilityFilter:
    def test_importable(self):
        from ..traversability_filter import TraversabilityFilter
        assert TraversabilityFilter is not None

    def test_init_default(self):
        from ..traversability_filter import TraversabilityFilter
        tf = TraversabilityFilter()
        assert hasattr(tf, "compute_traversability")

    def test_call_returns_array(self):
        from ..traversability_filter import TraversabilityFilter
        tf = TraversabilityFilter()
        n = 10
        elevation = xp.random.randn(n, n).astype(xp.float32)
        variance = xp.ones((n, n), dtype=xp.float32) * 0.01
        is_valid = xp.ones((n, n), dtype=xp.float32)
        result = tf(elevation, variance, is_valid)
        assert result.shape == (n, n)
        assert xp.all(result >= 0.0)
