import numpy as np
import pytest

from ..backend import xp


class TestMapInitializer:
    def test_importable(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        assert m is not None

    def test_default_constructor(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        assert m.initial_variance == 100.0
        assert m.new_variance == 10.0
        assert m.method == "points"
        assert m.xp is np

    def test_custom_xp(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(50.0, 5.0, xp=xp)
        assert m.initial_variance == 50.0
        assert m.new_variance == 5.0
        assert m.xp is xp

    def test_invalid_method_raises(self):
        from ..map_initializer import MapInitializer

        with pytest.raises(AssertionError):
            MapInitializer(100.0, 10.0, method="invalid")

    def test_call_with_unsupported_method_returns_none(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        m.method = "something_else"
        result = m(
            xp.zeros((4, 5, 5), dtype=xp.float32),
            xp.zeros((0, 3), dtype=xp.float32),
        )
        assert result is None

    def test_points_initializer_linear(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        em = xp.zeros((4, 10, 10), dtype=xp.float32)
        em[2, 2:5, 2:5] = 1.0
        em[0, 2:5, 2:5] = 0.5

        points = xp.array([[0, 0, 0.2], [9, 0, 0.2], [0, 9, 0.2]], dtype=xp.float32)
        m(em, points, method="linear")

        assert em[2].any()
        assert em[0].shape == (10, 10)

    def test_points_initializer_nearest(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        em = xp.zeros((4, 10, 10), dtype=xp.float32)
        em[2, 2:5, 2:5] = 1.0
        em[0, 2:5, 2:5] = 0.5

        points = xp.array([[0, 0, 0.2], [9, 0, 0.2], [0, 9, 0.2]], dtype=xp.float32)
        m(em, points, method="nearest")

        assert em[2].any()
        assert em[0].shape == (10, 10)

    def test_points_initializer_cubic(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        em = xp.zeros((4, 10, 10), dtype=xp.float32)
        em[2, 2:5, 2:5] = 1.0
        em[0, 2:5, 2:5] = 0.5

        points = xp.array([[0, 0, 0.2], [9, 0, 0.2], [0, 9, 0.2]], dtype=xp.float32)
        m(em, points, method="cubic")

        assert em[2].any()
        assert em[0].shape == (10, 10)

    def test_variance_set_correctly(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        em = xp.zeros((4, 10, 10), dtype=xp.float32)
        em[2, 2:5, 2:5] = 1.0
        em[0, 2:5, 2:5] = 0.5

        points = xp.array([[0, 0, 0.2], [9, 0, 0.2], [0, 9, 0.2]], dtype=xp.float32)
        m(em, points, method="linear")

        assert xp.any(em[1] == 10.0) or xp.any(em[1] == 100.0)

    def test_is_valid_set_correctly(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        em = xp.zeros((4, 10, 10), dtype=xp.float32)
        em[2, 2:5, 2:5] = 1.0
        em[0, 2:5, 2:5] = 0.5

        points = xp.array([[0, 0, 0.2], [9, 0, 0.2], [0, 9, 0.2]], dtype=xp.float32)
        m(em, points, method="linear")

        assert xp.any(em[2] > 0.5)

    def test_insufficient_points_raises(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        em = xp.zeros((4, 10, 10), dtype=xp.float32)
        em[2, :] = 0.0

        points = xp.array([[0, 0, 0.2], [1, 1, 0.3]], dtype=xp.float32)
        with pytest.raises(AssertionError):
            m(em, points)

    def test_no_valid_cells_in_map(self):
        from ..map_initializer import MapInitializer

        m = MapInitializer(100.0, 10.0)
        em = xp.zeros((4, 10, 10), dtype=xp.float32)

        points = xp.array([[0, 0, 0.2], [9, 0, 0.2], [0, 9, 0.2], [9, 9, 0.2]], dtype=xp.float32)
        m(em, points, method="linear")

        assert em[0].shape == (10, 10)
