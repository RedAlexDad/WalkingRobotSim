import numpy as np
import pytest

from ..backend import GPU_AVAILABLE, xp
from ..plugins.cost_function import CostFunction
from ..plugins.erosion import Erosion
from ..plugins.inpainting import Inpainting
from ..plugins.max_filter import MaxFilter
from ..plugins.max_layer_filter import MaxLayerFilter
from ..plugins.min_filter import MinFilter
from ..plugins.robot_centric_elevation import RobotCentricElevation
from ..plugins.roughness import Roughness
from ..plugins.smooth_filter import SmoothFilter
from ..plugins.surface_gradient import SurfaceGradient


@pytest.fixture
def elevation_map():
    n = 20
    em = xp.zeros((7, n, n), dtype=xp.float32)
    em[0] = xp.random.randn(n, n).astype(xp.float32) * 0.1
    em[1] = xp.ones((n, n), dtype=xp.float32) * 0.01
    em[2] = xp.ones((n, n), dtype=xp.float32)
    em[3] = xp.ones((n, n), dtype=xp.float32) * 0.8
    em[4] = xp.zeros((n, n), dtype=xp.float32)
    em[5] = xp.ones((n, n), dtype=xp.float32) * 0.5
    em[6] = xp.ones((n, n), dtype=xp.float32)
    return em


@pytest.fixture
def layer_names():
    return [
        "elevation",
        "variance",
        "is_valid",
        "traversability",
        "time",
        "upper_bound",
        "is_upper_bound",
    ]


@pytest.fixture
def plugin_layers(layer_names):
    n = 20
    return xp.zeros((0, n, n), dtype=xp.float32), []


@pytest.fixture
def semantic_map():
    n = 20
    sm = xp.zeros((2, n, n), dtype=xp.float32)
    sm[0] = xp.random.randn(n, n).astype(xp.float32)
    sm[1] = xp.random.randn(n, n).astype(xp.float32)
    return sm, ["class_0", "class_1"]


@pytest.fixture
def rotation():
    return xp.eye(3, dtype=xp.float32)


class TestSmoothFilter:
    def test_init_default(self):
        sf = SmoothFilter()
        assert sf.input_layer_name == "elevation"

    def test_init_custom(self):
        sf = SmoothFilter(cell_n=50, input_layer_name="inpaint")
        assert sf.input_layer_name == "inpaint"

    def test_call_from_elevation(self, elevation_map, layer_names, plugin_layers):
        sf = SmoothFilter(cell_n=20)
        result = sf(elevation_map, layer_names, *plugin_layers)
        assert result.shape == (20, 20)
        assert not xp.any(xp.isnan(result))

    def test_call_from_plugin_layer(self, elevation_map, layer_names):
        n = 20
        sf = SmoothFilter(cell_n=n, input_layer_name="test_layer")
        pl = xp.zeros((1, n, n), dtype=xp.float32)
        pl[0] = xp.random.randn(n, n).astype(xp.float32)
        result = sf(elevation_map, layer_names, pl, ["test_layer"])
        assert result.shape == (n, n)

    def test_call_fallback_to_elevation(self, elevation_map, layer_names, plugin_layers):
        sf = SmoothFilter(cell_n=20, input_layer_name="missing_layer")
        result = sf(elevation_map, layer_names, *plugin_layers)
        assert result.shape == (20, 20)

    def test_output_is_smoothed(self):
        n = 20
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0, 5:15, 5:15] = 1.0
        em[0, 0:5, 0:5] = 0.0
        em[2] = 1.0
        layer_names = [
            "elevation",
            "variance",
            "is_valid",
            "traversability",
            "time",
            "upper_bound",
            "is_upper_bound",
        ]
        sf = SmoothFilter(cell_n=n)
        result = sf(em, layer_names, xp.zeros((0, n, n)), [])
        assert float(result[5, 5]) < 1.0


class TestRoughness:
    def test_init_default(self):
        r = Roughness()
        assert r.input_layer_name == "inpaint"
        assert r.window_size == 5

    def test_call_returns_finite(self, elevation_map, layer_names, plugin_layers):
        r = Roughness(cell_n=20, input_layer_name="elevation")
        result = r(elevation_map, layer_names, *plugin_layers)
        assert result.shape == (20, 20)
        assert xp.all(xp.isfinite(result))

    def test_call_from_plugin(self, elevation_map, layer_names):
        n = 20
        r = Roughness(cell_n=n, input_layer_name="test_layer")
        pl = xp.zeros((1, n, n), dtype=xp.float32)
        pl[0] = xp.random.randn(n, n).astype(xp.float32) * 0.5
        result = r(elevation_map, layer_names, pl, ["test_layer"])
        assert result.shape == (n, n)

    def test_call_fallback(self, elevation_map, layer_names, plugin_layers):
        r = Roughness(cell_n=20, input_layer_name="missing")
        result = r(elevation_map, layer_names, *plugin_layers)
        assert result.shape == (20, 20)

    def test_roughness_of_constant_terrain_is_zero(self):
        n = 20
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0] = 0.5
        em[2] = 1.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        r = Roughness(cell_n=n, input_layer_name="elevation", window_size=5)
        result = r(em, lnames, xp.zeros((0, n, n)), [])
        assert xp.max(result) < 1e-5


class TestSurfaceGradient:
    def test_init_default(self):
        sg = SurfaceGradient()
        assert sg.input_layer_name == "inpaint"

    def test_call_returns_slope(self, elevation_map, layer_names, plugin_layers):
        sg = SurfaceGradient(cell_n=20, input_layer_name="elevation")
        result = sg(elevation_map, layer_names, *plugin_layers)
        assert result.shape == (20, 20)
        assert xp.all(xp.isfinite(result))

    def test_flat_terrain_zero_slope(self):
        n = 20
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0] = 0.5
        em[2] = 1.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        sg = SurfaceGradient(cell_n=n, input_layer_name="elevation")
        result = sg(em, lnames, xp.zeros((0, n, n)), [])
        assert xp.max(result) < 1e-5


class TestCostFunction:
    def test_init_default(self):
        cf = CostFunction()
        assert cf.w_slope == 0.4
        assert cf.w_roughness == 0.4
        assert cf.w_elevation == 0.2

    def test_call_returns_cost(self, elevation_map, layer_names, plugin_layers):
        cf = CostFunction(cell_n=20)
        result = cf(elevation_map, layer_names, *plugin_layers)
        assert result.shape == (20, 20)
        assert xp.all(result >= 0.0)
        assert xp.all(result <= 1.0)

    def test_cost_one_for_perfect_terrain(self):
        n = 20
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0] = 0.5
        em[2] = 1.0
        em[3] = 1.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        pl = xp.zeros((2, n, n), dtype=xp.float32)
        pl[0] = 0.0
        pl[1] = 0.0
        cf = CostFunction(cell_n=n, slope_layer_name="slope", roughness_layer_name="roughness")
        result = cf(em, lnames, pl, ["slope", "roughness"])
        assert xp.allclose(result, 1.0, atol=1e-5)

    def test_missing_slope_layer_fallback(self, elevation_map, layer_names):
        n = 20
        cf = CostFunction(cell_n=n, slope_layer_name="missing_slope", roughness_layer_name="missing_roughness")
        result = cf(elevation_map, layer_names, xp.zeros((0, n, n)), [])
        assert result.shape == (n, n)


class TestErosion:
    def test_init_default(self):
        e = Erosion()
        assert e.kernel_size == 3
        assert e.iterations == 1

    def test_call_from_layer(self, elevation_map, layer_names, semantic_map):
        n = 20
        e = Erosion(cell_n=n, input_layer_name="traversability")
        result = e(elevation_map, layer_names, xp.zeros((0, n, n)), [], *semantic_map)
        assert result.shape == (n, n)

    def test_call_with_reverse(self, elevation_map, layer_names, semantic_map):
        n = 20
        e = Erosion(cell_n=n, input_layer_name="traversability", reverse=True)
        result = e(elevation_map, layer_names, xp.zeros((0, n, n)), [], *semantic_map)
        assert result.shape == (n, n)

    def test_call_fallback_default(self, elevation_map, layer_names, semantic_map):
        n = 20
        e = Erosion(cell_n=n, input_layer_name="missing", default_layer_name="traversability")
        result = e(elevation_map, layer_names, xp.zeros((0, n, n)), [], *semantic_map)
        assert result.shape == (n, n)

    def test_call_fallback_traversability(self, elevation_map, layer_names, semantic_map):
        n = 20
        e = Erosion(cell_n=n, input_layer_name="missing", default_layer_name="also_missing")
        result = e(elevation_map, layer_names, xp.zeros((0, n, n)), [], *semantic_map)
        assert result.shape == (n, n)

    def test_call_from_plugin_layer(self, elevation_map, layer_names, semantic_map):
        n = 20
        e = Erosion(cell_n=n, input_layer_name="plugin_layer")
        pl = xp.ones((1, n, n), dtype=xp.float32) * 0.5
        result = e(elevation_map, layer_names, pl, ["plugin_layer"], *semantic_map)
        assert result.shape == (n, n)

    def test_erosion_reduces_traversability(self):
        n = 20
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[3] = 0.0
        em[3, 5:15, 5:15] = 1.0
        em[2] = 1.0
        em[0] = 0.5
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        e = Erosion(cell_n=n, input_layer_name="traversability", kernel_size=3, iterations=1)
        result = e(em, lnames, xp.zeros((0, n, n)), [], xp.zeros((0, n, n)), [])
        before = xp.count_nonzero(em[3] > 0.5)
        after = xp.count_nonzero(result > 0.5)
        assert after <= before


class TestInpainting:
    def test_init_default(self):
        ip = Inpainting()
        assert hasattr(ip, "method")

    def test_init_ns_method(self):
        ip = Inpainting(method="ns")
        import cv2 as cv

        assert ip.method == cv.INPAINT_NS

    def test_call_valid_mask_all_good(self, elevation_map, layer_names, plugin_layers):
        em = elevation_map.copy()
        em[2] = 1.0
        ip = Inpainting(cell_n=20)
        result = ip(em, layer_names, *plugin_layers)
        assert result.shape == (20, 20)
        assert not xp.any(xp.isnan(result))

    def test_call_with_invalid_cells(self, elevation_map, layer_names, plugin_layers):
        em = elevation_map.copy()
        em[2, 5:8, 5:8] = 0.0
        ip = Inpainting(cell_n=20)
        result = ip(em, layer_names, *plugin_layers)
        assert result.shape == (20, 20)

    def test_call_all_invalid_returns_elevation(self):
        n = 20
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0] = xp.random.randn(n, n).astype(xp.float32) * 0.1
        em[2] = 0.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        ip = Inpainting(cell_n=20)
        result = ip(em, lnames, xp.zeros((0, n, n)), [])
        assert xp.allclose(result, em[0])

    def test_near_flat_terrain_handled(self):
        n = 20
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0] = 0.5
        em[2, 5:8, 5:8] = 0.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        ip = Inpainting(cell_n=20)
        result = ip(em, lnames, xp.zeros((0, n, n)), [])
        assert result.shape == (n, n)


class TestMaxFilter:
    def test_init_default(self):
        mf = MaxFilter()
        assert mf.dilation_size == 5
        assert mf.iteration_n == 5

    def test_cpu_path(self, elevation_map, layer_names):
        if GPU_AVAILABLE:
            pytest.skip("CPU path only testable without GPU")
        mf = MaxFilter(cell_n=20, dilation_size=3, iteration_n=2)
        result = mf(elevation_map, layer_names, xp.zeros((0, 20, 20)), [])
        assert result.shape == (20, 20)

    def test_cpu_all_valid_no_change(self):
        n = 10
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0] = xp.random.randn(n, n).astype(xp.float32) * 0.1
        em[2] = 1.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        mf = MaxFilter(cell_n=n, dilation_size=2, iteration_n=1)
        result = mf(em, lnames, xp.zeros((0, n, n)), [])
        assert xp.allclose(result, em[0], equal_nan=True)

    def test_max_filter_fills_invalid(self):
        n = 10
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0, 2:8, 4:6] = 0.5
        em[0, 5, 5] = 1.0
        em[2] = 0.0
        em[2, 2:8, 4:6] = 1.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        mf = MaxFilter(cell_n=n, dilation_size=2, iteration_n=3)
        result = mf(em, lnames, xp.zeros((0, n, n)), [])
        assert not xp.all(xp.isnan(result))


class TestMinFilter:
    def test_init_default(self):
        mf = MinFilter()
        assert mf.dilation_size == 5
        assert mf.iteration_n == 5

    def test_cpu_path(self, elevation_map, layer_names):
        if GPU_AVAILABLE:
            pytest.skip("CPU path only testable without GPU")
        mf = MinFilter(cell_n=20, dilation_size=3, iteration_n=2)
        result = mf(elevation_map, layer_names, xp.zeros((0, 20, 20)), [])
        assert result.shape == (20, 20)

    def test_min_filter_fills_invalid(self):
        n = 10
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0, 2:8, 4:6] = 0.5
        em[0, 5, 5] = 0.1
        em[2] = 0.0
        em[2, 2:8, 4:6] = 1.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        mf = MinFilter(cell_n=n, dilation_size=2, iteration_n=3)
        result = mf(em, lnames, xp.zeros((0, n, n)), [])
        assert not xp.all(xp.isnan(result))


class TestMaxLayerFilter:
    def test_init_default(self):
        mlf = MaxLayerFilter()
        assert mlf.min_or_max == "max"
        assert mlf.default_value == 0.0

    def test_call_max_multiple_layers(self, elevation_map, layer_names, semantic_map):
        n = 20
        pl = xp.zeros((2, n, n), dtype=xp.float32)
        pl[0] = 0.3
        pl[1] = 0.7
        mlf = MaxLayerFilter(
            cell_n=n,
            layers=["layer_a", "layer_b"],
            min_or_max="max",
        )
        result = mlf(elevation_map, layer_names, pl, ["layer_a", "layer_b"], *semantic_map)
        assert result.shape == (n, n)

    def test_call_min(self, elevation_map, layer_names, semantic_map):
        n = 20
        pl = xp.zeros((2, n, n), dtype=xp.float32)
        pl[0] = 0.1
        pl[1] = 0.9
        mlf = MaxLayerFilter(
            cell_n=n,
            layers=["layer_a", "layer_b"],
            min_or_max="min",
            reverse=[],
        )
        result = mlf(elevation_map, layer_names, pl, ["layer_a", "layer_b"], *semantic_map)
        assert float(result[0, 0]) == pytest.approx(0.1, abs=1e-5)

    def test_call_with_reverse_and_threshold(self, elevation_map, layer_names, semantic_map):
        n = 20
        pl = xp.zeros((1, n, n), dtype=xp.float32)
        pl[0] = 0.7
        mlf = MaxLayerFilter(
            cell_n=n,
            layers=["test_layer"],
            reverse=[True],
            thresholds=[0.5],
            scales=[1.0],
        )
        result = mlf(elevation_map, layer_names, pl, ["test_layer"], *semantic_map)
        assert xp.all(result >= 0.0)

    def test_no_layers_found_float_default(self, elevation_map, layer_names, semantic_map):
        n = 20
        mlf = MaxLayerFilter(
            cell_n=n,
            layers=["missing"],
            default_value=0.5,
        )
        result = mlf(elevation_map, layer_names, xp.zeros((0, n, n)), [], *semantic_map)
        assert xp.allclose(result, 0.5)

    def test_no_layers_found_string_default(self, elevation_map, layer_names, semantic_map):
        n = 20
        mlf = MaxLayerFilter(
            cell_n=n,
            layers=["missing"],
            default_value="traversability",
        )
        result = mlf(elevation_map, layer_names, xp.zeros((0, n, n)), [], *semantic_map)
        assert result.shape == (n, n)

    def test_layer_with_default_value_float(self, elevation_map, layer_names, semantic_map):
        n = 20
        pl = xp.zeros((1, n, n), dtype=xp.float32)
        pl[0, 5, 5] = 0.0
        mlf = MaxLayerFilter(
            cell_n=n,
            layers=["test_layer"],
            default_value=0.5,
        )
        result = mlf(elevation_map, layer_names, pl, ["test_layer"], *semantic_map)
        assert float(result[5, 5]) == 0.5


class TestRobotCentricElevation:
    def test_init_default(self):
        rce = RobotCentricElevation()
        assert rce.use_threshold is False

    def test_cpu_path(self, elevation_map, layer_names, rotation):
        if GPU_AVAILABLE:
            pytest.skip("CPU path only testable without GPU")
        rce = RobotCentricElevation(cell_n=20, resolution=0.05)
        result = rce(elevation_map, layer_names, xp.zeros((0, 20, 20)), [], xp.zeros((0, 20, 20)), [], rotation)
        assert result.shape == (20, 20)

    def test_with_threshold_cpu(self, elevation_map, layer_names, rotation):
        if GPU_AVAILABLE:
            pytest.skip("CPU path only testable without GPU")
        rce = RobotCentricElevation(cell_n=20, resolution=0.05, threshold=0.4, use_threshold=1)
        result = rce(elevation_map, layer_names, xp.zeros((0, 20, 20)), [], xp.zeros((0, 20, 20)), [], rotation)
        assert result.shape == (20, 20)
        assert xp.all((result == 0.0) | (result == 1.0) | (result > 0.0))

    def test_identity_rotation_preserves_z(self, rotation):
        n = 10
        em = xp.zeros((7, n, n), dtype=xp.float32)
        em[0] = xp.ones((n, n), dtype=xp.float32) * 0.5
        em[2] = 1.0
        lnames = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        rce = RobotCentricElevation(cell_n=n, resolution=1.0)
        result = rce(em, lnames, xp.zeros((0, n, n)), [], xp.zeros((0, n, n)), [], rotation)
        assert result.shape == (n, n)
