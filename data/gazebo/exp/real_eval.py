"""Проверка моделей на реальных изображениях COCO128."""
import csv
import json
import os

from ultralytics import YOLO

BASE = "data/gazebo/exp"
MODELS = [
    ("yolov8n", "src/quadropted_perception/models/yolov8n.pt"),
    ("yolov8s", "src/quadropted_perception/models/yolov8s.pt"),
    ("yolov10n", "src/quadropted_perception/models/yolov10n.pt"),
    ("yolov9t", "src/quadropted_perception/models/yolov9t.pt"),
    ("yolo11n", "/tmp/opencode/yolo11n.pt"),
]


def main():
    rows = []
    for tag, path in MODELS:
        if not os.path.exists(path):
            continue
        model = YOLO(path)
        r = model.val(data="coco128.yaml", split="train", imgsz=640,
                      verbose=False, plots=False)
        speed = r.speed or {}
        rows.append({
            "model": tag,
            "images": 128,
            "instances": 929,
            "mAP50": float(r.box.map50),
            "mAP50_95": float(r.box.map),
            "precision": float(r.box.mp),
            "recall": float(r.box.mr),
            "inference_ms": float(speed.get("inference", 0.0)),
            "preprocess_ms": float(speed.get("preprocess", 0.0)),
            "postprocess_ms": float(speed.get("postprocess", 0.0)),
        })
        print(tag, rows[-1])

    with open(os.path.join(BASE, "real_coco128.json"), "w", encoding="utf-8") as f:
        json.dump({"dataset": "coco128", "rows": rows}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(BASE, "real_coco128.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
