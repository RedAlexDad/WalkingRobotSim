#
# Copyright (c) 2022, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
import string
from typing import List

import numpy as np
from numba import njit

from ..backend import GPU_AVAILABLE, cp, xp
from .plugin_manager import PluginBase


@njit
def _base_elevation_cpu_numba(
    min_filtered, elevation_map, mask, rotation, h, w, res, use_th, th
):
    r6 = rotation[2, 0]
    r7 = rotation[2, 1]
    r8 = rotation[2, 2]
    for i in range(h * w):
        if mask.flat[i] <= 0.5:
            continue
        row = i // w
        col = i % w
        rx = row * res
        ry = col * res
        rz = elevation_map.flat[i]
        z_b = r6 * rx + r7 * ry + r8 * rz
        if use_th and z_b >= th:
            min_filtered.flat[i] = 1.0
        elif use_th and z_b < th:
            min_filtered.flat[i] = 0.0
        else:
            min_filtered.flat[i] = z_b


class RobotCentricElevation(PluginBase):
    def __init__(
        self,
        cell_n: int = 100,
        resolution: float = 0.05,
        threshold: float = 0.4,
        use_threshold: bool = 0,
        **kwargs,
    ):
        super().__init__()
        self.width = cell_n
        self.height = cell_n
        self.resolution = resolution
        self.threshold = threshold
        self.use_threshold = bool(use_threshold)
        self.min_filtered = xp.zeros((self.width, self.height), dtype=xp.float32)
        if GPU_AVAILABLE:
            self.base_elevation_kernel = cp.ElementwiseKernel(
                in_params="raw U map, raw U mask, raw U R",
                out_params="raw U newmap",
                preamble=string.Template("""
                    __device__ int get_map_idx(int idx, int layer_n) {
                        const int layer = ${width} * ${height};
                        return layer * layer_n + idx;
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
                    __device__ float get_map_x(int idx){
                        float idx_x = idx / ${width}* ${resolution};
                        return idx_x;
                    }
                    __device__ float get_map_y(int idx){
                        float idx_y = idx % ${width}* ${resolution};
                        return idx_y;
                    }
                    __device__ float transform_p(float x, float y, float z,
                                         float r0, float r1, float r2) {
                        return r0 * x + r1 * y + r2 * z ;
                    }
                    """).substitute(
                    width=self.width, height=self.height, resolution=resolution
                ),
                operation=string.Template("""
                    U rz = map[get_map_idx(i, 0)];
                    U valid = mask[get_map_idx(i, 0)];
                    if (valid > 0.5) {
                        U rx = get_map_x(get_map_idx(i, 0));
                        U ry = get_map_y(get_map_idx(i, 0));
                        U x_b = transform_p(rx, ry, rz, R[0], R[1], R[2]);
                        U y_b = transform_p(rx, ry, rz, R[3], R[4], R[5]);
                        U z_b = transform_p(rx, ry, rz, R[6], R[7], R[8]);
                        if (${use_threshold} && z_b>= ${threshold} ) {
                            newmap[get_map_idx(i, 0)] = 1.0;
                        }
                        else if (${use_threshold} && z_b< ${threshold} ){
                            newmap[get_map_idx(i, 0)] = 0.0;
                        }
                        else{
                            newmap[get_map_idx(i, 0)] = z_b;
                        }
                    }
                    """).substitute(
                    threshold=threshold, use_threshold=int(use_threshold)
                ),
                name="base_elevation_kernel",
            )

    def __call__(
        self,
        elevation_map: np.ndarray,
        layer_names: List[str],
        plugin_layers: np.ndarray,
        plugin_layer_names: List[str],
        semantic_map: np.ndarray,
        semantic_layer_names: List[str],
        rotation,
        *args,
    ) -> np.ndarray:
        self.min_filtered = elevation_map[0].copy()
        self._run_iteration(elevation_map[0], elevation_map[2], rotation)
        return self.min_filtered

    def _run_iteration(
        self, elevation_map: np.ndarray, mask: np.ndarray, rotation
    ) -> None:
        if GPU_AVAILABLE:
            self.base_elevation_kernel(
                elevation_map,
                mask,
                rotation,
                self.min_filtered,
                size=(self.width * self.height),
            )
        else:
            _base_elevation_cpu_numba(
                self.min_filtered,
                elevation_map,
                mask,
                rotation,
                self.height,
                self.width,
                self.resolution,
                self.use_threshold,
                self.threshold,
            )
