"""Пиковый RSS процесса инференса для каждой модели (отдельный процесс)."""
import json
import os
import subprocess
import sys

PY = ".venv-lyrical/bin/python"
MODELS = [
    ("yolov8n", "src/quadropted_perception/models/yolov8n.pt"),
    ("yolov8s", "src/quadropted_perception/models/yolov8s.pt"),
    ("yolov10n", "src/quadropted_perception/models/yolov10n.pt"),
    ("yolov9t", "src/quadropted_perception/models/yolov9t.pt"),
    ("yolo11n", "/tmp/opencode/yolo11n.pt"),
]

BASE_CODE = r"""
import cv2, resource, torch, ultralytics
img = cv2.imread("data/gazebo/exp/frames/station_00/frame.png")
print("PEAK", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)
"""

MODEL_CODE = r"""
import sys, cv2, resource
from ultralytics import YOLO
img = cv2.imread("data/gazebo/exp/frames/station_00/frame.png")
m = YOLO(sys.argv[1])
m.predict(img, verbose=False)
for _ in range(30):
    m.predict(img, verbose=False)
print("PEAK", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)
"""


def peak(code, *args):
    r = subprocess.run([PY, "-c", code, *args], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("PEAK"):
            return float(line.split()[1])
    print(r.stderr[-500:])
    return None


def main():
    base = peak(BASE_CODE)
    print("baseline (torch+ultralytics):", base, "MB")
    out = {"baseline_mb": base, "models": {}}
    for tag, path in MODELS:
        if not os.path.exists(path):
            continue
        p = peak(MODEL_CODE, path)
        out["models"][tag] = {
            "peak_mb": p,
            "delta_mb": (p - base) if (p and base) else None,
        }
        print(f"{tag}: peak={p:.1f} MB delta={p - base:.1f} MB")
    with open("data/gazebo/exp/rss.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
