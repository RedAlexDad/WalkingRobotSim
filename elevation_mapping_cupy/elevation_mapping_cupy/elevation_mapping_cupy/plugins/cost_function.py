from typing import List

import numpy as np

from ..backend import GPU_AVAILABLE, asnumpy, scipy_ndimage, xp
from .plugin_manager import PluginBase


class CostFunction(PluginBase):

    def __init__(
        self,
        cell_n: int = 100,
        slope_layer_name: str = "slope",
        roughness_layer_name: str = "roughness",
        max_slope: float = 0.8,
        max_roughness: float = 0.1,
        max_elevation_diff: float = 0.3,
        weight_slope: float = 0.4,
        weight_roughness: float = 0.4,
        weight_elevation: float = 0.2,
        **kwargs,
    ):
        super().__init__()
        self.slope_layer_name = slope_layer_name
        self.roughness_layer_name = roughness_layer_name
        self.max_slope = max_slope
        self.max_roughness = max_roughness
        self.max_elevation_diff = max_elevation_diff
        self.w_slope = weight_slope
        self.w_roughness = weight_roughness
        self.w_elevation = weight_elevation

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: List[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: List[str],
        *args,
    ) -> np.ndarray:
        slope_layer = self.get_layer_data(
            elevation_map,
            layer_names,
            plugin_layers,
            plugin_layer_names,
            None,
            [],
            self.slope_layer_name,
        )
        if slope_layer is None:
            slope_layer = xp.zeros_like(elevation_map[0])

        roughness_layer = self.get_layer_data(
            elevation_map,
            layer_names,
            plugin_layers,
            plugin_layer_names,
            None,
            [],
            self.roughness_layer_name,
        )
        if roughness_layer is None:
            roughness_layer = xp.zeros_like(elevation_map[0])

        elevation = elevation_map[0]
        is_valid = elevation_map[2]
        finite = xp.isfinite(elevation)

        valid_mask = xp.logical_and(is_valid > 0.5, finite)
        elev_valid = xp.where(valid_mask, elevation, 0.0)
        elev_np = asnumpy(elev_valid)
        mean_elev = scipy_ndimage.uniform_filter(elev_np, size=11)
        elev_diff_np = np.abs(elev_np - mean_elev)
        elev_diff = xp.asarray(elev_diff_np, dtype=xp.float32)

        slope_norm = xp.clip(slope_layer / max(self.max_slope, 1e-6), 0.0, 1.0)
        roughness_norm = xp.clip(
            roughness_layer / max(self.max_roughness, 1e-6), 0.0, 1.0
        )
        elev_norm = xp.clip(elev_diff / max(self.max_elevation_diff, 1e-6), 0.0, 1.0)

        cost = 1.0 - (
            self.w_slope * slope_norm
            + self.w_roughness * roughness_norm
            + self.w_elevation * elev_norm
        )
        cost = xp.clip(cost, 0.0, 1.0)

        cost = xp.where(valid_mask, cost, 0.0)

        return cost.astype(xp.float32)
