"""Runtime-профиль: потоки torch, CPU-affinity, ONNX и OpenVINO."""
import json
import os
import statistics
import time

import cv2
import torch
from ultralytics import YOLO

BASE = "data/gazebo/exp"
MODEL = "/tmp/opencode/yolo11n.pt"
IMG = os.path.join(BASE, "frames", "station_00", "frame.png")
OUT = os.path.join(BASE, "runtime.json")


def bench(model, runs=40):
    img = cv2.imread(IMG)
    model.predict(img, verbose=False)
    ts = []
    for _ in range(runs):
        t = time.perf_counter()
        model.predict(img, verbose=False)
        ts.append(time.perf_counter() - t)
    med = statistics.median(ts)
    return {"T_p50_ms": round(med * 1000, 3), "fps": round(1.0 / med, 2)}


def dir_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path) / 1e6
    return sum(os.path.getsize(os.path.join(path, f)) for f in os.listdir(path)) / 1e6


def main():
    model = YOLO(MODEL)
    out = {"model": os.path.basename(MODEL), "image": IMG}

    threads = {}
    for n in (1, 2, 4, 8):
        torch.set_num_threads(n)
        threads[str(n)] = bench(model)
    torch.set_num_threads(8)
    out["threads"] = threads

    orig = os.sched_getaffinity(0)
    try:
        cpus = sorted(orig)[:4]
        os.sched_setaffinity(0, set(cpus))
        out["affinity_4cpu"] = {"cpus": cpus, **bench(model)}
    except Exception as e:
        out["affinity_4cpu"] = {"error": str(e)[:200]}
    finally:
        os.sched_setaffinity(0, orig)

    for name, fmt, kw in [
        ("onnx_fp32", "onnx", {"dynamic": False}),
        ("openvino_fp32", "openvino", {"half": False}),
        ("openvino_fp16", "openvino", {"half": True}),
    ]:
        try:
            path = model.export(format=fmt, imgsz=640, **kw)
            m = YOLO(path)
            out[name] = {**bench(m), "size_mb": round(dir_size(path), 2)}
        except Exception as e:
            out[name] = {"error": str(e)[:300]}

    out["int8"] = "not run: требует NNCF-калибровку"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
