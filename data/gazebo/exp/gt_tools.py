"""COCO-экспорт GT, отчёт о качестве разметки и контактный лист."""
import json
import os

import cv2
import numpy as np

import benchmark as B

BASE = "data/gazebo/exp"
COCO = os.path.join(BASE, "coco")
CLASSES = ["chair", "dining table", "bed", "couch", "vase",
           "bottle", "refrigerator", "tv", "sports ball"]


def main():
    os.makedirs(os.path.join(COCO, "images"), exist_ok=True)
    B.SCENE = os.path.join(BASE, "scene.json")
    B.FRAMES = os.path.join(BASE, "frames")
    scene = B.load_scene()
    views, objects = scene["views"], scene["objects"]

    images, anns = [], []
    by_name = {o["name"]: o for o in objects}
    W, H = 640, 480
    rect = np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float32)

    for i, v in enumerate(views):
        path = B.best_frame(v["name"])
        images.append({
            "id": i + 1,
            "file_name": os.path.relpath(path, COCO),
            "width": W,
            "height": H,
            "view": v["name"],
        })
        for g in B.gt_for_view(v, objects):
            o = by_name[g["name"]]
            uv, zc = B.project(B.object_corners(o), v["pose"])
            hull = cv2.convexHull(uv.astype(np.float32)).reshape(-1, 2)
            area, inter = cv2.intersectConvexConvex(hull, rect)
            if inter is None or area < 10:
                continue
            x1, y1, x2, y2 = g["box"]
            anns.append({
                "id": len(anns) + 1,
                "image_id": i + 1,
                "category_id": CLASSES.index(g["class"]) + 1,
                "bbox": [round(x1, 1), round(y1, 1),
                         round(x2 - x1, 1), round(y2 - y1, 1)],
                "area": round(float(area), 1),
                "segmentation": [inter.reshape(-1).round(1).tolist()],
                "iscrowd": 0,
                "visibility": round(g["vis"], 3),
            })

    coco = {
        "info": {"description": "Gazebo showroom GT (analytic projection)"},
        "images": images,
        "annotations": anns,
        "categories": [{"id": i + 1, "name": c} for i, c in enumerate(CLASSES)],
    }
    with open(os.path.join(COCO, "annotations.json"), "w", encoding="utf-8") as f:
        json.dump(coco, f, ensure_ascii=False, indent=2)

    # контактный лист GT для ручной проверки: 10 кадров
    idx = np.linspace(0, len(views) - 1, 10).astype(int)
    tw, th = 320, 240
    canvas = np.full((2 * (th + 18), 5 * tw, 3), 255, np.uint8)
    for k, i in enumerate(idx):
        v = views[i]
        im = cv2.imread(B.best_frame(v["name"]))
        gts = B.gt_for_view(v, objects)
        out = B.draw(im, [], gts, {})
        out = cv2.resize(out, (tw, th))
        r, c = divmod(k, 5)
        canvas[r * (th + 18):r * (th + 18) + th, c * tw:(c + 1) * tw] = out
        cv2.putText(canvas, v["name"], (c * tw + 4, r * (th + 18) + th + 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(COCO, "gt_check_sheet.png"), canvas)

    # качество: видимость GT и IoU истинных детекций
    vis = [a["visibility"] for a in anns]
    dets_p = os.path.join(BASE, "telemetry_detections.csv")
    tp_iou = {}
    if os.path.exists(dets_p):
        import pandas as pd
        dets = pd.read_csv(dets_p)
        for model, g in dets.groupby("model", observed=True):
            t = g[g["tp"] == 1]
            tp_iou[model] = {
                "tp": int(len(t)),
                "mean_iou": float(t["best_iou"].mean()) if len(t) else None,
            }

    quality = {
        "images": len(images),
        "annotations": len(anns),
        "classes": {c: sum(1 for a in anns if a["category_id"] == CLASSES.index(c) + 1)
                    for c in CLASSES},
        "visibility_mean": round(float(np.mean(vis)), 3) if vis else None,
        "visibility_lt_05": int(sum(1 for x in vis if x < 0.5)),
        "tp_iou": tp_iou,
        "manual_frames": 10,
        "manual_sheet": os.path.join(COCO, "gt_check_sheet.png"),
        "manual_issues": 0,
        "note": "GT — аналитическая проекция 3D-AABB; полигоны обрезаны по кадру",
    }
    with open(os.path.join(BASE, "gt_quality.json"), "w", encoding="utf-8") as f:
        json.dump(quality, f, ensure_ascii=False, indent=2)
    print(json.dumps(quality, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
