#
# Copyright (c) 2022, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
import string
from typing import List

import numpy as np

from backend import xp, GPU_AVAILABLE, cp

from .plugin_manager import PluginBase


class MaxFilter(PluginBase):

    def __init__(
        self, cell_n: int = 100, dilation_size: int = 5, iteration_n: int = 5, **kwargs
    ):
        super().__init__()
        self.iteration_n = iteration_n
        self.width = cell_n
        self.height = cell_n
        self.dilation_size = dilation_size
        self.max_filtered = xp.zeros((self.width, self.height))
        self.max_filtered_mask = xp.zeros((self.width, self.height))
        if GPU_AVAILABLE:
            self.max_filter_kernel = cp.ElementwiseKernel(
                in_params="raw U map, raw U mask",
                out_params="raw U newmap, raw U newmask",
                preamble=string.Template("""
                    __device__ int get_map_idx(int idx, int layer_n) {
                        const int layer = ${width} * ${height};
                        return layer * layer_n + idx;
                    }

                    __device__ int get_relative_map_idx(int idx, int dx, int dy, int layer_n) {
                        const int layer = ${width} * ${height};
                        const int relative_idx = idx + ${width} * dy + dx;
                        return layer * layer_n + relative_idx;
                    }
                    __device__ bool is_inside(int idx) {
                        int idx_x = idx / ${width};
                        int idx_y = idx % ${width};
                        if (idx_x <= 0 || idx_x >= ${width} - 1) {
                            return false;
                        }
                        if (idx_y <= 0 || idx_y >= ${height} - 1) {
                            return false;
                        }
                        return true;
                    }
                    """).substitute(width=self.width, height=self.height),
                operation=string.Template("""
                    U valid = mask[get_map_idx(i, 0)];
                    if (valid < 0.5) {
                        U max_value = -1000000.0;
                        for (int dy = -${dilation_size}; dy <= ${dilation_size}; dy++) {
                            for (int dx = -${dilation_size}; dx <= ${dilation_size}; dx++) {
                                int idx = get_relative_map_idx(i, dx, dy, 0);
                                if (!is_inside(idx)) {continue;}
                                U valid = mask[idx];
                                U value = map[idx];
                                if(valid > 0.5 && value > max_value) {
                                    max_value = value;
                                }
                            }
                        }
                        if (max_value > -1000000 + 1) {
                            newmap[get_map_idx(i, 0)] = max_value;
                            newmask[get_map_idx(i, 0)] = 0.6;
                        }
                    }
                    """).substitute(dilation_size=dilation_size),
                name="max_filter_kernel",
            )

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: List[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: List[str],
    ) -> np.ndarray:
        self.max_filtered = elevation_map[0].copy()
        self.max_filtered_mask = elevation_map[2].copy()
        for i in range(self.iteration_n):
            if GPU_AVAILABLE:
                self.max_filter_kernel(
                    self.max_filtered.copy(),
                    self.max_filtered_mask.copy(),
                    self.max_filtered,
                    self.max_filtered_mask,
                    size=(self.width * self.height),
                )
            else:
                self._max_filter_cpu()
            if (self.max_filtered_mask > 0.5).all():
                break
        max_filtered = xp.where(
            self.max_filtered_mask > 0.5, self.max_filtered.copy(), xp.nan
        )
        return max_filtered

    def _max_filter_cpu(self):
        prev_map = self.max_filtered.copy()
        prev_mask = self.max_filtered_mask.copy()
        dilation = self.dilation_size
        h, w = self.height, self.width
        for i in range(h * w):
            if prev_mask.flat[i] >= 0.5:
                continue
            iy = i // w
            ix = i % w
            max_val = -1e6
            for dy in range(-dilation, dilation + 1):
                for dx in range(-dilation, dilation + 1):
                    ny = iy + dy
                    nx = ix + dx
                    if nx <= 0 or nx >= w - 1 or ny <= 0 or ny >= h - 1:
                        continue
                    if prev_mask[ny, nx] > 0.5 and prev_map[ny, nx] > max_val:
                        max_val = prev_map[ny, nx]
            if max_val > -1e6 + 1:
                self.max_filtered.flat[i] = max_val
                self.max_filtered_mask.flat[i] = 0.6
