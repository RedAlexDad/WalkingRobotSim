#
# Copyright (c) 2023, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
from ..backend import xp, GPU_AVAILABLE, cp, scipy_ndimage, asnumpy
import string
import numpy as np


# ====================================================================
# CUDA kernels (only defined when GPU is available)
# =====================================================================
if GPU_AVAILABLE:

    def _sum_kernel_cuda(resolution, width, height):
        return cp.ElementwiseKernel(
            in_params="raw U p, raw U R, raw U t, raw W pcl_chan, raw W map_lay, raw W pcl_channels",
            out_params="raw U map, raw U newmap",
            preamble=string.Template("""
                    __device__ int get_map_idx(int idx, int layer_n) {
                        const int layer = ${width} * ${height};
                        return layer * layer_n + idx;
                    }
                """).substitute(resolution=resolution, width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                U idx = p[id * pcl_channels[0]];
                U valid = p[id * pcl_channels[0] + 1];
                U inside = p[id * pcl_channels[0] + 2];
                if (valid) {
                    if (inside) {
                        U feat = p[id * pcl_channels[0] + pcl_chan[layer]];
                        atomicAdd(&newmap[get_map_idx(idx, map_lay[layer])], feat);
                    }
                }
                """).substitute(),
            name="sum_kernel",
        )


    def _sum_compact_kernel_cuda(resolution, width, height):
        return cp.ElementwiseKernel(
            in_params="raw U p, raw U R, raw U t, raw W pcl_chan, raw W map_lay, raw W pcl_channels",
            out_params=" raw U newmap",
            preamble=string.Template("""
                    __device__ int get_map_idx(int idx, int layer_n) {
                        const int layer = ${width} * ${height};
                        return layer * layer_n + idx;
                    }
                """).substitute(resolution=resolution, width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                U idx = p[id * pcl_channels[0]];
                U valid = p[id * pcl_channels[0] + 1];
                U inside = p[id * pcl_channels[0] + 2];
                if (valid) {
                    if (inside) {
                        U feat = p[id * pcl_channels[0] + pcl_chan[layer]];
                        atomicAdd(&newmap[get_map_idx(idx, layer)], feat);
                    }
                }
                """).substitute(),
            name="sum_compact_kernel",
        )


    def _sum_max_kernel_cuda(resolution, width, height):
        return cp.ElementwiseKernel(
            in_params="raw U p, raw U max_pt, raw T max_id, raw W pcl_chan, raw W map_lay, raw W pcl_channels",
            out_params=" raw U newmap",
            preamble=string.Template("""
                    __device__ int get_map_idx(int idx, int layer_n) {
                        const int layer = ${width} * ${height};
                        return layer * layer_n + idx;
                    }
                """).substitute(resolution=resolution, width=width, height=height),
            operation=string.Template("""
                U idx = p[i * pcl_channels[0]];
                U valid = p[i * pcl_channels[0] + 1];
                U inside = p[i * pcl_channels[0] + 2];
                if (valid) {
                    if (inside) {
                        for ( W it=0;it<pcl_channels[2];it++){
                            U prob = max_pt[i * pcl_channels[2] + it];
                            T id = max_id[i * pcl_channels[2] + it];
                            atomicAdd(&newmap[get_map_idx(idx, id)], prob);
                        }
                    }
                }
                """).substitute(),
            name="sum_max_kernel",
        )


    def _alpha_kernel_cuda(resolution, width, height):
        return cp.ElementwiseKernel(
            in_params="raw U p, raw W pcl_chan, raw W map_lay, raw W pcl_channels",
            out_params="raw U newmap",
            preamble=string.Template("""
                    __device__ int get_map_idx(int idx, int layer_n) {
                        const int layer = ${width} * ${height};
                        return layer * layer_n + idx;
                    }
                """).substitute(resolution=resolution, width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                U idx = p[id * pcl_channels[0]];
                U valid = p[id * pcl_channels[0] + 1];
                U inside = p[id * pcl_channels[0] + 2];
                if (valid) {
                    if (inside) {
                        U theta_max = 0;
                        W arg_max = 0;
                        U theta = p[id * pcl_channels[0] + pcl_chan[layer]];
                            if (theta >=theta_max){
                                arg_max = map_lay[layer];
                                theta_max = theta;
                            }
                        atomicAdd(&newmap[get_map_idx(idx, arg_max)], theta_max);
                    }
                }
                """).substitute(),
            name="alpha_kernel",
        )


    def _average_kernel_cuda(width, height):
        return cp.ElementwiseKernel(
            in_params="raw V newmap, raw W pcl_chan, raw W map_lay, raw W pcl_channels, raw U new_elmap",
            out_params="raw U map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                U cnt = new_elmap[get_map_idx(id, 2)];
                if (cnt>0){
                    U feat = newmap[get_map_idx(id,  map_lay[layer])]/(1*cnt);
                    map[get_map_idx(id,  map_lay[layer])] = feat;
                }
                """).substitute(),
            name="average_map_kernel",
        )


    def _bayesian_inference_kernel_cuda(width, height):
        return cp.ElementwiseKernel(
            in_params=" raw W pcl_chan, raw W map_lay, raw W pcl_channels, raw U new_elmap",
            out_params="raw U newmap, raw U sum_mean, raw U map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                U cnt = new_elmap[get_map_idx(id, 2)];
                if (cnt>0){
                        U feat_ml = sum_mean[get_map_idx(id,  layer)]/cnt;
                        U feat_old = map[get_map_idx(id,  map_lay[layer])];
                        U sigma_old = newmap[get_map_idx(id,  map_lay[layer])];
                        U sigma = 1.0;
                        U feat_new = sigma*feat_old /(cnt*sigma_old + sigma) +cnt*sigma_old *feat_ml /(cnt*sigma_old+sigma);
                        U sigma_new = sigma*sigma_old /(cnt*sigma_old +sigma);
                        map[get_map_idx(id,  map_lay[layer])] = feat_new;
                        newmap[get_map_idx(id,  map_lay[layer])] = sigma_new;
                }
                """).substitute(),
            name="bayesian_inference_kernel",
        )


    def _class_average_kernel_cuda(width, height, alpha):
        return cp.ElementwiseKernel(
            in_params="raw V newmap, raw W pcl_chan, raw W map_lay, raw W pcl_channels, raw U new_elmap",
            out_params="raw U map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                U cnt = new_elmap[get_map_idx(id, 2)];
                if (cnt>0){
                    U prev_val = map[get_map_idx(id,  map_lay[layer])];
                    if (prev_val==0){
                        U val = newmap[get_map_idx(id, map_lay[layer])]/(1*cnt);
                        map[get_map_idx(id,  map_lay[layer])] = val;
                    }
                    else{
                        U val = ${alpha} *prev_val + (1-${alpha}) * newmap[get_map_idx(id, map_lay[layer])]/(cnt);
                        map[get_map_idx(id,  map_lay[layer])] = val;
                    }
                }
                """).substitute(alpha=alpha),
            name="class_average_kernel",
        )


    def _add_color_kernel_cuda(width, height):
        return cp.ElementwiseKernel(
            in_params="raw T p, raw U R, raw U t, raw W pcl_chan, raw W map_lay, raw W pcl_channels",
            out_params="raw V color_map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                __device__ unsigned int get_r(unsigned int color){
                    unsigned int red = 0xFF0000;
                    unsigned int reds = (color & red) >> 16;
                    return reds;
                }
                __device__ unsigned int get_g(unsigned int color){
                    unsigned int green = 0xFF00;
                    unsigned int greens = (color & green) >> 8;
                    return greens;
                }
                __device__ unsigned int get_b(unsigned int color){
                    unsigned int blue = 0xFF;
                    unsigned int blues = ( color & blue);
                    return blues;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                U idx = p[id * pcl_channels[0]];
                U valid = p[id * pcl_channels[0] + 1];
                U inside = p[id * pcl_channels[0] + 2];
                if (valid && inside){
                        unsigned int color = __float_as_uint(p[id * pcl_channels[0] + pcl_chan[layer]]);
                        atomicAdd(&color_map[get_map_idx(idx, layer*3)], get_r(color));
                        atomicAdd(&color_map[get_map_idx(idx, layer*3+1)], get_g(color));
                        atomicAdd(&color_map[get_map_idx(idx, layer*3 + 2)], get_b(color));
                        atomicAdd(&color_map[get_map_idx(idx, pcl_channels[1]*3)], 1);
                }
                """).substitute(width=width),
            name="add_color_kernel",
        )


    def _color_average_kernel_cuda(width, height):
        return cp.ElementwiseKernel(
            in_params="raw V color_map, raw W pcl_chan, raw W map_lay, raw W pcl_channels",
            out_params="raw U map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                __device__ unsigned int get_r(unsigned int color){
                    unsigned int red = 0xFF0000;
                    unsigned int reds = (color & red) >> 16;
                    return reds;
                }
                __device__ unsigned int get_g(unsigned int color){
                    unsigned int green = 0xFF00;
                    unsigned int greens = (color & green) >> 8;
                    return greens;
                }
                __device__ unsigned int get_b(unsigned int color){
                    unsigned int blue = 0xFF;
                    unsigned int blues = ( color & blue);
                    return blues;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                U id = floorf(i/pcl_channels[1]);
                int layer = i % pcl_channels[1];
                unsigned int cnt = color_map[get_map_idx(id, pcl_channels[1]*3)];
                if (cnt>0){
                        unsigned int r = color_map[get_map_idx(id, layer*3)]/(1*cnt);
                        unsigned int g = color_map[get_map_idx(id, layer*3+1)]/(1*cnt);
                        unsigned int b = color_map[get_map_idx(id, layer*3+2)]/(1*cnt);
                        unsigned int rgb = (r<<16) + (g << 8) + b;
                        float rgb_ = __uint_as_float(rgb);
                        map[get_map_idx(id,  map_lay[layer])] = rgb_;
                }
                """).substitute(),
            name="color_average_kernel",
        )


# =====================================================================
# CPU fallback implementations
# =====================================================================

def _make_sum_kernel_cpu(width, height):
    def sum_kernel_cpu(p, R, t, pcl_chan, map_lay, pcl_channels, map_, newmap, size=None):
        p = np.asarray(p)
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        map_lay = np.asarray(map_lay, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        n_layers = pc[1]
        n_pts = p.shape[0]
        cell_n = width * height
        for pid in range(n_pts):
            idx = int(p[pid, 0])
            valid = bool(p[pid, 1])
            inside = bool(p[pid, 2])
            if valid and inside:
                for lay in range(n_layers):
                    feat = p[pid, int(pcl_chan[lay])]
                    np.add.at(newmap.ravel(), idx + map_lay[lay] * cell_n, feat)
    return sum_kernel_cpu


def _make_sum_compact_kernel_cpu(width, height):
    def sum_compact_kernel_cpu(p, R, t, pcl_chan, map_lay, pcl_channels, newmap, size=None):
        p = np.asarray(p)
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        n_layers = pc[1]
        n_pts = p.shape[0]
        cell_n = width * height
        for pid in range(n_pts):
            idx = int(p[pid, 0])
            valid = bool(p[pid, 1])
            inside = bool(p[pid, 2])
            if valid and inside:
                for lay in range(n_layers):
                    feat = p[pid, int(pcl_chan[lay])]
                    np.add.at(newmap.ravel(), idx + lay * cell_n, feat)
    return sum_compact_kernel_cpu


def _make_sum_max_kernel_cpu(width, height):
    def sum_max_kernel_cpu(p, max_pt, max_id, pcl_chan, map_lay, pcl_channels, newmap, size=None):
        p = np.asarray(p)
        max_pt = np.asarray(max_pt)
        max_id = np.asarray(max_id, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        n_max = pc[2]
        n_pts = p.shape[0]
        cell_n = width * height
        for pid in range(n_pts):
            idx = int(p[pid, 0])
            valid = bool(p[pid, 1])
            inside = bool(p[pid, 2])
            if valid and inside:
                for it in range(n_max):
                    prob = max_pt[pid, it]
                    sid = int(max_id[pid, it])
                    np.add.at(newmap.ravel(), idx + sid * cell_n, prob)
    return sum_max_kernel_cpu


def _make_alpha_kernel_cpu(width, height):
    def alpha_kernel_cpu(p, pcl_chan, map_lay, pcl_channels, newmap, size=None):
        p = np.asarray(p)
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        map_lay = np.asarray(map_lay, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        n_layers = pc[1]
        n_pts = p.shape[0]
        cell_n = width * height
        for pid in range(n_pts):
            idx = int(p[pid, 0])
            valid = bool(p[pid, 1])
            inside = bool(p[pid, 2])
            if valid and inside:
                theta_max = 0.0
                arg_max = 0
                for lay in range(n_layers):
                    theta = p[pid, int(pcl_chan[lay])]
                    if theta >= theta_max:
                        arg_max = int(map_lay[lay])
                        theta_max = theta
                np.add.at(newmap.ravel(), idx + arg_max * cell_n, theta_max)
    return alpha_kernel_cpu


def _make_average_kernel_cpu(width, height):
    def average_kernel_cpu(newmap, pcl_chan, map_lay, pcl_channels, new_elmap, map_, size=None):
        newmap = np.asarray(newmap)
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        map_lay = np.asarray(map_lay, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        new_elmap = np.asarray(new_elmap)
        n_layers = pc[1]
        cell_n = width * height
        for cid in range(cell_n):
            cnt = new_elmap.ravel()[cid + 2 * cell_n]
            if cnt > 0:
                for lay in range(n_layers):
                    feat = newmap.ravel()[cid + map_lay[lay] * cell_n] / cnt
                    map_.ravel()[cid + map_lay[lay] * cell_n] = feat
    return average_kernel_cpu


def _make_bayesian_inference_kernel_cpu(width, height):
    def bayesian_inference_kernel_cpu(pcl_chan, map_lay, pcl_channels, new_elmap, newmap, sum_mean, map_, size=None):
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        map_lay = np.asarray(map_lay, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        new_elmap = np.asarray(new_elmap)
        newmap = np.asarray(newmap)
        sum_mean = np.asarray(sum_mean)
        map_ = np.asarray(map_)
        n_layers = pc[1]
        cell_n = width * height
        for cid in range(cell_n):
            cnt = new_elmap.ravel()[cid + 2 * cell_n]
            if cnt > 0:
                for lay in range(n_layers):
                    feat_ml = sum_mean.ravel()[cid + lay * cell_n] / cnt
                    feat_old = map_.ravel()[cid + map_lay[lay] * cell_n]
                    sigma_old = newmap.ravel()[cid + map_lay[lay] * cell_n]
                    sigma = 1.0
                    feat_new = sigma * feat_old / (cnt * sigma_old + sigma) + cnt * sigma_old * feat_ml / (cnt * sigma_old + sigma)
                    sigma_new = sigma * sigma_old / (cnt * sigma_old + sigma)
                    map_.ravel()[cid + map_lay[lay] * cell_n] = feat_new
                    newmap.ravel()[cid + map_lay[lay] * cell_n] = sigma_new
    return bayesian_inference_kernel_cpu


def _make_class_average_kernel_cpu(width, height, alpha):
    def class_average_kernel_cpu(newmap, pcl_chan, map_lay, pcl_channels, new_elmap, map_, size=None):
        newmap = np.asarray(newmap)
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        map_lay = np.asarray(map_lay, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        new_elmap = np.asarray(new_elmap)
        map_ = np.asarray(map_)
        n_layers = pc[1]
        cell_n = width * height
        for cid in range(cell_n):
            cnt = new_elmap.ravel()[cid + 2 * cell_n]
            if cnt > 0:
                for lay in range(n_layers):
                    prev_val = map_.ravel()[cid + map_lay[lay] * cell_n]
                    cur = newmap.ravel()[cid + map_lay[lay] * cell_n] / cnt
                    if prev_val == 0:
                        map_.ravel()[cid + map_lay[lay] * cell_n] = cur
                    else:
                        val = alpha * prev_val + (1 - alpha) * cur
                        map_.ravel()[cid + map_lay[lay] * cell_n] = val
    return class_average_kernel_cpu


def _make_add_color_kernel_cpu(width, height):
    def add_color_kernel_cpu(p, R, t, pcl_chan, map_lay, pcl_channels, color_map, size=None):
        p = np.asarray(p)
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        n_layers = pc[1]
        n_pts = p.shape[0]
        cell_n = width * height
        for pid in range(n_pts):
            idx = int(p[pid, 0])
            valid = bool(p[pid, 1])
            inside = bool(p[pid, 2])
            if valid and inside:
                for lay in range(n_layers):
                    color_float = p[pid, int(pcl_chan[lay])]
                    color_uint = np.frombuffer(np.float32(color_float).tobytes(), dtype=np.uint32)[0]
                    r = (color_uint >> 16) & 0xFF
                    g = (color_uint >> 8) & 0xFF
                    b = color_uint & 0xFF
                    np.add.at(color_map.ravel(), idx + (lay * 3 + 0) * cell_n, r)
                    np.add.at(color_map.ravel(), idx + (lay * 3 + 1) * cell_n, g)
                    np.add.at(color_map.ravel(), idx + (lay * 3 + 2) * cell_n, b)
                    np.add.at(color_map.ravel(), idx + (n_layers * 3) * cell_n, 1)
    return add_color_kernel_cpu


def _make_color_average_kernel_cpu(width, height):
    def color_average_kernel_cpu(color_map, pcl_chan, map_lay, pcl_channels, map_, size=None):
        color_map = np.asarray(color_map)
        pcl_chan = np.asarray(pcl_chan, dtype=int)
        map_lay = np.asarray(map_lay, dtype=int)
        pc = np.asarray(pcl_channels, dtype=int)
        map_ = np.asarray(map_)
        n_layers = pc[1]
        cell_n = width * height
        for cid in range(cell_n):
            cnt = int(color_map.ravel()[cid + (n_layers * 3) * cell_n])
            if cnt > 0:
                for lay in range(n_layers):
                    r = int(color_map.ravel()[cid + (lay * 3 + 0) * cell_n]) // cnt
                    g = int(color_map.ravel()[cid + (lay * 3 + 1) * cell_n]) // cnt
                    b = int(color_map.ravel()[cid + (lay * 3 + 2) * cell_n]) // cnt
                    rgb_uint = np.uint32((r << 16) | (g << 8) | b)
                    rgb_float = np.frombuffer(rgb_uint.tobytes(), dtype=np.float32)[0]
                    map_.ravel()[cid + map_lay[lay] * cell_n] = rgb_float
    return color_average_kernel_cpu


# =====================================================================
# Public API — dispatch between CUDA and CPU
# =====================================================================

def sum_kernel(resolution, width, height):
    if GPU_AVAILABLE:
        return _sum_kernel_cuda(resolution, width, height)
    return _make_sum_kernel_cpu(width, height)


def sum_compact_kernel(resolution, width, height):
    if GPU_AVAILABLE:
        return _sum_compact_kernel_cuda(resolution, width, height)
    return _make_sum_compact_kernel_cpu(width, height)


def sum_max_kernel(resolution, width, height):
    if GPU_AVAILABLE:
        return _sum_max_kernel_cuda(resolution, width, height)
    return _make_sum_max_kernel_cpu(width, height)


def alpha_kernel(resolution, width, height):
    if GPU_AVAILABLE:
        return _alpha_kernel_cuda(resolution, width, height)
    return _make_alpha_kernel_cpu(width, height)


def average_kernel(width, height):
    if GPU_AVAILABLE:
        return _average_kernel_cuda(width, height)
    return _make_average_kernel_cpu(width, height)


def bayesian_inference_kernel(width, height):
    if GPU_AVAILABLE:
        return _bayesian_inference_kernel_cuda(width, height)
    return _make_bayesian_inference_kernel_cpu(width, height)


def class_average_kernel(width, height, alpha):
    if GPU_AVAILABLE:
        return _class_average_kernel_cuda(width, height, alpha)
    return _make_class_average_kernel_cpu(width, height, alpha)


def add_color_kernel(width, height):
    if GPU_AVAILABLE:
        return _add_color_kernel_cuda(width, height)
    return _make_add_color_kernel_cpu(width, height)


def color_average_kernel(width, height):
    if GPU_AVAILABLE:
        return _color_average_kernel_cuda(width, height)
    return _make_color_average_kernel_cpu(width, height)
