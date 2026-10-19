"""Пилотная оценка YOLO на кадрах Gazebo (5 стульев, 4 ракурса, CPU).

GT строится проекцией 3D-габаритов стула на изображение по известной
позе камеры и внутренним параметрам. AP@0.5 считается без учёта класса.
"""
import json
import os
import resource
import statistics
import time

import cv2
import numpy as np
from ultralytics import YOLO

W, H = 640, 480
HFOV = 1.047
FX = FY = (W / 2.0) / np.tan(HFOV / 2.0)
CX, CY = W / 2.0, H / 2.0

POSES = {
    "pose0": (0.0, -6.0, 2.5, 0.0, 0.3948, 1.5708),
    "pose1": (0.0, -5.0, 3.2, 0.0, 0.55, 1.5708),
    "pose2": (-1.5, -6.5, 2.0, 0.0, 0.35, 1.45),
    "pose3": (1.5, -6.5, 2.0, 0.0, 0.35, 1.69),
}

# Габариты ChairA_01 (DAE в см -> м), поворот модели на 90 град.
HX, HY, HZ = 0.2368, 0.2186, 0.9130
CHAIR_X = [-3.0, -1.5, 0.0, 1.5, 3.0]

FRAMES = "data/gazebo/exp/frames"


def rot(yaw, pitch, roll):
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return rz @ ry @ rx


def gt_boxes(pose):
    cam = np.array(pose[:3])
    r = rot(pose[5], pose[4], pose[3])
    fwd = r @ np.array([1.0, 0.0, 0.0])
    up = r @ np.array([0.0, 0.0, 1.0])
    right = np.cross(fwd, up)

    def project(p):
        v = np.asarray(p, dtype=float) - cam
        xc, yc, zc = v @ right, v @ up, v @ fwd
        return CX + FX * xc / zc, CY - FY * yc / zc

    boxes = []
    for x in CHAIR_X:
        corners = []
        for dx in (-HX, HX):
            for dy in (-HY, HY):
                for z in (0.0, HZ):
                    corners.append(project([x + dx, dy, z]))
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        boxes.append([min(xs), min(ys), max(xs), max(ys)])
    return np.clip(np.array(boxes), [0, 0, 0, 0], [W, H, W, H])


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter + 1e-9)


def match_frame(dets, gts, thr=0.5):
    """Возвращает список (conf, tp) для кадра."""
    order = sorted(range(len(dets)), key=lambda i: -dets[i][0])
    used = np.zeros(len(gts), dtype=bool)
    out = []
    for i in order:
        conf, box = dets[i]
        best, best_iou = -1, 0.0
        for j, g in enumerate(gts):
            if used[j]:
                continue
            v = iou(box, g)
            if v > best_iou:
                best, best_iou = j, v
        tp = best_iou >= thr
        if tp:
            used[best] = True
        out.append((conf, tp))
    return out


def average_precision(records, n_gt, thr=0.5):
    if n_gt == 0:
        return None
    records = sorted(records, key=lambda r: -r[0])
    if not records:
        return 0.0
    tp = np.cumsum([1 if r[1] else 0 for r in records])
    fp = np.cumsum([0 if r[1] else 1 for r in records])
    recall = tp / n_gt
    precision = tp / np.maximum(tp + fp, 1)
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([1.0], precision, [0.0]))
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def frame_path(pose_dir):
    d = os.path.join(FRAMES, pose_dir)
    files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    # берём кадр с максимальной дисперсией (не пустой)
    best, best_std = None, -1.0
    for f in files:
        im = cv2.imread(os.path.join(d, f))
        std = float(im.std())
        if std > best_std:
            best, best_std = os.path.join(d, f), std
    return best


def measure(model_path, runs=60):
    model = YOLO(model_path)
    img = cv2.imread(frame_path("pose0"))
    model.predict(img, conf=0.001, verbose=False)

    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        model.predict(img, conf=0.001, verbose=False)
        times.append(time.perf_counter() - t0)

    records = []
    n_gt = 0
    n_det_050 = 0
    n_det_001 = 0
    conf_max = 0.0
    for pose_dir, pose in POSES.items():
        im = cv2.imread(frame_path(pose_dir))
        r = model.predict(im, conf=0.001, verbose=False)[0]
        dets = [(float(c), [float(v) for v in b]) for c, b in zip(r.boxes.conf, r.boxes.xyxy)]
        gts = gt_boxes(pose)
        records.extend(match_frame(dets, gts, 0.5))
        n_gt += len(gts)
        n_det_001 += len(dets)
        n_det_050 += sum(1 for c, _ in dets if c >= 0.5)
        conf_max = max(conf_max, max((c for c, _ in dets), default=0.0))

    return {
        "model": os.path.basename(model_path),
        "T_median": statistics.median(times),
        "T_mean": statistics.mean(times),
        "T_std": statistics.pstdev(times),
        "f_hz": 1.0 / statistics.median(times),
        "AP50": average_precision(records, n_gt, 0.5),
        "n_gt": n_gt,
        "n_frames": len(POSES),
        "n_det_050": n_det_050,
        "n_det_001": n_det_001,
        "conf_max": conf_max,
        "params_m": sum(p.numel() for p in model.model.parameters()) / 1e6,
        "size_mb": os.path.getsize(model_path) / 1e6,
    }


if __name__ == "__main__":
    for pose_dir, pose in POSES.items():
        gts = gt_boxes(pose)
        print(pose_dir, "GT:", [[round(float(v), 1) for v in g] for g in gts])

    out = []
    for path in [
        "src/quadropted_perception/models/yolov8n.pt",
        "/tmp/opencode/yolo11n.pt",
        "src/quadropted_perception/models/yolov10n.pt",
    ]:
        if not os.path.exists(path):
            continue
        res = measure(path)
        out.append(res)
        print(json.dumps(res, ensure_ascii=False))

    with open("data/gazebo/exp/results.json", "w", encoding="utf-8") as f:
        json.dump({"poses": POSES, "results": out}, f, ensure_ascii=False, indent=2)
