"""Агрегация бенчмарка по сценам + bootstrap-интервалы."""
import json
import os

import numpy as np
import pandas as pd

BASE = "data/gazebo/exp"
SCENES = [
    ("showroom", os.path.join(BASE, "benchmark_results.json")),
    ("warm_light", os.path.join(BASE, "results_v1", "benchmark_results.json")),
    ("cool_light", os.path.join(BASE, "results_v2", "benchmark_results.json")),
    ("orbit_video", os.path.join(BASE, "results_video", "benchmark_results.json")),
]


def main():
    rows = []
    for scene, path in SCENES:
        if not os.path.exists(path):
            print("skip", scene, path)
            continue
        data = json.load(open(path, encoding="utf-8"))
        for r in data.get("results", []):
            rows.append({
                "scene": scene,
                "model": r["model"],
                "mAP50": r["mAP50"],
                "mAP50_95": r["mAP50_95"],
                "T_ms": r["T_median_ms"],
                "params_m": r["params_m"],
                "size_mb": r["size_mb"],
            })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(BASE, "scene_results.csv"), index=False)

    agg = (df.groupby("model")
           .agg(scenes=("scene", "nunique"),
                mAP50_mean=("mAP50", "mean"),
                mAP50_std=("mAP50", "std"),
                mAP50_min=("mAP50", "min"),
                mAP50_max=("mAP50", "max"),
                mAP50_95_mean=("mAP50_95", "mean"),
                T_mean=("T_ms", "mean"))
           .reset_index()
           .sort_values("mAP50_mean", ascending=False))

    rng = np.random.default_rng(0)
    lo, hi = [], []
    for model in agg["model"]:
        vals = df.loc[df["model"] == model, "mAP50"].to_numpy()
        boot = np.array([rng.choice(vals, size=len(vals), replace=True).mean()
                         for _ in range(4000)])
        lo.append(float(np.percentile(boot, 2.5)))
        hi.append(float(np.percentile(boot, 97.5)))
    agg["mAP50_ci95_lo"] = lo
    agg["mAP50_ci95_hi"] = hi
    agg.to_csv(os.path.join(BASE, "scene_aggregate.csv"), index=False)

    print(df.pivot(index="model", columns="scene", values="mAP50").round(3).to_string())
    print()
    print(agg.round(3).to_string(index=False))

    out = {
        "scenes": [s for s, _ in SCENES],
        "per_scene": df.to_dict(orient="records"),
        "aggregate": agg.to_dict(orient="records"),
    }
    with open(os.path.join(BASE, "scene_aggregate.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
