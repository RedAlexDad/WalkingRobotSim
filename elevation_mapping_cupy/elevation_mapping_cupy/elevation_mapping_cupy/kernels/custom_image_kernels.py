#
# Copyright (c) 2023, Takahiro Miki. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#
import string

import numpy as np
from ..backend import GPU_AVAILABLE, asnumpy, cp, scipy_ndimage, xp

# =====================================================================
# CUDA kernels (only defined when GPU is available)
# =====================================================================
if GPU_AVAILABLE:

    def image_to_map_correspondence_kernel_cuda(
        resolution, width, height, tolerance_z_collision
    ):
        _image_to_map_correspondence_kernel = cp.ElementwiseKernel(
            in_params="raw U map, raw U x1, raw U y1, raw U z1, raw U P, raw U K, raw U D, raw U image_height, raw U image_width, raw U center",
            out_params="raw U uv_correspondence, raw B valid_correspondence",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                __device__ bool is_inside_map(int x, int y) {
                    return (x >= 0 && y >= 0 && x<${width} && y<${height});
                }
                __device__ float get_l2_distance(int x0, int y0, int x1, int y1) {
                    float dx = x0-x1;
                    float dy = y0-y1;
                    return sqrt( dx*dx + dy*dy);
                }
                """).substitute(width=width, height=height, resolution=resolution),
            operation=string.Template("""
                int cell_idx = get_map_idx(i, 0);

                // return if gridcell has no valid height
                if (map[get_map_idx(i, 2)] != 1){
                    return;
                }

                // get current cell position
                int y0 = i % ${width};
                int x0 = i / ${width};

                // gridcell 3D point in worldframe TODO reverse x and y
                float p1 = (x0-(${width}/2)) * ${resolution} + center[0];
                float p2 = (y0-(${height}/2)) * ${resolution} + center[1];
                float p3 = map[cell_idx] +  center[2];

                // reproject 3D point into image plane
                float u = p1 * P[0]  + p2 * P[1] + p3 * P[2] + P[3];
                float v = p1 * P[4]  + p2 * P[5] + p3 * P[6] + P[7];
                float d = p1 * P[8]  + p2 * P[9] + p3 * P[10] + P[11];

                // filter point behind image plane
                if (d <= 0) {
                    return;
                }
                u = u/d;
                v = v/d;

                // Check if D is all zeros
                bool is_D_zero = (D[0] == 0 && D[1] == 0 && D[2] == 0 && D[3] == 0 && D[4] == 0);

                // Apply undistortion using distortion matrix D if not all zeros
                if (!is_D_zero) {
                    float k1 = D[0];
                    float k2 = D[1];
                    float p1 = D[2];
                    float p2 = D[3];
                    float k3 = D[4];
                    float fx = K[0];
                    float fy = K[4];
                    float cx = K[2];
                    float cy = K[5];
                    float x = (u - cx) / fx;
                    float y = (v - cy) / fy;
                    float r2 = x * x + y * y;
                    float radial_distortion = 1 + k1 * r2 + k2 * r2 * r2 + k3 * r2 * r2 * r2;
                    float u_corrected = x * radial_distortion + 2 * p1 * x * y + p2 * (r2 + 2 * x * x);
                    float v_corrected = y * radial_distortion + 2 * p2 * x * y + p1 * (r2 + 2 * y * y);
                    u = fx * u_corrected + cx;
                    v = fy * v_corrected + cy;
                }

                // filter point next to image plane
                if ((u < 0) || (v < 0) || (u >= image_width) || (v >= image_height)){
                    return;
                }

                int y0_c = y0;
                int x0_c = x0;
                float total_dis = get_l2_distance(x0_c, y0_c, x1,y1);
                float z0 = map[cell_idx];
                float delta_z = z1-z0;


                // bresenham algorithm to iterate over cells in line between camera center and current gridmap cell
                // https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
                int dx = abs(x1-x0);
                int sx = x0 < x1 ? 1 : -1;
                int dy = -abs(y1 - y0);
                int sy = y0 < y1 ? 1 : -1;
                int error = dx + dy;

                bool is_valid = true;

                // iterate over all cells along line
                while (1){
                    // assumption we do not need to check the height for camera center cell
                    if (x0 == x1 && y0 == y1){
                        break;
                    }

                    // check if height is invalid
                    if (is_inside_map(x0,y0)){
                        int idx = y0 + (x0 * ${width});
                        if (map[get_map_idx(idx, 2)]){
                            float dis = get_l2_distance(x0_c, y0_c, x0, y0);
                            float rayheight = z0 + ( dis / total_dis * delta_z);
                            if ( map[idx] - ${tolerance_z_collision} > rayheight){
                                is_valid = false;
                                break;
                            }
                        }
                    }


                    // computation of next gridcell index in line
                    int e2 = 2 * error;
                    if (e2 >= dy){
                        if(x0 == x1){
                            break;
                        }
                        error = error + dy;
                        x0 = x0 + sx;
                    }
                    if (e2 <= dx){
                        if (y0 == y1){
                            break;
                        }
                        error = error + dx;
                        y0 = y0 + sy;
                    }
                }

                // mark the correspondence
                uv_correspondence[get_map_idx(i, 0)] = u;
                uv_correspondence[get_map_idx(i, 1)] = v;
                valid_correspondence[get_map_idx(i, 0)] = is_valid;
                """).substitute(
                height=height,
                width=width,
                resolution=resolution,
                tolerance_z_collision=tolerance_z_collision,
            ),
            name="image_to_map_correspondence_kernel",
        )
        return _image_to_map_correspondence_kernel

    def average_correspondences_to_map_kernel_cuda(width, height):
        _average_correspondences_to_map_kernel = cp.ElementwiseKernel(
            in_params="raw U sem_map, raw U map_idx, raw U image_mono, raw U uv_correspondence, raw B valid_correspondence, raw U image_height, raw U image_width",
            out_params="raw U new_sem_map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                int cell_idx = get_map_idx(i, 0);
                if (valid_correspondence[cell_idx]){
                    int cell_idx_2 = get_map_idx(i, 1);
                    int idx = int(uv_correspondence[cell_idx]) + int(uv_correspondence[cell_idx_2]) * image_width;
                    new_sem_map[get_map_idx(i, map_idx)] = image_mono[idx];
                }else{
                    new_sem_map[get_map_idx(i, map_idx)] = sem_map[get_map_idx(i, map_idx)];
                }

                """).substitute(),
            name="average_correspondences_to_map_kernel",
        )
        return _average_correspondences_to_map_kernel

    def exponential_correspondences_to_map_kernel_cuda(width, height, alpha):
        _exponential_correspondences_to_map_kernel = cp.ElementwiseKernel(
            in_params="raw U sem_map, raw U map_idx, raw U image_mono, raw U uv_correspondence, raw B valid_correspondence, raw U image_height, raw U image_width",
            out_params="raw U new_sem_map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                int cell_idx = get_map_idx(i, 0);
                if (valid_correspondence[cell_idx]){
                    int cell_idx_2 = get_map_idx(i, 1);
                    int idx = int(uv_correspondence[cell_idx]) + int(uv_correspondence[cell_idx_2]) * image_width;
                    new_sem_map[get_map_idx(i, map_idx)] = sem_map[get_map_idx(i, map_idx)] * (1-${alpha}) +  ${alpha} * image_mono[idx];
                }else{
                    new_sem_map[get_map_idx(i, map_idx)] = sem_map[get_map_idx(i, map_idx)];
                }

                """).substitute(alpha=alpha),
            name="exponential_correspondences_to_map_kernel",
        )
        return _exponential_correspondences_to_map_kernel

    def color_correspondences_to_map_kernel_cuda(width, height):
        _color_correspondences_to_map_kernel = cp.ElementwiseKernel(
            in_params="raw U sem_map, raw U map_idx, raw U image_rgb, raw U uv_correspondence, raw B valid_correspondence, raw U image_height, raw U image_width",
            out_params="raw U new_sem_map",
            preamble=string.Template("""
                __device__ int get_map_idx(int idx, int layer_n) {
                    const int layer = ${width} * ${height};
                    return layer * layer_n + idx;
                }
                """).substitute(width=width, height=height),
            operation=string.Template("""
                int cell_idx = get_map_idx(i, 0);
                if (valid_correspondence[cell_idx]){
                    int cell_idx_2 = get_map_idx(i, 1);

                    int idx_red = int(uv_correspondence[cell_idx]) + int(uv_correspondence[cell_idx_2]) * image_width;
                    int idx_green = image_width * image_height + idx_red;
                    int idx_blue = image_width * image_height * 2 + idx_red;

                    unsigned int r = image_rgb[idx_red];
                    unsigned int g = image_rgb[idx_green];
                    unsigned int b = image_rgb[idx_blue];

                    unsigned int rgb = (r<<16) + (g << 8) + b;
                    float rgb_ = __uint_as_float(rgb);
                    new_sem_map[get_map_idx(i, map_idx)] = rgb_;
                }else{
                    new_sem_map[get_map_idx(i, map_idx)] = sem_map[get_map_idx(i, map_idx)];
                }
                """).substitute(),
            name="color_correspondences_to_map_kernel",
        )
        return _color_correspondences_to_map_kernel


# =====================================================================
# CPU fallback implementations
# =====================================================================


def _make_image_to_map_correspondence_cpu(
    resolution, width, height, tolerance_z_collision
):
    def image_to_map_correspondence_cpu(
        map_,
        x1,
        y1,
        z1,
        P,
        K,
        D,
        image_height,
        image_width,
        center,
        uv_correspondence,
        valid_correspondence,
        size=None,
    ):
        cell_n = width * height
        P = np.asarray(P, dtype=np.float64).ravel()
        K = np.asarray(K, dtype=np.float64).ravel()
        D = np.asarray(D, dtype=np.float64).ravel()
        cx_f = float(center[0])
        cy_f = float(center[1])
        cz_f = float(center[2])
        x1_f = float(x1[0])
        y1_f = float(y1[0])
        z1_f = float(z1[0])
        img_w = int(image_width[0])
        img_h = int(image_height[0])

        is_D_zero = np.all(D == 0)

        for i in range(cell_n):
            if map_[2].ravel()[i] != 1:
                continue

            y0 = i % width
            x0 = i // width

            p1 = (x0 - width / 2) * resolution + cx_f
            p2 = (y0 - height / 2) * resolution + cy_f
            p3 = map_[0, x0, y0] + cz_f

            u = p1 * P[0] + p2 * P[1] + p3 * P[2] + P[3]
            v = p1 * P[4] + p2 * P[5] + p3 * P[6] + P[7]
            d = p1 * P[8] + p2 * P[9] + p3 * P[10] + P[11]

            if d <= 0:
                continue
            u = u / d
            v = v / d

            if not is_D_zero:
                k1, k2, p1_d, p2_d, k3 = D[0], D[1], D[2], D[3], D[4]
                fx, fy = K[0], K[4]
                cx_k, cy_k = K[2], K[5]
                x_norm = (u - cx_k) / fx
                y_norm = (v - cy_k) / fy
                r2 = x_norm * x_norm + y_norm * y_norm
                radial = 1 + k1 * r2 + k2 * r2 * r2 + k3 * r2 * r2 * r2
                u_corr = (
                    x_norm * radial
                    + 2 * p1_d * x_norm * y_norm
                    + p2_d * (r2 + 2 * x_norm * x_norm)
                )
                v_corr = (
                    y_norm * radial
                    + 2 * p2_d * x_norm * y_norm
                    + p1_d * (r2 + 2 * y_norm * y_norm)
                )
                u = fx * u_corr + cx_k
                v = fy * v_corr + cy_k

            if u < 0 or v < 0 or u >= img_w or v >= img_h:
                continue

            x0_c, y0_c = x0, y0
            total_dis = np.sqrt((x0_c - x1_f) ** 2 + (y0_c - y1_f) ** 2)
            z0 = map_[0, x0_c, y0_c]
            delta_z = z1_f - z0

            # Bresenham line algorithm
            dx_c = abs(int(x1_f) - x0)
            sx = 1 if x0 < x1_f else -1
            dy_c = -abs(int(y1_f) - y0)
            sy = 1 if y0 < y1_f else -1
            err = dx_c + dy_c

            bx, by = x0, y0
            is_valid = True

            while True:
                if bx == int(x1_f) and by == int(y1_f):
                    break

                if 0 <= bx < width and 0 <= by < height:
                    idx = by + bx * width
                    if map_[2].ravel()[idx]:
                        dis = np.sqrt((x0_c - bx) ** 2 + (y0_c - by) ** 2)
                        rayheight = z0 + (dis / total_dis * delta_z)
                        if map_[0, bx, by] - tolerance_z_collision > rayheight:
                            is_valid = False
                            break

                e2 = 2 * err
                if e2 >= dy_c:
                    if bx == int(x1_f):
                        break
                    err += dy_c
                    bx += sx
                if e2 <= dx_c:
                    if by == int(y1_f):
                        break
                    err += dx_c
                    by += sy

            uv_correspondence[0, x0, y0] = u
            uv_correspondence[1, x0, y0] = v
            valid_correspondence[0, x0, y0] = float(is_valid)

    return image_to_map_correspondence_cpu


def _make_average_correspondences_to_map_cpu(width, height):
    def average_correspondences_to_map_cpu(
        sem_map,
        map_idx,
        image_mono,
        uv_correspondence,
        valid_correspondence,
        image_height,
        image_width,
        new_sem_map,
        size=None,
    ):
        img_w = int(image_width[0])
        valid = valid_correspondence[0]
        u = uv_correspondence[0]
        v = uv_correspondence[1]
        valid_mask = valid > 0.5

        ui = u[valid_mask].astype(int)
        vi = v[valid_mask].astype(int)
        img_idx = np.clip(ui + vi * img_w, 0, image_mono.size - 1)

        map_idx_val = int(map_idx[0] if hasattr(map_idx, "__len__") else map_idx)
        new_sem_map[map_idx_val][valid_mask] = image_mono.ravel()[img_idx]
        new_sem_map[:, ~valid_mask] = sem_map[:, ~valid_mask]

    return average_correspondences_to_map_cpu


def _make_exponential_correspondences_to_map_cpu(width, height, alpha):
    def exponential_correspondences_to_map_cpu(
        sem_map,
        map_idx,
        image_mono,
        uv_correspondence,
        valid_correspondence,
        image_height,
        image_width,
        new_sem_map,
        size=None,
    ):
        img_w = int(image_width[0])
        valid = valid_correspondence[0]
        u = uv_correspondence[0]
        v = uv_correspondence[1]
        valid_mask = valid > 0.5

        ui = u[valid_mask].astype(int)
        vi = v[valid_mask].astype(int)
        img_idx = np.clip(ui + vi * img_w, 0, image_mono.size - 1)

        map_idx_val = int(map_idx[0] if hasattr(map_idx, "__len__") else map_idx)
        new_sem_map[map_idx_val][valid_mask] = (
            sem_map[map_idx_val][valid_mask] * (1 - alpha)
            + alpha * image_mono.ravel()[img_idx]
        )
        new_sem_map[:, ~valid_mask] = sem_map[:, ~valid_mask]

    return exponential_correspondences_to_map_cpu


def _make_color_correspondences_to_map_cpu(width, height):
    def color_correspondences_to_map_cpu(
        sem_map,
        map_idx,
        image_rgb,
        uv_correspondence,
        valid_correspondence,
        image_height,
        image_width,
        new_sem_map,
        size=None,
    ):
        img_w = int(image_width[0])
        img_h = int(image_height[0])
        valid = valid_correspondence[0]
        u = uv_correspondence[0]
        v = uv_correspondence[1]
        valid_mask = valid > 0.5

        ui = u[valid_mask].astype(int)
        vi = v[valid_mask].astype(int)
        base_idx = np.clip(ui + vi * img_w, 0, img_w * img_h - 1)

        img_flat = image_rgb.ravel()
        r = img_flat[base_idx].astype(np.uint32)
        g = img_flat[img_w * img_h + base_idx].astype(np.uint32)
        b = img_flat[2 * img_w * img_h + base_idx].astype(np.uint32)

        rgb_int = (r << 16) | (g << 8) | b
        rgb_float = np.frombuffer(
            rgb_int.astype(np.uint32).tobytes(), dtype=np.float32
        ).copy()

        map_idx_val = int(map_idx[0] if hasattr(map_idx, "__len__") else map_idx)
        new_sem_map[map_idx_val][valid_mask] = rgb_float
        new_sem_map[:, ~valid_mask] = sem_map[:, ~valid_mask]

    return color_correspondences_to_map_cpu


# =====================================================================
# Public API — dispatch between CUDA and CPU
# =====================================================================


def image_to_map_correspondence_kernel(
    resolution, width, height, tolerance_z_collision
):
    if GPU_AVAILABLE:
        return image_to_map_correspondence_kernel_cuda(
            resolution, width, height, tolerance_z_collision
        )
    return _make_image_to_map_correspondence_cpu(
        resolution, width, height, tolerance_z_collision
    )


def average_correspondences_to_map_kernel(width, height):
    if GPU_AVAILABLE:
        return average_correspondences_to_map_kernel_cuda(width, height)
    return _make_average_correspondences_to_map_cpu(width, height)


def exponential_correspondences_to_map_kernel(width, height, alpha):
    if GPU_AVAILABLE:
        return exponential_correspondences_to_map_kernel_cuda(width, height, alpha)
    return _make_exponential_correspondences_to_map_cpu(width, height, alpha)


def color_correspondences_to_map_kernel(width, height):
    if GPU_AVAILABLE:
        return color_correspondences_to_map_kernel_cuda(width, height)
    return _make_color_correspondences_to_map_cpu(width, height)
