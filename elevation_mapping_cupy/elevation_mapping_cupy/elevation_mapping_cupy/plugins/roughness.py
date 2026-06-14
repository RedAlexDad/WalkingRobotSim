import numpy as np

from ..backend import scipy_ndimage, xp
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
            h = elevation_map[0]

        is_valid = elevation_map[2]
        finite = xp.isfinite(h)
        valid = xp.logical_and(is_valid > 0.5, finite)
        h_clean = xp.where(valid, h, 0.0)
        mean = scipy_ndimage.uniform_filter(h_clean, size=self.window_size)
        mean_sq = scipy_ndimage.uniform_filter(h_clean**2, size=self.window_size)
        variance = mean_sq - mean**2
        variance = xp.maximum(variance, 0.0)
        roughness = xp.sqrt(variance)
        roughness[~valid] = 0.0

        return roughness.astype(xp.float32)
