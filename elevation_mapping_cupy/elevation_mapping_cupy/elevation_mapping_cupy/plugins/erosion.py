#
# Copyright (c) 2024, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
from typing import List, Optional

import cv2 as cv
import numpy as np

from ..backend import xp, GPU_AVAILABLE, asnumpy

from .plugin_manager import PluginBase


class Erosion(PluginBase):

    def __init__(
        self,
        input_layer_name="traversability",
        kernel_size: int = 3,
        iterations: int = 1,
        reverse: bool = False,
        default_layer_name: str = "traversability",
        **kwargs,
    ):
        super().__init__()
        self.input_layer_name = input_layer_name
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.reverse = reverse
        self.default_layer_name = default_layer_name

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: List[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: List[str],
        semantic_map: np.ndarray,
        semantic_layer_names: List[str],
        *args,
    ) -> np.ndarray:
        layer_data = self.get_layer_data(
            elevation_map,
            layer_names,
            plugin_layers,
            plugin_layer_names,
            semantic_map,
            semantic_layer_names,
            self.input_layer_name,
        )
        if layer_data is None:
            print(f"No layers are found, using {self.default_layer_name}!")
            layer_data = self.get_layer_data(
                elevation_map,
                layer_names,
                plugin_layers,
                plugin_layer_names,
                semantic_map,
                semantic_layer_names,
                self.default_layer_name,
            )
            if layer_data is None:
                print(f"No layers are found, using traversability!")
                layer_data = self.get_layer_data(
                    elevation_map,
                    layer_names,
                    plugin_layers,
                    plugin_layer_names,
                    semantic_map,
                    semantic_layer_names,
                    "traversability",
                )
        layer_np = asnumpy(layer_data)

        kernel = np.ones((self.kernel_size, self.kernel_size), np.uint8)

        if self.reverse:
            layer_np = 1 - layer_np
        layer_min = float(layer_np.min())
        layer_max = float(layer_np.max())
        layer_np_normalized = (
            (layer_np - layer_min) * 255 / (layer_max - layer_min)
        ).astype("uint8")
        eroded_map_np = cv.erode(
            layer_np_normalized, kernel, iterations=self.iterations
        )
        eroded_map_np = (
            eroded_map_np.astype(np.float32) * (layer_max - layer_min) / 255 + layer_min
        )
        if self.reverse:
            eroded_map_np = 1 - eroded_map_np

        return xp.asarray(eroded_map_np)
