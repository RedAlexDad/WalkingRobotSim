from typing import List

import numpy as np

from ..backend import GPU_AVAILABLE, asnumpy, scipy_ndimage, xp, cp
from .plugin_manager import PluginBase


class Roughness(PluginBase):

    def __init__(
        self,
        cell_n: int = 100,
        input_layer_name: str = "inpaint",
        window_size: int = 5,
        **kwargs,
    ):
        super().__init__()
        self.input_layer_name = input_layer_name
        self.window_size = window_size

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
            h = elevation_map[0]

        is_valid = elevation_map[2]
        finite = xp.isfinite(h)
        valid = xp.logical_and(is_valid > 0.5, finite)
        h_clean = xp.where(valid, h, 0.0)

        if GPU_AVAILABLE and type(h_clean) == cp.ndarray:
            mean = cp.ndimage.uniform_filter(h_clean, size=self.window_size)
            mean_sq = cp.ndimage.uniform_filter(h_clean**2, size=self.window_size)
            variance = mean_sq - mean**2
            variance = xp.maximum(variance, 0.0)
            roughness = xp.sqrt(variance)
            roughness[~valid] = 0.0
        else:
            h_np = asnumpy(h_clean)
            valid_np = asnumpy(valid)
            mean = scipy_ndimage.uniform_filter(h_np, size=self.window_size)
            mean_sq = scipy_ndimage.uniform_filter(h_np**2, size=self.window_size)
            variance = mean_sq - mean**2
            variance = np.maximum(variance, 0.0)
            roughness = np.sqrt(variance)
            roughness[~valid_np] = 0.0

        return xp.asarray(roughness, dtype=xp.float32)
