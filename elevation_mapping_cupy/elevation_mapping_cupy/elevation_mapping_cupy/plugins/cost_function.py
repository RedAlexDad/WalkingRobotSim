import numpy as np

from ..backend import scipy_ndimage, xp
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
        self.max_slope = float(max_slope)
        self.max_roughness = float(max_roughness)
        self.max_elevation_diff = float(max_elevation_diff)
        self.w_slope = float(weight_slope)
        self.w_roughness = float(weight_roughness)
        self.w_elevation = float(weight_elevation)

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: list[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: list[str],
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
        mean_elev = scipy_ndimage.uniform_filter(elev_valid, size=11)
        elev_diff = xp.abs(elev_valid - mean_elev).astype(xp.float32)

        max_slope = float(max(self.max_slope, 1e-6))
        max_roughness = float(max(self.max_roughness, 1e-6))
        max_elev_diff = float(max(self.max_elevation_diff, 1e-6))
        slope_norm = xp.clip(slope_layer / max_slope, 0.0, 1.0)
        roughness_norm = xp.clip(roughness_layer / max_roughness, 0.0, 1.0)
        elev_norm = xp.clip(elev_diff / max_elev_diff, 0.0, 1.0)

        cost = 1.0 - (self.w_slope * slope_norm + self.w_roughness * roughness_norm + self.w_elevation * elev_norm)
        cost = xp.clip(cost, 0.0, 1.0)

        cost = xp.where(valid_mask, cost, 0.0)

        return cost.astype(xp.float32)
