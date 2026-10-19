"""Бенчмарк YOLO на сцене Gazebo: 16 объектов, 9 COCO-классов, 24 ракурса.

Считает class-aware AP@0.5, mAP@0.5:0.95, P/R/F1 при conf 0.5, время
инференса и сохраняет аннотированные кадры (bbox + confidence).
"""
import argparse
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statistics
import time

import cv2
import numpy as np
from ultralytics import YOLO

W, H = 640, 480
HFOV = 1.047
FX = FY = (W / 2.0) / np.tan(HFOV / 2.0)
CX, CY = W / 2.0, H / 2.0

BASE = "data/gazebo/exp"
SCENE = os.path.join(BASE, "scene.json")
FRAMES = os.path.join(BASE, "frames")

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
    u = CX + FX * xc / np.where(np.abs(zc) < 1e-9, 1e-9, zc)
    w = CY - FY * yc / np.where(np.abs(zc) < 1e-9, 1e-9, zc)
    return np.stack([u, w], axis=1), zc


def object_corners(obj):
    lo, hi = np.array(obj["bbox"][0]), np.array(obj["bbox"][1])
    pts = np.array([[x, y, z] for x in (lo[0], hi[0])
                    for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    yaw = obj["pose"][5]
    c, s = np.cos(yaw), np.sin(yaw)
    rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return pts @ rz.T + np.array(obj["pose"][:3])


def gt_for_view(view, objects):
    out = []
    for o in objects:
        pts = object_corners(o)
        uv, zc = project(pts, view["pose"])
        if np.any(zc <= 0.1):
            continue
        x1, y1 = uv.min(axis=0)
        x2, y2 = uv.max(axis=0)
        full = max((x2 - x1) * (y2 - y1), 1e-6)
        cx1, cy1 = max(x1, 0), max(y1, 0)
        cx2, cy2 = min(x2, W), min(y2, H)
        if cx2 - cx1 < 8 or cy2 - cy1 < 8:
            continue
        vis = (cx2 - cx1) * (cy2 - cy1) / full
        if vis < 0.35:
            continue
        out.append({
            "class": o["class"],
            "box": [float(cx1), float(cy1), float(cx2), float(cy2)],
            "name": o["name"],
            "vis": float(vis),
        })
    return out


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    aa = (a[2] - a[0]) * (a[3] - a[1])
    ab = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (aa + ab - inter + 1e-9)


def match_view(dets, gts, thr):
    """dets: [(conf, cls, box)], gts: [dict]. Возвращает {(cls): [(conf,tp)]}."""
    by_cls = {}
    for conf, cls, box in sorted(dets, key=lambda d: -d[0]):
        by_cls.setdefault(cls, []).append((conf, box))
    rec = {}
    for cls, dlist in by_cls.items():
        glist = [g for g in gts if g["class"] == cls]
        used = np.zeros(len(glist), dtype=bool)
        rows = []
        for conf, box in dlist:
            best, best_iou = -1, 0.0
            for j, g in enumerate(glist):
                if used[j]:
                    continue
                v = iou(box, g["box"])
                if v > best_iou:
                    best, best_iou = j, v
            tp = best_iou >= thr
            if tp:
                used[best] = True
            rows.append((conf, tp))
        rec[cls] = rows
    return rec


def ap_from_records(records, n_gt):
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


def pr_points(records, n_gt):
    records = sorted(records, key=lambda r: -r[0])
    tp = np.cumsum([1 if r[1] else 0 for r in records])
    fp = np.cumsum([0 if r[1] else 1 for r in records])
    rec = tp / max(n_gt, 1)
    prec = tp / np.maximum(tp + fp, 1)
    return {"recall": rec.tolist(), "precision": prec.tolist()}


def best_frame(view_name):
    d = os.path.join(FRAMES, view_name)
    files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    best, best_std = None, -1
    for f in files:
        im = cv2.imread(os.path.join(d, f))
        std = float(im.std())
        if std > best_std:
            best, best_std = os.path.join(d, f), std
    return best


def load_scene():
    with open(SCENE, encoding="utf-8") as f:
        return json.load(f)


def draw(im, dets, gts, names):
    out = im.copy()
    for g in gts:
        x1, y1, x2, y2 = [int(round(v)) for v in g["box"]]
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 220, 255), 1)
        cv2.putText(out, f"GT {g['class']}", (x1 + 2, max(y1 - 4, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 255), 1, cv2.LINE_AA)
    for conf, cls, box in dets:
        x1, y1, x2, y2 = [int(round(v)) for v in box]
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{cls} {conf * 100:.0f}%"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(out, (x1, y1 - th - 6), (x1 + tw + 4, y1), (0, 255, 0), -1)
        cv2.putText(out, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt-only", action="store_true")
    args = ap.parse_args()

    scene = load_scene()
    views, objects = scene["views"], scene["objects"]

    if args.gt_only:
        for v in views[:3]:
            im = cv2.imread(best_frame(v["name"]))
            gts = gt_for_view(v, objects)
            out = draw(im, [], gts, {})
            os.makedirs(os.path.join(BASE, "gt_check"), exist_ok=True)
            p = os.path.join(BASE, "gt_check", v["name"] + ".png")
            cv2.imwrite(p, out)
            print(v["name"], "GT:", [(g["class"], [round(x) for x in g["box"]]) for g in gts])
        return

    # GT по всем ракурсам
    gt_by_view = {v["name"]: gt_for_view(v, objects) for v in views}
    n_gt_class = {}
    for gts in gt_by_view.values():
        for g in gts:
            n_gt_class[g["class"]] = n_gt_class.get(g["class"], 0) + 1
    print("GT instances:", sum(n_gt_class.values()), n_gt_class)

    results = []
    for tag, path in MODELS:
        if not os.path.exists(path):
            print("skip", tag)
            continue
        model = YOLO(path)
        names = model.names
        img0 = cv2.imread(best_frame(views[0]["name"]))
        model.predict(img0, conf=0.25, verbose=False)

        times = []
        for _ in range(50):
            t0 = time.perf_counter()
            model.predict(img0, conf=0.25, verbose=False)
            times.append(time.perf_counter() - t0)

        # сбор детекций
        det_by_view = {}
        for v in views:
            im = cv2.imread(best_frame(v["name"]))
            r = model.predict(im, conf=0.001, verbose=False)[0]
            dets = [(float(c), names[int(k)], [float(x) for x in b])
                    for c, k, b in zip(r.boxes.conf, r.boxes.cls, r.boxes.xyxy)]
            det_by_view[v["name"]] = dets

        per_class_50, per_class_coco, pr_curves = {}, {}, {}
        tp = fp = fn = 0
        thresholds = np.arange(0.5, 1.0, 0.05)
        for cls in n_gt_class:
            aps = []
            for thr in thresholds:
                recs = []
                for v in views:
                    gts = [x for x in gt_by_view[v["name"]] if x["class"] == cls]
                    dets = [d for d in det_by_view[v["name"]] if d[1] == cls]
                    recs += match_view(dets, gts, float(thr)).get(cls, [])
                aps.append(ap_from_records(recs, n_gt_class[cls]))
                if abs(float(thr) - 0.5) < 1e-9:
                    recs50 = recs
            per_class_50[cls] = aps[0]
            per_class_coco[cls] = float(np.mean(aps))
            pr_curves[cls] = pr_points(recs50, n_gt_class[cls])

            # P/R при conf 0.5
            for v in views:
                gts = gt_by_view[v["name"]]
                g = [x for x in gts if x["class"] == cls]
                d50 = [d for d in det_by_view[v["name"]]
                       if d[1] == cls and d[0] >= 0.5]
                rows = match_view(d50, gts, 0.5).get(cls, [])
                tp += sum(1 for c, ok in rows if ok)
                fp += sum(1 for c, ok in rows if not ok)
                fn += len(g) - sum(1 for c, ok in rows if ok)

        mAP50 = float(np.mean([v for v in per_class_50.values() if v is not None]))
        mAP = float(np.mean([v for v in per_class_coco.values() if v is not None]))
        prec = tp / max(tp + fp, 1)
        rec = tp / max(tp + fn, 1)
        f1 = 2 * prec * rec / max(prec + rec, 1e-9)

        # аннотированные кадры
        outdir = os.path.join(FRAMES, "annotated", tag)
        os.makedirs(outdir, exist_ok=True)
        for v in views:
            im = cv2.imread(best_frame(v["name"]))
            dets = [d for d in det_by_view[v["name"]] if d[0] >= 0.05]
            out = draw(im, dets, gt_by_view[v["name"]], names)
            cv2.imwrite(os.path.join(outdir, v["name"] + ".png"), out)

        fig, axes = plt.subplots(3, 3, figsize=(10, 9))
        for ax, cls in zip(axes.flat, n_gt_class):
            pr = pr_curves.get(cls, {"recall": [], "precision": []})
            ax.plot(pr["recall"], pr["precision"], color="C0")
            ax.set_title(f"{cls}: AP50={per_class_50[cls]:.2f}")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1.05)
            ax.grid(alpha=0.3)
        for ax in list(axes.flat)[len(n_gt_class):]:
            ax.axis("off")
        plt.tight_layout()
        plt.savefig(os.path.join(FRAMES, f"pr_{tag}.png"), dpi=110)
        plt.close(fig)

        res = {
            "model": tag,
            "T_median_ms": statistics.median(times) * 1000,
            "f_hz": 1.0 / statistics.median(times),
            "mAP50": mAP50,
            "mAP50_95": mAP,
            "precision_050": prec,
            "recall_050": rec,
            "f1_050": f1,
            "tp": tp, "fp": fp, "fn": fn,
            "params_m": sum(p.numel() for p in model.model.parameters()) / 1e6,
            "size_mb": os.path.getsize(path) / 1e6,
            "ap50_per_class": per_class_50,
            "ap50_95_per_class": per_class_coco,
            "pr_curves": pr_curves,
        }
        results.append(res)
        print(json.dumps(res, ensure_ascii=False))

    with open(os.path.join(BASE, "benchmark_results.json"), "w", encoding="utf-8") as f:
        json.dump({"gt_instances": n_gt_class, "results": results}, f,
                  ensure_ascii=False, indent=2)
    with open(os.path.join(BASE, "benchmark_results.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["model", "T_ms", "f_Hz", "mAP50", "mAP50_95", "P@0.5", "R@0.5", "F1@0.5",
                    "params_M", "size_MB"])
        for r in results:
            w.writerow([r["model"], f"{r['T_median_ms']:.2f}", f"{r['f_hz']:.1f}",
                        f"{r['mAP50']:.4f}", f"{r['mAP50_95']:.4f}",
                        f"{r['precision_050']:.4f}", f"{r['recall_050']:.4f}",
                        f"{r['f1_050']:.4f}", f"{r['params_m']:.3f}", f"{r['size_mb']:.2f}"])


if __name__ == "__main__":
    main()
