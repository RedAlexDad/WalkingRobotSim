#
# Copyright (c) 2022, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import numpy as np

from ..backend import scipy_ndimage

try:
    from walking_robot_utils.logging import get_logger

    _log = get_logger("elevation_mapping.plugins.smooth_filter")
except ImportError:
    import logging as _logging

    _log = _logging.getLogger("elevation_mapping.plugins.smooth_filter")
    _log.addHandler(_logging.StreamHandler())
    _log.setLevel(_logging.INFO)


from .plugin_manager import PluginBase


class SmoothFilter(PluginBase):
    def __init__(self, cell_n: int = 100, input_layer_name: str = "elevation", **kwargs):
        super().__init__()
        self.input_layer_name = input_layer_name

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: list[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: list[str],
        *args,
    ) -> np.ndarray:
        if self.input_layer_name in layer_names:
            idx = layer_names.index(self.input_layer_name)
            h = elevation_map[idx]
        elif self.input_layer_name in plugin_layer_names:
            idx = plugin_layer_names.index(self.input_layer_name)
            h = plugin_layers[idx]
        else:
            _log.info(
                "layer name %s was not found. Using elevation layer.",
                self.input_layer_name,
            )
            h = elevation_map[0]
        hs1 = scipy_ndimage.uniform_filter(h, size=3)
        hs1 = scipy_ndimage.uniform_filter(hs1, size=3)
        return hs1
