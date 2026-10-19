"""Построчная телеметрия бенчмарка: кадры, детекции и сводка.

Пишет:
  telemetry_frames.csv      — строка на кадр/модель
  telemetry_detections.csv  — строка на детекцию
  telemetry_summary.json    — перцентили, TP/FP/FN, per-class
"""
import argparse
import csv
import json
import os
import time
from datetime import datetime

import cv2
import numpy as np
import psutil
from ultralytics import YOLO

import benchmark as B

BASE = "data/gazebo/exp"
FRAMES = os.path.join(BASE, "frames")
OUT_FRAMES = os.path.join(BASE, "telemetry_frames.csv")
OUT_DETS = os.path.join(BASE, "telemetry_detections.csv")
OUT_SUMMARY = os.path.join(BASE, "telemetry_summary.json")

ENERGY_PATH = "/sys/class/powercap/intel-rapl:0/energy_uj"
CONF_THR = 0.05


def read_energy():
    try:
        with open(ENERGY_PATH, "r", encoding="ascii") as f:
            return int(f.read().strip())
    except Exception:
        return None


def match_detections(dets, gts, thr=0.5):
    """dets: [(conf, cls, box)], gts: [dict]. Возвращает (rows, fn)."""
    order = sorted(range(len(dets)), key=lambda i: -dets[i][0])
    used = [False] * len(gts)
    rows = []
    for idx in order:
        conf, cls, box = dets[idx]
        best_j, best_iou = -1, 0.0
        for j, g in enumerate(gts):
            if used[j] or g["class"] != cls:
                continue
            v = B.iou(box, g["box"])
            if v > best_iou:
                best_j, best_iou = j, v
        tp = best_iou >= thr
        if tp:
            used[best_j] = True

        any_iou, any_cls = 0.0, ""
        for g in gts:
            v = B.iou(box, g["box"])
            if v > any_iou:
                any_iou, any_cls = v, g["class"]

        rows.append({
            "class_pred": cls,
            "conf": conf,
            "box": box,
            "best_iou": best_iou if tp else any_iou,
            "class_gt": any_cls if any_iou >= thr else "",
            "tp": tp,
        })
    fn = len(gts) - sum(1 for r in rows if r["tp"])
    return rows, fn


def main():
    global BASE, FRAMES, OUT_FRAMES, OUT_DETS, OUT_SUMMARY
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default=os.path.join(BASE, "scene.json"))
    ap.add_argument("--frames", default=FRAMES)
    ap.add_argument("--out", default=BASE)
    ap.add_argument("--label", default="showroom")
    args = ap.parse_args()

    BASE, FRAMES = args.out, args.frames
    OUT_FRAMES = os.path.join(BASE, "telemetry_frames.csv")
    OUT_DETS = os.path.join(BASE, "telemetry_detections.csv")
    OUT_SUMMARY = os.path.join(BASE, "telemetry_summary.json")
    os.makedirs(BASE, exist_ok=True)
    B.SCENE, B.FRAMES = args.scene, args.frames

    scene = B.load_scene()
    views, objects = scene["views"], scene["objects"]
    gt_by_view = {v["name"]: B.gt_for_view(v, objects) for v in views}

    frame_rows, det_rows = [], []
    summary = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "scene": args.label, "models": {}}

    proc = psutil.Process()
    proc.cpu_percent(None)
    energy_available = read_energy() is not None

    for tag, path in B.MODELS:
        if not os.path.exists(path):
            print("skip", tag)
            continue
        model = YOLO(path)
        img0 = cv2.imread(B.best_frame(views[0]["name"]))
        model.predict(img0, conf=0.001, verbose=False)  # прогрев
        proc.cpu_percent(None)

        rows_model = []
        dets_model = []
        for v in views:
            im = cv2.imread(B.best_frame(v["name"]))
            gts = gt_by_view[v["name"]]

            e0 = read_energy()
            t0 = time.perf_counter()
            r = model.predict(im, conf=CONF_THR, verbose=False)[0]
            t_total = (time.perf_counter() - t0) * 1000.0
            e1 = read_energy()

            speed = r.speed or {}
            dets = [(float(c), model.names[int(k)], [float(x) for x in b])
                    for c, k, b in zip(r.boxes.conf, r.boxes.cls, r.boxes.xyxy)]
            match, fn = match_detections(dets, gts, 0.5)
            tp = sum(1 for m in match if m["tp"])
            fp = len(match) - tp

            energy_mj = None
            power_w = None
            if e0 is not None and e1 is not None and e1 >= e0:
                energy_mj = (e1 - e0) / 1000.0
                if t_total > 0:
                    power_w = (energy_mj / 1000.0) / (t_total / 1000.0)

            stamp = datetime.now().isoformat(timespec="milliseconds")
            row = {
                "timestamp": stamp,
                "scene": args.label,
                "view": v["name"],
                "model": tag,
                "conf_thr": CONF_THR,
                "T_pre_ms": round(float(speed.get("preprocess", 0.0)), 4),
                "T_infer_ms": round(float(speed.get("inference", 0.0)), 4),
                "T_post_ms": round(float(speed.get("postprocess", 0.0)), 4),
                "T_total_ms": round(t_total, 4),
                "rss_mb": round(proc.memory_info().rss / 1e6, 1),
                "cpu_pct": round(proc.cpu_percent(None), 1),
                "gpu_pct": "",
                "power_w": round(power_w, 2) if power_w is not None else "",
                "energy_mj": round(energy_mj, 3) if energy_mj is not None else "",
                "n_det": len(match),
                "n_gt": len(gts),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "dropped": 0,
            }
            rows_model.append(row)

            for m in match:
                box = m["box"]
                dets_model.append({
                    "timestamp": stamp,
                    "scene": args.label,
                    "view": v["name"],
                    "model": tag,
                    "conf_thr": CONF_THR,
                    "class_pred": m["class_pred"],
                    "conf": round(m["conf"], 5),
                    "x1": round(box[0], 1), "y1": round(box[1], 1),
                    "x2": round(box[2], 1), "y2": round(box[3], 1),
                    "best_iou": round(m["best_iou"], 4),
                    "class_gt": m["class_gt"],
                    "tp": int(m["tp"]),
                })

        totals = {"tp": 0, "fp": 0, "fn": 0, "n_gt": 0}
        per_class = {}
        for r in rows_model:
            totals["tp"] += r["tp"]
            totals["fp"] += r["fp"]
            totals["fn"] += r["fn"]
            totals["n_gt"] += r["n_gt"]

        for d in dets_model:
            cls = d["class_pred"]
            pc = per_class.setdefault(cls, {"tp": 0, "fp": 0, "fn": 0})
            if d["tp"]:
                pc["tp"] += 1
            else:
                pc["fp"] += 1
        gt_counts = {}
        for v in views:
            for g in gt_by_view[v["name"]]:
                gt_counts[g["class"]] = gt_counts.get(g["class"], 0) + 1
        for cls, n in gt_counts.items():
            pc = per_class.setdefault(cls, {"tp": 0, "fp": 0, "fn": 0})
            pc["fn"] = n - pc["tp"]

        t = [r["T_total_ms"] for r in rows_model]
        e = [r["energy_mj"] for r in rows_model if r["energy_mj"] != ""]
        cpu = [r["cpu_pct"] for r in rows_model]
        rss = [r["rss_mb"] for r in rows_model]
        p = totals["tp"] / max(totals["tp"] + totals["fp"], 1)
        rec = totals["tp"] / max(totals["tp"] + totals["fn"], 1)
        f1 = 2 * p * rec / max(p + rec, 1e-9)

        summary["models"][tag] = {
            "T_p50_ms": round(float(np.percentile(t, 50)), 3),
            "T_p95_ms": round(float(np.percentile(t, 95)), 3),
            "T_p99_ms": round(float(np.percentile(t, 99)), 3),
            "T_mean_ms": round(float(np.mean(t)), 3),
            "T_std_ms": round(float(np.std(t)), 3),
            "fps": round(1000.0 / float(np.percentile(t, 50)), 2),
            "rss_mb": round(float(np.mean(rss)), 1),
            "cpu_pct": round(float(np.mean(cpu)), 1),
            "energy_available": energy_available,
            "energy_per_frame_mj": round(float(np.mean(e)), 3) if e else None,
            "power_w": round(float(np.mean([r["power_w"] for r in rows_model
                                            if r["power_w"] != ""])), 2)
            if energy_available else None,
            "conf_thr": CONF_THR,
            "n_frames": len(rows_model),
            "n_gt": totals["n_gt"],
            "tp": totals["tp"], "fp": totals["fp"], "fn": totals["fn"],
            "precision": round(p, 4), "recall": round(rec, 4), "f1": round(f1, 4),
            "per_class": {k: v for k, v in sorted(per_class.items())},
        }
        frame_rows.extend(rows_model)
        det_rows.extend(dets_model)
        print(tag, summary["models"][tag]["T_p50_ms"], "ms",
              "mAP-инфо:", totals)

    with open(OUT_FRAMES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(frame_rows[0].keys()))
        w.writeheader()
        w.writerows(frame_rows)
    with open(OUT_DETS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(det_rows[0].keys()))
        w.writeheader()
        w.writerows(det_rows)
    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("frames:", len(frame_rows), "detections:", len(det_rows))
    print("energy available:", energy_available)


if __name__ == "__main__":
    main()
