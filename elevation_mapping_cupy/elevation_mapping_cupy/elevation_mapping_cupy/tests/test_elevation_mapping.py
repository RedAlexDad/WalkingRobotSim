from pathlib import Path

import numpy as np
import pytest

from .. import elevation_mapping, parameter
from ..backend import xp

_TEST_DIR = Path(__file__).parent
_CONFIG_DIR = _TEST_DIR.parent.parent / "config" / "core"


def encode_max(maxim, index):
    maxim, index = xp.asarray(maxim, dtype=xp.float32), xp.asarray(
        index, dtype=xp.uint32
    )
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
            ind = xp.random.randint(0, 2, size=(100000, len(channels))).astype(
                xp.float32
            )
            points = encode_max(val, ind)
        else:
            points = xp.random.rand(100000, len(channels)).astype(
                elmap_ex.param.data_type
            )
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
            points = np.array(
                [[-4.0, 0.0, 0.0], [-4.0, 8.0, 1.0], [4.0, 8.0, 0.0], [4.0, 0.0, 0.0]]
            )
            elmap_ex.initialize_map(points, method)

    def test_plugins(self, elmap_ex):
        layers = elmap_ex.plugin_manager.layer_names
        data = np.zeros((200, 200), dtype=np.float32)
        for layer in layers:
            elmap_ex.get_map_with_name_ref(layer, data)
