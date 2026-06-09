from pathlib import Path

import numpy as np
import pytest

from .. import elevation_mapping, parameter
from ..backend import xp
from ..elevation_mapping import GridGeometry

_TEST_DIR = Path(__file__).parent
_CONFIG_DIR = _TEST_DIR.parent.parent / "config" / "core"


def encode_max(maxim, index):
    maxim, index = xp.asarray(maxim, dtype=xp.float32), xp.asarray(index, dtype=xp.uint32)
    maxim = maxim.astype(xp.float16)
    maxim = maxim.view(xp.uint16)
    maxim = maxim.astype(xp.uint32)
    index = index.astype(xp.uint32)
    mer = xp.array(xp.left_shift(index, 16) | maxim, dtype=xp.uint32)
    mer = mer.view(xp.float32)
    return mer


@pytest.fixture()
def elmap_ex(add_lay, fusion_alg):
    additional_layer = add_lay
    fusion_algorithms = fusion_alg
    p = parameter.Parameter(
        use_chainer=False,
        weight_file=str(_CONFIG_DIR / "weights.dat"),
        plugin_config_file=str(_CONFIG_DIR / "plugin_config.yaml"),
    )
    p.subscriber_cfg["front_cam"]["channels"] = additional_layer
    p.subscriber_cfg["front_cam"]["fusion"] = fusion_algorithms
    p.additional_layers = additional_layer
    p.update()
    e = elevation_mapping.ElevationMap(p)
    return e


@pytest.mark.parametrize(
    "add_lay,fusion_alg",
    [
        (["feat_0", "feat_1", "rgb"], ["average", "average", "color"]),
        (["feat_0", "feat_1"], ["average", "average"]),
        (["feat_0", "feat_1"], ["class_average", "class_average"]),
        (["feat_0", "feat_1"], ["class_bayesian", "class_bayesian"]),
        (["feat_0", "feat_1"], ["class_bayesian", "class_max"]),
        (["feat_0", "feat_1"], ["bayesian_inference", "bayesian_inference"]),
    ],
)
class TestElevationMap:
    def test_init(self, elmap_ex):
        assert len(elmap_ex.layer_names) == elmap_ex.elevation_map.shape[0]

    def test_input(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.random.rand(100000, len(channels)).astype(xp.float16)
            ind = xp.random.randint(0, 2, size=(100000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(100000, len(channels)).astype(elmap_ex.param.data_type)
        R = xp.random.rand(3, 3).astype(elmap_ex.param.data_type)
        t = xp.random.rand(3).astype(elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)

    def test_update_normal(self, elmap_ex):
        elmap_ex.update_normal(elmap_ex.elevation_map[0])

    def test_move_to(self, elmap_ex):
        for i in range(20):
            pos = np.array([i * 0.01, i * 0.02, i * 0.01])
            R = xp.random.rand(3, 3)
            elmap_ex.move_to(pos, R)

    def test_get_map(self, elmap_ex):
        layers = [
            "elevation",
            "variance",
            "traversability",
            "min_filter",
            "smooth",
            "inpaint",
        ]
        data = np.zeros((elmap_ex.cell_n - 2, elmap_ex.cell_n - 2), dtype=np.float32)
        for layer in layers:
            elmap_ex.get_map_with_name_ref(layer, data)

    def test_get_position(self, elmap_ex):
        pos = np.random.rand(1, 3)
        elmap_ex.get_position(pos)

    def test_clear(self, elmap_ex):
        elmap_ex.clear()

    def test_move(self, elmap_ex):
        delta_position = np.random.rand(3)
        elmap_ex.move(delta_position)

    def test_exists_layer(self, elmap_ex, add_lay):
        for layer in add_lay:
            assert elmap_ex.exists_layer(layer)

    def test_polygon_traversability(self, elmap_ex):
        polygon = xp.array([[0, 0], [2, 0], [0, 2]], dtype=np.float64)
        result = np.array([0, 0, 0])
        number_polygons = elmap_ex.get_polygon_traversability(polygon, result)
        untraversable_polygon = np.zeros((number_polygons, 2))
        elmap_ex.get_untraversable_polygon(untraversable_polygon)

    def test_initialize_map(self, elmap_ex):
        methods = ["linear", "cubic", "nearest"]
        for method in methods:
            points = np.array([[-4.0, 0.0, 0.0], [-4.0, 8.0, 1.0], [4.0, 8.0, 0.0], [4.0, 0.0, 0.0]])
            elmap_ex.initialize_map(points, method)

    def test_plugins(self, elmap_ex):
        layers = elmap_ex.plugin_manager.layer_names
        data = np.zeros((200, 200), dtype=np.float32)
        for layer in layers:
            elmap_ex.get_map_with_name_ref(layer, data)

    def test_get_center_position(self, elmap_ex):
        pos = np.zeros((1, 3), dtype=np.float64)
        elmap_ex.get_center_position(pos)
        expected = np.asarray(elmap_ex.center)
        assert np.allclose(pos[0], expected)

    def test_get_additive_mean_error(self, elmap_ex):
        err = elmap_ex.get_additive_mean_error()
        assert isinstance(err, float)
        assert err >= 0.0

    def test_shift_map_z(self, elmap_ex):
        z0 = elmap_ex.elevation_map[0].copy()
        ub0 = elmap_ex.elevation_map[5].copy()
        elmap_ex.shift_map_z(0.5)
        assert xp.allclose(elmap_ex.elevation_map[0], z0 + 0.5)
        assert xp.allclose(elmap_ex.elevation_map[5], ub0 + 0.5)

    def test_shift_map_z_negative(self, elmap_ex):
        z0 = elmap_ex.elevation_map[0].copy()
        elmap_ex.shift_map_z(-1.0)
        assert xp.allclose(elmap_ex.elevation_map[0], z0 - 1.0)

    def test_clear_overlap_map(self, elmap_ex):
        elmap_ex.elevation_map[0] = 1.0
        elmap_ex.elevation_map[2] = 1.0
        t = xp.array([0.0, 0.0, 5.0], dtype=xp.float32)
        elmap_ex.clear_overlap_map(t)
        assert xp.any(elmap_ex.elevation_map[2] < 0.5)

    def test_update_upper_bound_with_valid_elevation(self, elmap_ex):
        elmap_ex.elevation_map[0] = 2.0
        elmap_ex.elevation_map[2] = 1.0
        elmap_ex.elevation_map[6] = 1.0
        elmap_ex.update_upper_bound_with_valid_elevation()
        assert xp.allclose(elmap_ex.elevation_map[5][elmap_ex.elevation_map[2] > 0.5], 2.0)
        assert xp.all(elmap_ex.elevation_map[6][elmap_ex.elevation_map[2] > 0.5] < 0.5)

    def test_update_variance_does_not_crash(self, elmap_ex):
        elmap_ex.update_variance()

    def test_update_time(self, elmap_ex):
        t0 = elmap_ex.elevation_map[4].copy()
        elmap_ex.update_time()
        assert xp.any(xp.abs(elmap_ex.elevation_map[4]) >= 0.0)

    def test_get_layer(self, elmap_ex):
        elev = elmap_ex.get_layer("elevation")
        assert elev is not None

    def test_get_layer_variance(self, elmap_ex):
        var = elmap_ex.get_layer("variance")
        assert var is not None

    def test_get_layer_nonexistent(self, elmap_ex):
        result = elmap_ex.get_layer("missing_layer")
        assert result is None

    def test_list_layers(self, elmap_ex):
        names = elmap_ex.list_layers()
        assert "elevation" in names
        assert "variance" in names
        assert "traversability" in names

    def test_export_layers(self, elmap_ex):
        names = ["elevation", "variance"]
        result = elmap_ex.export_layers(names)
        assert isinstance(result, dict)
        assert "elevation" in result
        assert "variance" in result
        arr = result["elevation"]
        assert isinstance(arr, np.ndarray)

    def test_get_normal_maps(self, elmap_ex):
        nm = elmap_ex.get_normal_maps()
        assert nm.shape[0] == 3

    def test_get_normal_ref_does_not_crash(self, elmap_ex):
        maps = elmap_ex.get_normal_maps()
        h, w = maps.shape[1], maps.shape[2]
        nx = np.zeros((h, w), dtype=np.float32)
        ny = np.zeros((h, w), dtype=np.float32)
        nz = np.zeros((h, w), dtype=np.float32)
        elmap_ex.get_normal_ref(nx, ny, nz)

    def test_xp_of_array(self, elmap_ex):
        assert elmap_ex.xp_of_array(xp.array([1, 2, 3])) is xp
        assert elmap_ex.xp_of_array(np.array([1, 2, 3])) is np

    def test_copy_to_cpu(self, elmap_ex):
        src = xp.array([[1.0, 2.0], [3.0, 4.0]], dtype=xp.float32)
        dst = np.zeros((2, 2), dtype=np.float32)
        elmap_ex.copy_to_cpu(src, dst)
        assert np.allclose(dst, [[1.0, 2.0], [3.0, 4.0]])

    def test_process_map_for_publish_add_z(self, elmap_ex):
        layer = xp.ones((200, 200), dtype=xp.float32)
        result = elmap_ex.process_map_for_publish(layer, fill_nan=False, add_z=True)
        assert result.shape == (198, 198)
        assert np.allclose(result[0, 0], 1.0 + float(elmap_ex.center[2]))

    def test_process_map_for_publish_fill_nan(self, elmap_ex):
        layer = xp.ones((200, 200), dtype=xp.float32)
        elmap_ex.elevation_map[2, 0, 0] = 0.0
        result = elmap_ex.process_map_for_publish(layer, fill_nan=True, add_z=False)
        assert np.isnan(result[0, 0])

    def test_transform_to_grid_map(self, elmap_ex):
        m = xp.array([[1, 2, 3], [4, 5, 6]], dtype=xp.float32)
        result = elmap_ex._transform_to_grid_map_coordinate_convention(m)
        back = elmap_ex._transform_to_elevation_mapping_coordinate_convention(result)
        assert xp.allclose(back, m)

    def test_transform_to_elevation_mapping_coordinate(self, elmap_ex):
        m = xp.array([[1, 2, 3], [4, 5, 6]], dtype=xp.float32)
        result = elmap_ex._transform_to_elevation_mapping_coordinate_convention(m)
        back = elmap_ex._transform_to_grid_map_coordinate_convention(result)
        assert xp.allclose(back, m)

    def test_invalidate_caches_does_not_crash(self, elmap_ex):
        elmap_ex._invalidate_caches(reset_plugins=False)

    def test_validate_geometry_against_shape_match(self, elmap_ex):
        n = elmap_ex.cell_n
        res = elmap_ex.resolution
        geom = GridGeometry(
            length_x=n * res, length_y=n * res, resolution=res, center=np.array([0.0, 0.0, 0.0]), orientation=np.eye(3)
        )
        elmap_ex._validate_geometry_against_shape((n, n), geom)

    def test_validate_geometry_against_shape_mismatch(self, elmap_ex):
        n = elmap_ex.cell_n
        res = elmap_ex.resolution
        geom = GridGeometry(
            length_x=n * res, length_y=n * res, resolution=res, center=np.array([0.0, 0.0, 0.0]), orientation=np.eye(3)
        )
        with pytest.raises(ValueError):
            elmap_ex._validate_geometry_against_shape((n + 10, n + 10), geom)

    def test_resolve_layer_target(self, elmap_ex):
        viewed = elmap_ex._resolve_layer_target("elevation")
        assert viewed is not None

    def test_resolve_layer_target_missing(self, elmap_ex):
        viewed = elmap_ex._resolve_layer_target("nonexistent_layer")
        assert viewed is None

    def test_compute_overlap_indices(self, elmap_ex):
        n = elmap_ex.cell_n
        res = elmap_ex.resolution
        geom = GridGeometry(
            length_x=n * res, length_y=n * res, resolution=res, center=np.array([0.0, 0.0, 0.0]), orientation=np.eye(3)
        )
        result = elmap_ex._compute_overlap_indices((n, n), geom)
        assert result is not None
        assert "map" in result
        assert "patch" in result

    def test_input_pointcloud_with_nan_rows(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.random.rand(100000, len(channels)).astype(xp.float16)
            ind = xp.random.randint(0, 2, size=(100000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(100000, len(channels)).astype(elmap_ex.param.data_type)
        points[::5, :] = xp.nan
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        t = xp.zeros(3, dtype=elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)

    def test_input_pointcloud_with_inf_values(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.random.rand(100000, len(channels)).astype(xp.float16)
            ind = xp.random.randint(0, 2, size=(100000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(100000, len(channels)).astype(elmap_ex.param.data_type)
        points[::7, 0] = xp.inf
        points[::11, 1] = -xp.inf
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        t = xp.zeros(3, dtype=elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)

    def test_input_pointcloud_all_nan(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.full((1000, len(channels)), xp.nan, dtype=xp.float16)
            ind = xp.random.randint(0, 2, size=(1000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.full((1000, len(channels)), xp.nan, dtype=elmap_ex.param.data_type)
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        t = xp.zeros(3, dtype=elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)

    def test_full_pipeline_input_to_publish(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.random.rand(50000, len(channels)).astype(xp.float16)
            ind = xp.random.randint(0, 2, size=(50000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(50000, len(channels)).astype(elmap_ex.param.data_type)
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        t = xp.zeros(3, dtype=elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)
        elmap_ex.update_normal(elmap_ex.elevation_map[0])
        elev = elmap_ex.get_layer("elevation")
        assert elev is not None
        published = elmap_ex.process_map_for_publish(elev, fill_nan=False, add_z=True)
        assert published.shape == (elmap_ex.cell_n - 2, elmap_ex.cell_n - 2)

    def test_multiple_pointclouds_sequential(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        for i in range(5):
            if "class_max" in elmap_ex.param.fusion_algorithms:
                val = xp.random.rand(20000, len(channels)).astype(xp.float16)
                ind = xp.random.randint(0, 2, size=(20000, len(channels))).astype(xp.float32)
                points = encode_max(val, ind)
            else:
                points = xp.random.rand(20000, len(channels)).astype(elmap_ex.param.data_type)
            t = xp.array([i * 0.1, i * 0.1, 0.0], dtype=elmap_ex.param.data_type)
            elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)

    def test_large_move_then_input_pointcloud(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        pos = np.array([3.0, 3.0, 1.0])
        angle = np.pi / 6
        R = xp.array([[np.cos(angle), -np.sin(angle), 0],
                       [np.sin(angle), np.cos(angle), 0],
                       [0, 0, 1]], dtype=elmap_ex.param.data_type)
        elmap_ex.move_to(pos, R)
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.random.rand(50000, len(channels)).astype(xp.float16)
            ind = xp.random.randint(0, 2, size=(50000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(50000, len(channels)).astype(elmap_ex.param.data_type)
        t = xp.zeros(3, dtype=elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)

    def test_update_variance_after_multiple_inputs(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        for _ in range(3):
            if "class_max" in elmap_ex.param.fusion_algorithms:
                val = xp.random.rand(20000, len(channels)).astype(xp.float16)
                ind = xp.random.randint(0, 2, size=(20000, len(channels))).astype(xp.float32)
                points = encode_max(val, ind)
            else:
                points = xp.random.rand(20000, len(channels)).astype(elmap_ex.param.data_type)
            t = xp.random.rand(3).astype(elmap_ex.param.data_type)
            elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)
        elmap_ex.update_variance()
        var_layer = elmap_ex.get_layer("variance")
        assert var_layer is not None

    def test_semantic_layers_persist_after_input(self, elmap_ex, add_lay):
        channels = ["x", "y", "z"] + add_lay
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.random.rand(50000, len(channels)).astype(xp.float16)
            ind = xp.random.randint(0, 2, size=(50000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(50000, len(channels)).astype(elmap_ex.param.data_type)
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        t = xp.zeros(3, dtype=elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)
        for layer in add_lay:
            if elmap_ex.exists_layer(layer):
                _ = elmap_ex.get_layer(layer)

    def test_clear_overlap_after_large_z_shift(self, elmap_ex):
        elmap_ex.elevation_map[0] = 2.0
        elmap_ex.elevation_map[2] = 1.0
        t = xp.array([0.0, 0.0, 10.0], dtype=xp.float32)
        elmap_ex.clear_overlap_map(t)
        assert xp.any(elmap_ex.elevation_map[2] < 0.5)

    def test_shift_map_xy_preserves_invariants(self, elmap_ex):
        z0 = elmap_ex.elevation_map[0].copy()
        elmap_ex.shift_map_xy(xp.array([5, 3]))
        assert elmap_ex.elevation_map[0].shape == z0.shape

    def test_shift_map_z_large_negative(self, elmap_ex):
        elmap_ex.shift_map_z(-100.0)
        assert xp.allclose(elmap_ex.elevation_map[0], -100.0)

    def test_process_map_for_publish_all_nan(self, elmap_ex):
        layer = xp.full((200, 200), xp.nan, dtype=xp.float32)
        result = elmap_ex.process_map_for_publish(layer, fill_nan=True, add_z=False)
        assert result.shape == (198, 198)
        assert xp.all(xp.isnan(result))

    def test_process_map_for_publish_all_zero(self, elmap_ex):
        layer = xp.zeros((200, 200), dtype=xp.float32)
        result = elmap_ex.process_map_for_publish(layer, fill_nan=False, add_z=True)
        assert result.shape == (198, 198)
        assert xp.allclose(result, float(elmap_ex.center[2]))

    def test_get_elevation_and_variance_together(self, elmap_ex):
        elev = elmap_ex.get_elevation()
        var = elmap_ex.get_variance()
        assert elev.shape == var.shape

    def test_map_after_clear_then_input(self, elmap_ex):
        channels = ["x", "y", "z"] + elmap_ex.param.additional_layers
        R = xp.eye(3, dtype=elmap_ex.param.data_type)
        t = xp.zeros(3, dtype=elmap_ex.param.data_type)
        if "class_max" in elmap_ex.param.fusion_algorithms:
            val = xp.random.rand(30000, len(channels)).astype(xp.float16)
            ind = xp.random.randint(0, 2, size=(30000, len(channels))).astype(xp.float32)
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(30000, len(channels)).astype(elmap_ex.param.data_type)
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)
        elmap_ex.clear()
        elmap_ex.input_pointcloud(points, channels, R, t, 0, 0)
        assert xp.any(elmap_ex.elevation_map[2] > 0.5)
