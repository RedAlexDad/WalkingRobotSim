"""Анализ ошибок бенчмарка: confusion GT->prediction и контактные листы."""
import json
import os

import cv2
import numpy as np
from ultralytics import YOLO

BASE = "data/gazebo/exp"
FRAMES = os.path.join(BASE, "frames")
W, H = 640, 480
HFOV = 1.047
FX = FY = (W / 2.0) / np.tan(HFOV / 2.0)
CX, CY = W / 2.0, H / 2.0

MODELS = [
    ("yolov8n", "src/quadropted_perception/models/yolov8n.pt"),
    ("yolov8s", "src/quadropted_perception/models/yolov8s.pt"),
    ("yolov10n", "src/quadropted_perception/models/yolov10n.pt"),
    ("yolov9t", "src/quadropted_perception/models/yolov9t.pt"),
    ("yolo11n", "/tmp/opencode/yolo11n.pt"),
]


def rot(yaw, pitch, roll):
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return rz @ ry @ rx


def project(pts, pose):
    cam = np.array(pose[:3])
    r = rot(pose[5], pose[4], pose[3])
    fwd = r @ np.array([1.0, 0.0, 0.0])
    up = r @ np.array([0.0, 0.0, 1.0])
    right = np.cross(fwd, up)
    v = np.asarray(pts, dtype=float) - cam
    xc, yc, zc = v @ right, v @ up, v @ fwd
    safe = np.where(np.abs(zc) < 1e-9, 1e-9, zc)
    return np.stack([CX + FX * xc / safe, CY - FY * yc / safe], axis=1), zc


def corners(obj):
    lo, hi = np.array(obj["bbox"][0]), np.array(obj["bbox"][1])
    pts = np.array([[x, y, z] for x in (lo[0], hi[0])
                    for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    yaw = obj["pose"][5]
    c, s = np.cos(yaw), np.sin(yaw)
    rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return pts @ rz.T + np.array(obj["pose"][:3])


def gts_for(view, objects):
    out = []
    for o in objects:
        uv, zc = project(corners(o), view["pose"])
        if np.any(zc <= 0.1):
            continue
        x1, y1 = uv.min(axis=0)
        x2, y2 = uv.max(axis=0)
        full = max((x2 - x1) * (y2 - y1), 1e-6)
        cx1, cy1, cx2, cy2 = max(x1, 0), max(y1, 0), min(x2, W), min(y2, H)
        if cx2 - cx1 < 8 or cy2 - cy1 < 8:
            continue
        if (cx2 - cx1) * (cy2 - cy1) / full < 0.35:
            continue
        out.append((o["class"], [cx1, cy1, cx2, cy2]))
    return out


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    aa = (a[2] - a[0]) * (a[3] - a[1])
    ab = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (aa + ab - inter + 1e-9)


def best_frame(v):
    d = os.path.join(FRAMES, v)
    files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    best, std = None, -1
    for f in files:
        im = cv2.imread(os.path.join(d, f))
        if im is not None and im.std() > std:
            best, std = os.path.join(d, f), im.std()
    return best


def sheet(model):
    d = os.path.join(FRAMES, "annotated", model)
    views = sorted(f[:-4] for f in os.listdir(d) if f.endswith(".png"))
    cols, rows = 8, 6
    tw, th = 320, 240
    canvas = np.full((rows * (th + 18) + 22, cols * tw, 3), 255, np.uint8)
    cv2.putText(canvas,
                "зелёный — детекция (класс, %); жёлтый — GT; TP = IoU>=0.5 и класс совпал",
                (8, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
    for i, v in enumerate(views):
        im = cv2.imread(os.path.join(d, v + ".png"))
        im = cv2.resize(im, (tw, th))
        r, c = divmod(i, cols)
        y0, x0 = 22 + r * (th + 18), c * tw
        canvas[y0:y0 + th, x0:x0 + tw] = im
        cv2.putText(canvas, v, (x0 + 4, y0 + th + 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
    out = os.path.join(FRAMES, f"annotated_{model}_sheet.png")
    cv2.imwrite(out, canvas)
    print("sheet:", out)


def main():
    scene = json.load(open(os.path.join(BASE, "scene.json"), encoding="utf-8"))
    views, objects = scene["views"], scene["objects"]
    gt = {v["name"]: gts_for(v, objects) for v in views}

    for tag, path in MODELS:
        if not os.path.exists(path):
            continue
        model = YOLO(path)
        names = model.names
        confusion = {}
        n_gt = 0
        for v in views:
            im = cv2.imread(best_frame(v["name"]))
            r = model.predict(im, conf=0.05, verbose=False)[0]
            dets = [(names[int(k)], [float(x) for x in b], float(c))
                    for k, b, c in zip(r.boxes.cls, r.boxes.xyxy, r.boxes.conf)]
            for cls, box in gt[v["name"]]:
                n_gt += 1
                best, best_iou = "miss", 0.0
                for dcls, dbox, conf in dets:
                    v_iou = iou(box, dbox)
                    if v_iou > best_iou:
                        best, best_iou = dcls, v_iou
                key = f"{cls} -> {best}" if best_iou >= 0.5 else f"{cls} -> MISS"
                confusion[key] = confusion.get(key, 0) + 1
        print("\n", tag, "GT:", n_gt)
        for k in sorted(confusion, key=lambda x: -confusion[x]):
            print(f"  {confusion[k]:3d}  {k}")
        with open(os.path.join(BASE, f"confusion_{tag}.json"), "w", encoding="utf-8") as f:
            json.dump({"n_gt": n_gt, "confusion": confusion}, f,
                      ensure_ascii=False, indent=2)
        sheet(tag)


if __name__ == "__main__":
    main()
