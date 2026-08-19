from typing import List

import numpy as np

from ..backend import GPU_AVAILABLE, asnumpy, xp, cp
from .plugin_manager import PluginBase


class SurfaceGradient(PluginBase):

    def __init__(
        self,
        cell_n: int = 100,
        input_layer_name: str = "inpaint",
        **kwargs,
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
            h = elevation_map[0]

        is_valid = elevation_map[2]
        finite = xp.isfinite(h)
        valid = xp.logical_and(is_valid > 0.5, finite)
        h_clean = xp.where(valid, h, xp.nan)

        if GPU_AVAILABLE and type(h_clean) == cp.ndarray:
            dy, dx = xp.gradient(h_clean, axis=(0, 1))
            magnitude = xp.sqrt(dx**2 + dy**2)
            slope = xp.arctan(magnitude)
            slope[~valid] = 0.0
        else:
            h_np = asnumpy(h_clean)
            valid_np = asnumpy(valid)
            dy, dx = np.gradient(h_np, axis=(0, 1))
            magnitude = np.sqrt(dx**2 + dy**2)
            slope = np.arctan(magnitude)
            slope[~valid_np] = 0.0

        return xp.asarray(slope, dtype=xp.float32)
