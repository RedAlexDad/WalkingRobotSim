#
# Copyright (c) 2022, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import numpy as np

from elevation_mapping_cupy.plugins.plugin_manager import PluginBase

from ..backend import xp

try:
    from walking_robot_utils.logging import get_logger

    _log = get_logger("elevation_mapping.plugins.max_layer_filter")
except ImportError:
    import logging as _logging

    _log = _logging.getLogger("elevation_mapping.plugins.max_layer_filter")
    _log.addHandler(_logging.StreamHandler())
    _log.setLevel(_logging.INFO)


class MaxLayerFilter(PluginBase):
    def __init__(
        self,
        cell_n: int = 100,
        layers: list = ["traversability"],
        reverse: list = [True],
        min_or_max: str = "max",
        thresholds: list = [False],
        scales: list = [1.0],
        default_value: float = 0.0,
        **kwargs,
    ):
        super().__init__()
        self.layers = layers
        self.reverse = reverse
        self.min_or_max = min_or_max
        self.thresholds = thresholds
        self.scales = scales
        self.default_value = default_value

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: list[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: list[str],
        semantic_map: np.ndarray,
        semantic_layer_names: list[str],
        *args,
    ) -> np.ndarray:
        layers = []
        for it, name in enumerate(self.layers):
            layer = self.get_layer_data(
                elevation_map,
                layer_names,
                plugin_layers,
                plugin_layer_names,
                semantic_map,
                semantic_layer_names,
                name,
            )
            if layer is None:
                continue
            if isinstance(self.default_value, float):
                layer = xp.where(layer == 0.0, float(self.default_value), layer)
            elif isinstance(self.default_value, str):
                default_layer = self.get_layer_data(
                    elevation_map,
                    layer_names,
                    plugin_layers,
                    plugin_layer_names,
                    semantic_map,
                    semantic_layer_names,
                    self.default_value,
                )
                layer = xp.where(layer == 0, default_layer, layer)
            if len(self.reverse) > it and self.reverse[it]:
                layer = 1.0 - layer
            if len(self.scales) > it and isinstance(self.scales[it], float):
                layer = layer * float(self.scales[it])
            if len(self.thresholds) > it and isinstance(self.thresholds[it], float):
                layer = xp.where(layer > float(self.thresholds[it]), 1, 0)
            layers.append(layer)
        if len(layers) == 0:
            _log.info("No layers are found, returning traversability!")
            if isinstance(self.default_value, float):
                layer = xp.ones_like(elevation_map[0])
                layer *= float(self.default_value)
                return layer
            else:
                idx = layer_names.index("traversability")
                return elevation_map[idx]
        result = xp.stack(layers, axis=0)
        if self.min_or_max == "min":
            result = xp.min(result, axis=0)
        else:
            result = xp.max(result, axis=0)
        return result
