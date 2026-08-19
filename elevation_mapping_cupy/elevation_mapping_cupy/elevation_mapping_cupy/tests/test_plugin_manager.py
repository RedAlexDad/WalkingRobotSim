from pathlib import Path

import numpy as np
import pytest
from ruamel.yaml import YAML

from ..backend import xp
from ..plugins.plugin_manager import PluginBase, PluginManager, PluginParams

_TEST_DIR = Path(__file__).parent
_CONFIG_DIR = _TEST_DIR.parent.parent / "config" / "core"
_PLUGIN_CONFIG = str(_CONFIG_DIR / "plugin_config.yaml")


class TestPluginParams:
    def test_default_values(self):
        p = PluginParams(name="test", layer_name="test_layer")
        assert p.name == "test"
        assert p.layer_name == "test_layer"
        assert p.fill_nan is False
        assert p.is_height_layer is False

    def test_custom_values(self):
        p = PluginParams(name="filter", layer_name="out", fill_nan=True, is_height_layer=True)
        assert p.fill_nan is True
        assert p.is_height_layer is True


class TestPluginManager:
    def test_init_empty(self):
        pm = PluginManager(cell_n=100)
        assert pm.cell_n == 100
        assert not hasattr(pm, "plugins")

    def test_init_with_params(self):
        pm = PluginManager(cell_n=50)
        params = [PluginParams(name="smooth_filter", layer_name="smooth")]
        extras = [{"cell_n": 50}]
        pm.init(params, extras)
        assert len(pm.plugins) == 1
        assert pm.layers.shape == (1, 50, 50)
        assert pm.layer_names == ["smooth"]
        assert pm.plugin_names == ["smooth_filter"]

    def test_load_plugin_settings(self):
        pm = PluginManager(cell_n=200)
        pm.load_plugin_settings(_PLUGIN_CONFIG)
        assert len(pm.plugins) > 0
        assert len(pm.layer_names) == len(pm.plugins)
        assert len(pm.plugin_names) == len(pm.plugins)

    def test_get_layer_names(self):
        pm = PluginManager(cell_n=100)
        params = [
            PluginParams(name="min_filter", layer_name="min_filter"),
            PluginParams(name="smooth_filter", layer_name="smooth"),
        ]
        extras = [{"cell_n": 100}, {"cell_n": 100}]
        pm.init(params, extras)
        assert pm.get_layer_names() == ["min_filter", "smooth"]

    def test_get_plugin_names(self):
        pm = PluginManager(cell_n=100)
        params = [PluginParams(name="min_filter", layer_name="min_filter")]
        extras = [{"cell_n": 100}]
        pm.init(params, extras)
        assert pm.get_plugin_names() == ["min_filter"]

    def test_get_plugin_index_with_name_found(self):
        pm = PluginManager(cell_n=100)
        params = [PluginParams(name="min_filter", layer_name="min_filter")]
        extras = [{"cell_n": 100}]
        pm.init(params, extras)
        assert pm.get_plugin_index_with_name("min_filter") == 0

    def test_get_plugin_index_with_name_not_found(self):
        pm = PluginManager(cell_n=100)
        params = [PluginParams(name="min_filter", layer_name="min_filter")]
        extras = [{"cell_n": 100}]
        pm.init(params, extras)
        assert pm.get_plugin_index_with_name("nonexistent") is None

    def test_get_layer_index_with_name_found(self):
        pm = PluginManager(cell_n=100)
        params = [PluginParams(name="min_filter", layer_name="min_filter")]
        extras = [{"cell_n": 100}]
        pm.init(params, extras)
        assert pm.get_layer_index_with_name("min_filter") == 0

    def test_get_layer_index_with_name_not_found(self):
        pm = PluginManager(cell_n=100)
        assert pm.get_layer_index_with_name("missing") is None

    def test_reset_layers(self):
        pm = PluginManager(cell_n=50)
        params = [PluginParams(name="smooth_filter", layer_name="smooth")]
        extras = [{"cell_n": 50}]
        pm.init(params, extras)
        pm.layers[0, 10, 10] = 42.0
        pm.reset_layers()
        assert xp.isnan(pm.layers[0, 10, 10])

    def test_reset_layers_before_init_does_not_crash(self):
        pm = PluginManager(cell_n=50)
        pm.reset_layers()

    def test_get_map_with_name_found(self):
        pm = PluginManager(cell_n=50)
        params = [PluginParams(name="smooth_filter", layer_name="smooth")]
        extras = [{"cell_n": 50}]
        pm.init(params, extras)
        result = pm.get_map_with_name("smooth")
        assert result is not None
        assert result.shape == (50, 50)

    def test_get_map_with_name_not_found(self):
        pm = PluginManager(cell_n=50)
        assert pm.get_map_with_name("nonexistent") is None

    def test_get_param_with_name_found(self):
        pm = PluginManager(cell_n=50)
        params = [PluginParams(name="smooth_filter", layer_name="smooth")]
        extras = [{"cell_n": 50}]
        pm.init(params, extras)
        result = pm.get_param_with_name("smooth")
        assert result is not None
        assert isinstance(result, PluginParams)

    def test_get_param_with_name_not_found(self):
        pm = PluginManager(cell_n=50)
        assert pm.get_param_with_name("missing") is None


class TestPluginBase:
    def test_get_layer_data_from_elevation(self):
        em = xp.zeros((7, 10, 10), dtype=xp.float32)
        em[0] = 1.0
        layer_names = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        plugin_layers = xp.zeros((0, 10, 10), dtype=xp.float32)
        plugin_layer_names = []
        semantic_map = xp.zeros((0, 10, 10), dtype=xp.float32)
        semantic_layer_names = []
        pb = PluginBase()
        result = pb.get_layer_data(
            em, layer_names, plugin_layers, plugin_layer_names, semantic_map, semantic_layer_names, "elevation"
        )
        assert result is not None
        assert result.shape == (10, 10)
        assert xp.allclose(result, 1.0)

    def test_get_layer_data_from_plugin(self):
        em = xp.zeros((7, 10, 10), dtype=xp.float32)
        layer_names = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        plugin_layers = xp.zeros((1, 10, 10), dtype=xp.float32)
        plugin_layers[0] = 42.0
        plugin_layer_names = ["custom_layer"]
        semantic_map = xp.zeros((0, 10, 10), dtype=xp.float32)
        semantic_layer_names = []
        pb = PluginBase()
        result = pb.get_layer_data(
            em, layer_names, plugin_layers, plugin_layer_names, semantic_map, semantic_layer_names, "custom_layer"
        )
        assert result is not None
        assert xp.allclose(result, 42.0)

    def test_get_layer_data_from_semantic(self):
        em = xp.zeros((7, 10, 10), dtype=xp.float32)
        layer_names = ["elevation", "variance", "is_valid", "traversability", "time", "upper_bound", "is_upper_bound"]
        plugin_layers = xp.zeros((0, 10, 10), dtype=xp.float32)
        plugin_layer_names = []
        semantic_map = xp.zeros((1, 10, 10), dtype=xp.float32)
        semantic_map[0] = 99.0
        semantic_layer_names = ["semantic_class"]
        pb = PluginBase()
        result = pb.get_layer_data(
            em, layer_names, plugin_layers, plugin_layer_names, semantic_map, semantic_layer_names, "semantic_class"
        )
        assert result is not None
        assert xp.allclose(result, 99.0)

    def test_get_layer_data_not_found(self):
        em = xp.zeros((7, 10, 10), dtype=xp.float32)
        layer_names = ["elevation"]
        plugin_layers = xp.zeros((0, 10, 10), dtype=xp.float32)
        plugin_layer_names = []
        semantic_map = xp.zeros((0, 10, 10), dtype=xp.float32)
        semantic_layer_names = []
        pb = PluginBase()
        result = pb.get_layer_data(
            em, layer_names, plugin_layers, plugin_layer_names, semantic_map, semantic_layer_names, "missing"
        )
        assert result is None

    def test_get_layer_data_returns_copy(self):
        em = xp.zeros((7, 10, 10), dtype=xp.float32)
        em[0] = 1.0
        layer_names = ["elevation"]
        pb = PluginBase()
        result = pb.get_layer_data(em, layer_names, xp.zeros((0, 10, 10)), [], xp.zeros((0, 10, 10)), [], "elevation")
        em[0, 0, 0] = 999.0
        assert result[0, 0] != 999.0
