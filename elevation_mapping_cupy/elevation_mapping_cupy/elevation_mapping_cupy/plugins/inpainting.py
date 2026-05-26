#
# Copyright (c) 2022, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
import logging
from typing import List

import cv2 as cv
import numpy as np

from backend import xp, GPU_AVAILABLE, scipy_ndimage, asnumpy

_LOGGER = logging.getLogger(__name__)

from .plugin_manager import PluginBase


class Inpainting(PluginBase):

    def __init__(self, cell_n: int = 100, method: str = "telea", **kwargs):
        super().__init__()
        if method == "telea":
            self.method = cv.INPAINT_TELEA
        elif method == "ns":
            self.method = cv.INPAINT_NS
        else:
            self.method = cv.INPAINT_TELEA

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: List[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: List[str],
        *args,
    ) -> np.ndarray:
        valid_layer = elevation_map[2]
        mask_np = asnumpy((valid_layer < 0.5).astype("uint8"))
        elevation = elevation_map[0]
        finite_elevation = xp.isfinite(elevation)
        valid_mask = xp.logical_and(valid_layer > 0.5, finite_elevation)

        if (mask_np < 1).any():
            if not xp.any(valid_mask):
                return elevation

            h_valid = elevation[valid_mask]
            h_max = float(asnumpy(h_valid.max()))
            h_min = float(asnumpy(h_valid.min()))
            denom = h_max - h_min
            if denom <= 1e-6:
                _LOGGER.warning(
                    "Inpainting detected near-flat terrain (h_min=%.3f, h_max=%.3f); broadcasting height.",
                    h_min,
                    h_max,
                )
                filled = xp.full(elevation.shape, h_max, dtype=xp.float32)
            else:
                safe_elevation = xp.where(finite_elevation, elevation, h_min)
                scaled = asnumpy((safe_elevation - h_min) * 255.0 / denom).astype(
                    "uint8"
                )
                dst = cv.inpaint(scaled, mask_np, 1, self.method)
                h_inpainted = dst.astype(np.float32) * denom / 255.0 + h_min
                filled = xp.asarray(h_inpainted, dtype=xp.float32)

            filled = xp.where(valid_mask, elevation, filled)
            return filled.astype(xp.float64)
        else:
            return elevation_map[0]
