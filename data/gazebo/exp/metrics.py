"""Метрики надёжности: ECE, bootstrap-CI для F1, latency-перцентили."""
import json
import os

import numpy as np
import pandas as pd

BASE = "data/gazebo/exp"


def ece(conf, correct, bins=10):
    conf = np.asarray(conf, dtype=float)
    correct = np.asarray(correct, dtype=float)
    edges = np.linspace(0, 1, bins + 1)
    total = len(conf)
    if total == 0:
        return None
    val = 0.0
    for i in range(bins):
        m = (conf >= edges[i]) & (conf < edges[i + 1] if i < bins - 1 else conf <= edges[i + 1])
        if not m.any():
            continue
        val += (m.sum() / total) * abs(correct[m].mean() - conf[m].mean())
    return float(val)


def bootstrap_f1(frames, model, n=4000, seed=0):
    g = frames[frames["model"] == model]
    tp = g["tp"].to_numpy()
    fp = g["fp"].to_numpy()
    fn = g["fn"].to_numpy()
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(tp), len(tp))
        t, f, nf = tp[idx].sum(), fp[idx].sum(), fn[idx].sum()
        p = t / max(t + f, 1)
        r = t / max(t + nf, 1)
        vals.append(2 * p * r / max(p + r, 1e-9))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main():
    frames = pd.read_csv(os.path.join(BASE, "telemetry_frames.csv"))
    dets = pd.read_csv(os.path.join(BASE, "telemetry_detections.csv"))
    summary = json.load(open(os.path.join(BASE, "telemetry_summary.json"), encoding="utf-8"))

    rows = []
    for model in frames["model"].unique():
        g = frames[frames["model"] == model]
        d = dets[dets["model"] == model]
        lo, hi = bootstrap_f1(frames, model)
        rows.append({
            "model": model,
            "T_p50_ms": float(np.percentile(g["T_total_ms"], 50)),
            "T_p95_ms": float(np.percentile(g["T_total_ms"], 95)),
            "T_p99_ms": float(np.percentile(g["T_total_ms"], 99)),
            "F1_conf005": float(2 * (g["tp"].sum() / max(g["tp"].sum() + g["fp"].sum(), 1)) *
                                (g["tp"].sum() / max(g["tp"].sum() + g["fn"].sum(), 1)) /
                                max((g["tp"].sum() / max(g["tp"].sum() + g["fp"].sum(), 1)) +
                                    (g["tp"].sum() / max(g["tp"].sum() + g["fn"].sum(), 1)), 1e-9)),
            "F1_ci95_lo": lo,
            "F1_ci95_hi": hi,
            "ECE": ece(d["conf"], d["tp"]),
            "energy_per_frame_mj": summary["models"].get(model, {}).get("energy_per_frame_mj"),
        })

    df = pd.DataFrame(rows).sort_values("F1_conf005", ascending=False)
    df.to_csv(os.path.join(BASE, "metrics.csv"), index=False)
    print(df.round(4).to_string(index=False))
    with open(os.path.join(BASE, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump({"rows": df.round(5).to_dict(orient="records"),
                   "energy_available": bool(summary["models"][df.iloc[0]["model"]]
                                            .get("energy_available", False))},
                  f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
