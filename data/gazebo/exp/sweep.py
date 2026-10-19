"""Подбор порога уверенности по F1 (class-aware, IoU 0.5)."""
import json
import os

import cv2
import numpy as np
from ultralytics import YOLO

import benchmark as B

BASE = "data/gazebo/exp"
FRAMES = os.path.join(BASE, "frames")
MODELS = B.MODELS


def main():
    scene = json.load(open(os.path.join(BASE, "scene.json"), encoding="utf-8"))
    views, objects = scene["views"], scene["objects"]
    gt = {v["name"]: B.gt_for_view(v, objects) for v in views}

    for tag, path in MODELS:
        if not os.path.exists(path):
            continue
        model = YOLO(path)
        names = model.names
        dets = {}
        for v in views:
            im = cv2.imread(B.best_frame(v["name"]))
            r = model.predict(im, conf=0.001, verbose=False)[0]
            dets[v["name"]] = [(float(c), names[int(k)], [float(x) for x in b])
                               for c, k, b in zip(r.boxes.conf, r.boxes.cls, r.boxes.xyxy)]

        rows = []
        for conf in np.arange(0.01, 0.96, 0.01):
            tp = fp = fn = 0
            for v in views:
                gts = gt[v["name"]]
                d = [x for x in dets[v["name"]] if x[0] >= conf]
                a, b, c = B.match_all(d, gts, 0.5)
                tp += a
                fp += b
                fn += c
            p = tp / max(tp + fp, 1)
            r = tp / max(tp + fn, 1)
            f1 = 2 * p * r / max(p + r, 1e-9)
            rows.append({"conf": float(conf), "tp": tp, "fp": fp, "fn": fn,
                         "precision": p, "recall": r, "f1": f1})
        best = max(rows, key=lambda x: x["f1"])
        print(f"{tag}: best conf={best['conf']:.2f} F1={best['f1']:.3f} "
              f"P={best['precision']:.3f} R={best['recall']:.3f} "
              f"TP={best['tp']} FP={best['fp']} FN={best['fn']}")
        with open(os.path.join(BASE, f"sweep_{tag}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
