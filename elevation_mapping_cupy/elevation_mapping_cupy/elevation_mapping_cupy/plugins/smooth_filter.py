#
# Copyright (c) 2022, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
from typing import List

import numpy as np

from ..backend import xp, GPU_AVAILABLE, scipy_ndimage

from .plugin_manager import PluginBase


class SmoothFilter(PluginBase):

    def __init__(
        self, cell_n: int = 100, input_layer_name: str = "elevation", **kwargs
    ):
        super().__init__()
        self.input_layer_name = input_layer_name

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: List[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: List[str],
        *args,
    ) -> np.ndarray:
        if self.input_layer_name in layer_names:
            idx = layer_names.index(self.input_layer_name)
            h = elevation_map[idx]
        elif self.input_layer_name in plugin_layer_names:
            idx = plugin_layer_names.index(self.input_layer_name)
            h = plugin_layers[idx]
        else:
            print(
                "layer name {} was not found. Using elevation layer.".format(
                    self.input_layer_name
                )
            )
            h = elevation_map[0]
        hs1 = scipy_ndimage.uniform_filter(h, size=3)
        hs1 = scipy_ndimage.uniform_filter(hs1, size=3)
        return hs1
