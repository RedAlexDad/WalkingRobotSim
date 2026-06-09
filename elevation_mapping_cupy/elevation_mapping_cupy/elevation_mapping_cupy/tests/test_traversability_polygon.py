import numpy as np
import pytest

from ..backend import xp


class TestGetMaskedTraversability:
    def test_basic(self):
        from ..traversability_polygon import get_masked_traversability

        n = 7
        map_array = xp.zeros((3, n, n), dtype=xp.float32)
        map_array[2] = 1.0
        traversability = xp.ones((n, n), dtype=xp.float32) * 0.8
        mask = xp.ones((n, n), dtype=xp.float32)

        masked, masked_isvalid = get_masked_traversability(
            map_array, mask, traversability
        )
        assert masked.shape == (n - 2, n - 2)
        assert masked_isvalid.shape == (n - 2, n - 2)

    def test_untraversable_cells(self):
        from ..traversability_polygon import get_masked_traversability

        n = 7
        map_array = xp.zeros((3, n, n), dtype=xp.float32)
        map_array[2] = 1.0
        traversability = xp.zeros((n, n), dtype=xp.float32)
        mask = xp.ones((n, n), dtype=xp.float32)

        masked, _ = get_masked_traversability(map_array, mask, traversability)
        expected = 1 - traversability[1:-1, 1:-1]
        assert xp.allclose(masked, expected)


class TestIsTraversable:
    def test_traversable(self):
        from ..traversability_polygon import is_traversable

        arr = xp.zeros((10, 10), dtype=xp.float32)
        safe, poly = is_traversable(arr, thresh=0.5, min_thresh=0.3, max_over_n=5)
        assert safe is True

    def test_untraversable_too_many_over_thresh(self):
        from ..traversability_polygon import is_traversable

        arr = xp.ones((10, 10), dtype=xp.float32) * 0.9
        safe, poly = is_traversable(arr, thresh=0.5, min_thresh=0.3, max_over_n=5)
        assert safe is False

    def test_untraversable_max_exceeds_thresh(self):
        from ..traversability_polygon import is_traversable

        arr = xp.ones((10, 10), dtype=xp.float32) * 0.9
        safe, poly = is_traversable(arr, thresh=0.5, min_thresh=0.3, max_over_n=100)
        assert safe is False


class TestCalculateArea:
    def test_triangle(self):
        from ..traversability_polygon import calculate_area

        poly = np.array([[0, 0], [3, 0], [0, 4]])
        area = calculate_area(poly)
        assert area == pytest.approx(6.0)

    def test_square(self):
        from ..traversability_polygon import calculate_area

        poly = np.array([[0, 0], [2, 0], [2, 2], [0, 2]])
        area = calculate_area(poly)
        assert area == pytest.approx(4.0)


class TestCalculateUntraversablePolygon:
    def test_no_points_returns_none(self):
        from ..traversability_polygon import calculate_untraversable_polygon

        arr = xp.zeros((10, 10), dtype=xp.float32)
        result = calculate_untraversable_polygon(arr)
        assert result is None

    def test_single_point_returns_none(self):
        from ..traversability_polygon import calculate_untraversable_polygon

        arr = xp.zeros((10, 10), dtype=xp.float32)
        arr[5, 5] = 1.0
        result = calculate_untraversable_polygon(arr)
        assert result is None

    def test_cluster_returns_polygon(self):
        from ..traversability_polygon import calculate_untraversable_polygon

        arr = xp.zeros((10, 10), dtype=xp.float32)
        arr[2:5, 2:5] = 1.0
        result = calculate_untraversable_polygon(arr)
        assert result is not None
        assert len(result) >= 4


class TestTransformToMapPosition:
    def test_basic(self):
        from ..traversability_polygon import transform_to_map_position

        polygon = xp.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=xp.float32)
        center = xp.array([1.0, 2.0], dtype=xp.float32)
        result = transform_to_map_position(polygon, center, cell_n=10.0, resolution=0.1)
        assert result.shape == (3, 2)

    def test_identity(self):
        from ..traversability_polygon import transform_to_map_position

        polygon = xp.array([[5.0, 5.0]], dtype=xp.float32)
        center = xp.array([0.0, 0.0], dtype=xp.float32)
        result = transform_to_map_position(polygon, center, cell_n=10.0, resolution=1.0)
        expected = center + (polygon - 5.0) * 1.0
        assert xp.allclose(result, expected)


class TestTransformToMapIndex:
    def test_basic(self):
        from ..traversability_polygon import transform_to_map_index

        points = xp.array([[0.0, 0.0], [1.0, 0.0]], dtype=xp.float32)
        center = xp.array([0.0, 0.0], dtype=xp.float32)
        indices = transform_to_map_index(points, center, cell_n=10.0, resolution=0.1)
        assert indices.shape == (2, 2)
        assert indices.dtype == xp.int32

    def test_center_point(self):
        from ..traversability_polygon import transform_to_map_index

        points = xp.array([[0.0, 0.0]], dtype=xp.float32)
        center = xp.array([0.0, 0.0], dtype=xp.float32)
        indices = transform_to_map_index(points, center, cell_n=10.0, resolution=1.0)
        assert xp.allclose(indices, xp.array([[5, 5]], dtype=xp.int32))
