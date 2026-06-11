#!/usr/bin/env python3
"""
Benchmark v2: CPU fallback optimizations with numba @njit (bit-identical).

Требование: atoi не более 1e-9 (bit-identical).
Numba JIT компилирует Python-циклы в машинный код без изменения алгоритма.
"""

import time
import numpy as np
from scipy.ndimage import minimum_filter, maximum_filter
from numba import njit

np.random.seed(42)


# ============================================================
# 1. min_filter
# ============================================================
def min_filter_python(orig_map, orig_mask, dilation, h, w):
    result = orig_map.copy()
    result_mask = orig_mask.copy()
    for i in range(h * w):
        if orig_mask.flat[i] >= 0.5:
            continue
        iy = i // w
        ix = i % w
        min_val = 1e6
        for dy in range(-dilation, dilation + 1):
            for dx in range(-dilation, dilation + 1):
                ny = iy + dy
                nx = ix + dx
                if nx <= 0 or nx >= w - 1 or ny <= 0 or ny >= h - 1:
                    continue
                if result_mask[ny, nx] > 0.5 and result[ny, nx] < min_val:
                    min_val = result[ny, nx]
        if min_val < 1e6 - 1:
            result.flat[i] = min_val
            result_mask.flat[i] = 0.6
    return result, result_mask


@njit
def min_filter_numba(orig_map, orig_mask, dilation, h, w):
    result = orig_map.copy()
    result_mask = orig_mask.copy()
    for i in range(h * w):
        if orig_mask.flat[i] >= 0.5:
            continue
        iy = i // w
        ix = i % w
        min_val = 1e6
        for dy in range(-dilation, dilation + 1):
            for dx in range(-dilation, dilation + 1):
                ny = iy + dy
                nx = ix + dx
                if nx <= 0 or nx >= w - 1 or ny <= 0 or ny >= h - 1:
                    continue
                if result_mask[ny, nx] > 0.5 and result[ny, nx] < min_val:
                    min_val = result[ny, nx]
        if min_val < 1e6 - 1:
            result.flat[i] = min_val
            result_mask.flat[i] = 0.6
    return result, result_mask


# ============================================================
# 2. max_filter
# ============================================================
def max_filter_python(h, w, dilation, prev_map, prev_mask):
    result = prev_map.copy()
    result_mask = prev_mask.copy()
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
            result.flat[i] = max_val
            result_mask.flat[i] = 0.6
    return result, result_mask


@njit
def max_filter_numba(h, w, dilation, prev_map, prev_mask):
    result = prev_map.copy()
    result_mask = prev_mask.copy()
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
            result.flat[i] = max_val
            result_mask.flat[i] = 0.6
    return result, result_mask


# ============================================================
# 3. error_counting
# ============================================================
def error_counting_python(map_, p, center_x, center_y, R, t,
                          width, height, resolution,
                          min_valid_distance, max_height_range,
                          ramped_height_range_a, ramped_height_range_b,
                          ramped_height_range_c,
                          mahalanobis_thresh, outlier_variance,
                          traversability_inlier):
    n_points = p.shape[0]
    Rf = R.ravel()
    tf = t.ravel()
    rx, ry, rz = p[:, 0], p[:, 1], p[:, 2]
    with np.errstate(invalid="ignore"):
        x = Rf[0] * rx + Rf[1] * ry + Rf[2] * rz + tf[0]
        y = Rf[3] * rx + Rf[4] * ry + Rf[5] * rz + tf[1]
        z = Rf[6] * rx + Rf[7] * ry + Rf[8] * rz + tf[2]
        cx, cy = float(center_x[0]), float(center_y[0])
        cols = np.clip(((x - cx) / resolution + 0.5 * width).astype(int), 0, width - 1)
        rows = np.clip(((y - cy) / resolution + 0.5 * height).astype(int), 0, height - 1)
        sensor_dist2 = (x - tf[0]) ** 2 + (y - tf[1]) ** 2 + (z - tf[2]) ** 2
        dxy = np.maximum(np.sqrt(x * x + y * y) - ramped_height_range_b, 0.0)

    finite = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    valid = np.ones(n_points, dtype=bool)
    valid &= sensor_dist2 >= min_valid_distance * min_valid_distance
    valid &= (z - tf[2]) <= dxy * ramped_height_range_a + ramped_height_range_c
    valid &= (z - tf[2]) <= max_height_range
    valid &= finite
    inside = (cols > 0) & (cols < width - 1) & (rows > 0) & (rows < height - 1)
    process = valid & inside
    process_idx = np.where(process)[0]
    newmap = np.zeros_like(map_)

    error_total = 0.0
    error_cnt_total = 0
    for idx in process_idx:
        r, c = rows[idx], cols[idx]
        map_h = map_[0, r, c]
        map_v = map_[1, r, c]
        map_valid = map_[2, r, c]
        map_t = map_[3, r, c]
        if (map_valid > 0.5
            and abs(map_h - z[idx]) < (map_v * mahalanobis_thresh)
            and map_v < outlier_variance / 2.0
            and map_t > traversability_inlier):
            e = z[idx] - map_h
            error_total += e
            error_cnt_total += 1
            newmap[3, r, c] += 1.0
        newmap[4, r, c] += 1.0

    error = np.array([error_total])
    error_cnt = np.array([error_cnt_total])
    return newmap, error, error_cnt


@njit
def error_counting_numba_inner(map_, rows, cols, z, process_idx,
                               mahalanobis_thresh, outlier_variance,
                               traversability_inlier):
    newmap = np.zeros_like(map_)
    error_total = 0.0
    error_cnt_total = 0
    for idx_idx in range(len(process_idx)):
        idx = process_idx[idx_idx]
        r, c = rows[idx], cols[idx]
        map_h = map_[0, r, c]
        map_v = map_[1, r, c]
        map_valid = map_[2, r, c]
        map_t = map_[3, r, c]
        if (map_valid > 0.5
            and abs(map_h - z[idx]) < (map_v * mahalanobis_thresh)
            and map_v < outlier_variance / 2.0
            and map_t > traversability_inlier):
            e = z[idx] - map_h
            error_total += e
            error_cnt_total += 1
            newmap[3, r, c] += 1.0
        newmap[4, r, c] += 1.0
    return newmap, error_total, error_cnt_total


# ============================================================
# 4. base_elevation
# ============================================================
def base_elevation_python(elevation_map, mask, rotation, h, w, res, use_th, th):
    result = np.zeros_like(elevation_map)
    R_flat = rotation.ravel()
    for i in range(h * w):
        if mask.flat[i] <= 0.5:
            continue
        row = i // w
        col = i % w
        rx = row * res
        ry = col * res
        rz = elevation_map.flat[i]
        z_b = R_flat[6] * rx + R_flat[7] * ry + R_flat[8] * rz
        if use_th and z_b >= th:
            result.flat[i] = 1.0
        elif use_th and z_b < th:
            result.flat[i] = 0.0
        else:
            result.flat[i] = z_b
    return result


@njit
def base_elevation_numba(elevation_map, mask, rotation, h, w, res, use_th, th):
    result = np.zeros_like(elevation_map)
    r6, r7, r8 = rotation[2, 0], rotation[2, 1], rotation[2, 2]
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
            result.flat[i] = 1.0
        elif use_th and z_b < th:
            result.flat[i] = 0.0
        else:
            result.flat[i] = z_b
    return result


# ============================================================
# 5. sum_kernel
# ============================================================
def sum_kernel_python(p, map_lay, pcl_channels, map_, h, w):
    newmap = np.zeros_like(map_)
    n_points = p.shape[0]
    for idx in range(n_points):
        ux = int(p[idx, 0])
        uy = int(p[idx, 1])
        if ux < 0 or ux >= w or uy < 0 or uy >= h:
            continue
        for li in range(map_lay):
            newmap[li, uy, ux] += p[idx, 3 + li]
    return newmap


@njit
def sum_kernel_numba(p, map_lay, map_, h, w):
    newmap = np.zeros_like(map_)
    n_points = p.shape[0]
    for idx in range(n_points):
        ux = int(p[idx, 0])
        uy = int(p[idx, 1])
        if ux < 0 or ux >= w or uy < 0 or uy >= h:
            continue
        for li in range(map_lay):
            newmap[li, uy, ux] += p[idx, 3 + li]
    return newmap


# ============================================================
# Benchmark runner
# ============================================================
def verify(a, b, name):
    if isinstance(a, tuple):
        return all(verify(aa, bb, f"{name}[{i}]") for i, (aa, bb) in enumerate(zip(a, b)))
    diff = np.max(np.abs(a - b))
    ok = diff < 1e-9
    if not ok:
        print(f"  ⚠ {name}: max diff = {diff:.2e}  EXCEEDS 1e-9!")
    return ok


def bench(name, fn_py, fn_opt, *args, warmup=3, runs=20):
    # Warmup
    for _ in range(warmup):
        r_py = fn_py(*args)
        r_opt = fn_opt(*args)

    t_py = []
    t_opt = []
    r_py_last = None
    r_opt_last = None
    for _ in range(runs):
        t0 = time.perf_counter()
        r_py_last = fn_py(*args)
        t1 = time.perf_counter()
        r_opt_last = fn_opt(*args)
        t2 = time.perf_counter()
        t_py.append(t1 - t0)
        t_opt.append(t2 - t1)

    med_py = np.median(t_py)
    med_opt = np.median(t_opt)
    speedup = med_py / med_opt if med_opt > 0 else float('inf')
    match = verify(r_py_last, r_opt_last, name)

    print(f"  {name:35s}  Python={med_py*1000:8.2f}ms  opt={med_opt*1000:8.2f}ms  "
          f"speedup={speedup:5.1f}x  match={match}")
    return med_py, med_opt, speedup, match


if __name__ == "__main__":
    print("=" * 80)
    print("CPU OPTIMIZATION BENCHMARK v2 — bit-identical (1e-9)")
    print("=" * 80)
    print()

    H, W = 200, 200
    print(f"Map size: {H}x{W}")

    mask = np.zeros((H, W), dtype=np.float32)
    mask[10:190, 10:190] = 1.0
    elevation = np.random.uniform(-1.0, 2.0, (H, W)).astype(np.float32)
    rotation = np.eye(3, dtype=np.float32)

    # 1. min_filter
    print("\n--- 1. min_filter (dilation=5) ---")
    _, _, spd1, ok1 = bench("_min_filter_cpu (numba)",
                            min_filter_python, min_filter_numba,
                            elevation, mask, 5, H, W)

    # 2. max_filter
    print("\n--- 2. max_filter (dilation=5) ---")
    _, _, spd2, ok2 = bench("_max_filter_cpu (numba)",
                            max_filter_python, max_filter_numba,
                            H, W, 5, elevation, mask)

    # 3. error_counting
    print("\n--- 3. error_counting (50K points) ---")
    N_POINTS = 50000
    p = np.random.uniform(-10, 10, (N_POINTS, 3)).astype(np.float32)
    center = np.array([0.0, 0.0], dtype=np.float32)
    t_vec = np.zeros(3, dtype=np.float32)
    map_layers = np.zeros((5, H, W), dtype=np.float32)

    # Numba version for error_counting: vectorized pre-filter + numba inner loop
    def error_counting_numba_wrapper(map_, p, center_x, center_y, R, t,
                                      width, height, resolution,
                                      min_valid_distance, max_height_range,
                                      ramped_height_range_a, ramped_height_range_b,
                                      ramped_height_range_c,
                                      mahalanobis_thresh, outlier_variance,
                                      traversability_inlier):
        n_points = p.shape[0]
        Rf = R.ravel()
        tf = t.ravel()
        rx, ry, rz = p[:, 0], p[:, 1], p[:, 2]
        with np.errstate(invalid="ignore"):
            x = Rf[0] * rx + Rf[1] * ry + Rf[2] * rz + tf[0]
            y = Rf[3] * rx + Rf[4] * ry + Rf[5] * rz + tf[1]
            z = Rf[6] * rx + Rf[7] * ry + Rf[8] * rz + tf[2]
            cx, cy = float(center_x[0]), float(center_y[0])
            cols = np.clip(((x - cx) / resolution + 0.5 * width).astype(int), 0, width - 1)
            rows = np.clip(((y - cy) / resolution + 0.5 * height).astype(int), 0, height - 1)
            sensor_dist2 = (x - tf[0]) ** 2 + (y - tf[1]) ** 2 + (z - tf[2]) ** 2
            dxy = np.maximum(np.sqrt(x * x + y * y) - ramped_height_range_b, 0.0)

        finite = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        valid = np.ones(n_points, dtype=bool)
        valid &= sensor_dist2 >= min_valid_distance * min_valid_distance
        valid &= (z - tf[2]) <= dxy * ramped_height_range_a + ramped_height_range_c
        valid &= (z - tf[2]) <= max_height_range
        valid &= finite
        inside = (cols > 0) & (cols < width - 1) & (rows > 0) & (rows < height - 1)
        process = valid & inside
        process_idx = np.where(process)[0]

        newmap, err_tot, err_cnt = error_counting_numba_inner(
            map_, rows, cols, z, process_idx,
            mahalanobis_thresh, outlier_variance, traversability_inlier
        )
        return newmap, np.array([err_tot]), np.array([err_cnt])

    _, _, spd3, ok3 = bench("error_counting_cpu (numba)",
                            error_counting_python,
                            error_counting_numba_wrapper,
                            map_layers, p, center, center, rotation, t_vec,
                            W, H, 0.1, 0.3, 3.0, 0.3, 1.0, 0.2, 2.0, 0.01, 0.9)

    # 4. base_elevation
    print("\n--- 4. base_elevation ---")
    _, _, spd4, ok4 = bench("_base_elevation_cpu (numba)",
                            base_elevation_python, base_elevation_numba,
                            elevation, mask, rotation, H, W, 0.1, False, 0.0)

    # 5. sum_kernel
    print("\n--- 5. semantic sum_kernel (50K points, 3 layers) ---")
    sem_p = np.random.uniform(0, W, (N_POINTS, 6)).astype(np.float32)
    sem_p[:, 0] = np.clip(sem_p[:, 0], 0, W - 1)
    sem_p[:, 1] = np.clip(sem_p[:, 1], 0, H - 1)
    sem_map = np.zeros((3, H, W), dtype=np.float32)

    def sum_kernel_numba_wrapper(p, map_lay, pcl_channels, map_, h, w):
        return sum_kernel_numba(p, map_lay, map_, h, w)

    _, _, spd5, ok5 = bench("sum_kernel_cpu (numba)",
                            sum_kernel_python, sum_kernel_numba_wrapper,
                            sem_p, 3, 6, sem_map, H, W)

    # ============================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    all_ok = ok1 and ok2 and ok3 and ok4 and ok5
    print(f"  Все результаты bit-identical (< 1e-9): {'✅ ДА' if all_ok else '❌ НЕТ'}")
    print()
    print(f"  min_filter:       {spd1:5.1f}x ускорение")
    print(f"  max_filter:       {spd2:5.1f}x ускорение")
    print(f"  error_counting:   {spd3:5.1f}x ускорение")
    print(f"  base_elevation:   {spd4:5.1f}x ускорение")
    print(f"  sum_kernel:       {spd5:5.1f}x ускорение")
    print()
    print("  Метод: @njit декоратор — компилирует Python-циклы в машинный код")
    print("  без изменения алгоритма. Результат идентичен до 1e-9.")
    print("  Ни одной строки C++, ни одной новой зависимости (numba уже есть).")
