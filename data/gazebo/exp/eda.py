#!/usr/bin/env python3
"""EDA по всем артефактам Gazebo-бенчмарка.

Читает:
  telemetry_frames.csv, telemetry_detections.csv, telemetry_summary.json,
  benchmark_results.json, rss.json, ros_telemetry.json,
  confusion_*.json, sweep_*.json, scene.json

Пишет:
  eda/REPORT.md, eda/summary.json,
  eda/tables/*.csv, eda/plots/*.png

Зависимости:
  pandas, numpy, matplotlib, seaborn, tabulate

Запуск:
  .venv-lyrical/bin/python data/gazebo/exp/eda.py
  .venv-lyrical/bin/python data/gazebo/exp/eda.py --dir data/gazebo/exp --out /tmp/eda
"""
import argparse
import glob
import json
import os
import sqlite3
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["figure.dpi"] = 110


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def md(df):
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"


def q(series, p):
    return float(np.percentile(series, p)) if len(series) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/gazebo/exp")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    base = args.dir
    out = args.out or os.path.join(base, "eda")
    plots = os.path.join(out, "plots")
    tables = os.path.join(out, "tables")
    os.makedirs(plots, exist_ok=True)
    os.makedirs(tables, exist_ok=True)

    frames_p = os.path.join(base, "telemetry_frames.csv")
    dets_p = os.path.join(base, "telemetry_detections.csv")
    if not os.path.exists(frames_p):
        raise SystemExit(
            f"Нет {frames_p}. Сначала запусти telemetry.py:\n"
            "  .venv-lyrical/bin/python data/gazebo/exp/telemetry.py"
        )

    frames = pd.read_csv(frames_p)
    dets = pd.read_csv(dets_p) if os.path.exists(dets_p) else pd.DataFrame()
    summary = load_json(os.path.join(base, "telemetry_summary.json"), {})
    bench = load_json(os.path.join(base, "benchmark_results.json"), {})
    rss = load_json(os.path.join(base, "rss.json"), {})
    ros = load_json(os.path.join(base, "ros_telemetry.json"), {})
    scene = load_json(os.path.join(base, "scene.json"), {})

    for df in (frames, dets):
        if not df.empty and "model" in df.columns:
            order = [m for m in summary.get("models", {}) if m in set(df["model"])]
            if order:
                df["model"] = pd.Categorical(df["model"], categories=order, ordered=True)

    report = []
    report.append("# EDA: Gazebo-бенчмарк YOLO\n")
    report.append(f"Сгенерировано: {datetime.now().isoformat(timespec='seconds')}\n")
    report.append(f"Каталог данных: `{base}`\n")

    # ---------- 1. Обзор ----------
    report.append("## 1. Обзор данных\n")
    overview = {
        "frames": int(len(frames)),
        "models": int(frames["model"].nunique()),
        "views": int(frames["view"].nunique()),
        "gt_instances_per_model": int(frames.groupby("model", observed=True)["n_gt"].sum().max()),
        "detections": int(len(dets)),
        "scene_objects": len(scene.get("objects", [])),
        "scene_views": len(scene.get("views", [])),
    }
    if summary.get("models"):
        overview["energy_available"] = bool(
            next(iter(summary["models"].values())).get("energy_available", False)
        )
    report.append(md(pd.DataFrame([overview])))
    report.append("")

    miss = frames.isna().sum().to_frame("NaN").T
    report.append("### Пропуски в telemetry_frames.csv\n")
    report.append(md(miss.reset_index(drop=True).T.reset_index().rename(columns={"index": "column", 0: "NaN"})))
    report.append("")

    # ---------- 2. Задержка ----------
    report.append("## 2. Задержка и ресурсы\n")
    agg = frames.groupby("model", observed=True).agg(
        frames=("view", "count"),
        T_p50=("T_total_ms", lambda s: q(s, 50)),
        T_p95=("T_total_ms", lambda s: q(s, 95)),
        T_p99=("T_total_ms", lambda s: q(s, 99)),
        T_mean=("T_total_ms", "mean"),
        T_std=("T_total_ms", "std"),
        pre=("T_pre_ms", "mean"),
        infer=("T_infer_ms", "mean"),
        post=("T_post_ms", "mean"),
        rss=("rss_mb", "mean"),
        cpu=("cpu_pct", "mean"),
    ).reset_index()
    agg["fps"] = 1000.0 / agg["T_p50"]
    agg.to_csv(os.path.join(tables, "latency_resources.csv"), index=False)
    report.append(md(agg.round(3)))
    report.append("")

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=frames, x="model", y="T_total_ms", ax=ax)
    ax.set_title("T_total по моделям (48 кадров)")
    ax.set_xlabel("")
    ax.set_ylabel("T_total, мс")
    fig.tight_layout()
    fig.savefig(os.path.join(plots, "latency_box.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    m = agg.melt(id_vars="model", value_vars=["T_p50", "T_p95", "T_p99"],
                 var_name="percentile", value_name="ms")
    sns.barplot(data=m, x="model", y="ms", hue="percentile", ax=ax)
    ax.set_title("Перцентили задержки")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(os.path.join(plots, "latency_percentiles.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    parts = agg.melt(id_vars="model", value_vars=["pre", "infer", "post"],
                     var_name="stage", value_name="ms")
    sns.barplot(data=parts, x="model", y="ms", hue="stage", ax=ax)
    ax.set_title("Среднее время по стадиям")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(os.path.join(plots, "latency_parts.png"))
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.scatterplot(data=frames, x="cpu_pct", y="T_total_ms", hue="model", alpha=0.6, ax=ax)
    ax.set_title("T_total vs загрузка CPU")
    fig.tight_layout()
    fig.savefig(os.path.join(plots, "latency_vs_cpu.png"))
    plt.close(fig)

    pivot = frames.pivot_table(index="view", columns="model", values="T_total_ms",
                               aggfunc="median", observed=True)
    fig, ax = plt.subplots(figsize=(8, 16))
    sns.heatmap(pivot, cmap="viridis", ax=ax, cbar_kws={"label": "T_total, мс"})
    ax.set_title("Медиана T_total по ракурсам")
    fig.tight_layout()
    fig.savefig(os.path.join(plots, "latency_by_view.png"))
    plt.close(fig)

    corr = (frames.groupby("model", observed=True)
            .apply(lambda d: d[["T_total_ms", "T_pre_ms", "T_infer_ms", "T_post_ms",
                                "rss_mb", "cpu_pct", "n_det"]].corr()["T_total_ms"],
                   include_groups=False)
            .reset_index())
    corr.to_csv(os.path.join(tables, "correlations.csv"), index=False)
    report.append("### Корреляции с T_total\n")
    report.append(md(corr.round(3)))
    report.append("")

    # ---------- 3. Качество ----------
    if not dets.empty:
        report.append("## 3. Качество детекций\n")
        quality = []
        for model, g in dets.groupby("model", observed=True):
            tp = int(g["tp"].sum())
            fp = int(len(g) - tp)
            n_gt = int(frames.loc[frames["model"] == model, "n_gt"].sum())
            fn = n_gt - tp
            p = tp / max(tp + fp, 1)
            r = tp / max(tp + fn, 1)
            f1 = 2 * p * r / max(p + r, 1e-9)
            quality.append({"model": model, "n_gt": n_gt, "tp": tp, "fp": fp, "fn": fn,
                            "precision": p, "recall": r, "f1": f1,
                            "mean_conf_tp": float(g.loc[g["tp"] == 1, "conf"].mean())
                            if (g["tp"] == 1).any() else None,
                            "mean_iou_tp": float(g.loc[g["tp"] == 1, "best_iou"].mean())
                            if (g["tp"] == 1).any() else None})
        qual = pd.DataFrame(quality)
        qual.to_csv(os.path.join(tables, "quality.csv"), index=False)
        report.append(md(qual.round(3)))
        report.append("")

        fig, ax = plt.subplots(figsize=(10, 5))
        qm = qual.melt(id_vars="model", value_vars=["tp", "fp", "fn"],
                       var_name="type", value_name="count")
        sns.barplot(data=qm, x="model", y="count", hue="type", ax=ax)
        ax.set_title("TP / FP / FN при conf 0.05")
        ax.set_xlabel("")
        fig.tight_layout()
        fig.savefig(os.path.join(plots, "quality_tp_fp_fn.png"))
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.histplot(data=dets[dets["tp"] == 1], x="conf", hue="model",
                     bins=20, element="step", fill=False, ax=ax)
        ax.set_title("Уверенность истинных детекций")
        fig.tight_layout()
        fig.savefig(os.path.join(plots, "confidence_tp.png"))
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.histplot(data=dets, x="best_iou", hue="tp", bins=20,
                     element="step", fill=False, ax=ax)
        ax.set_title("IoU лучшего GT для детекций")
        fig.tight_layout()
        fig.savefig(os.path.join(plots, "iou_distribution.png"))
        plt.close(fig)

        pivot = dets.pivot_table(index="view", columns="model", values="tp",
                                 aggfunc="count", observed=True, fill_value=0)
        fig, ax = plt.subplots(figsize=(8, 16))
        sns.heatmap(pivot, cmap="magma", ax=ax, cbar_kws={"label": "детекций"})
        ax.set_title("Число детекций по ракурсам")
        fig.tight_layout()
        fig.savefig(os.path.join(plots, "detections_by_view.png"))
        plt.close(fig)

        # per-class таблица
        gt_counts = bench.get("gt_instances", {})
        per_class = []
        for r in bench.get("results", []):
            model = r["model"]
            for cls in sorted(gt_counts):
                g = dets[(dets["model"] == model) & (dets["class_pred"] == cls)]
                tp = int(g["tp"].sum())
                fp = int(len(g) - tp)
                per_class.append({
                    "model": model, "class": cls,
                    "gt": gt_counts.get(cls, 0),
                    "det": len(g), "tp": tp, "fp": fp,
                    "fn": gt_counts.get(cls, 0) - tp,
                    "ap50": r.get("ap50_per_class", {}).get(cls),
                    "ap50_95": r.get("ap50_95_per_class", {}).get(cls),
                })
        pc = pd.DataFrame(per_class)
        pc.to_csv(os.path.join(tables, "per_class.csv"), index=False)
        report.append("### AP и детекции по классам\n")
        report.append(md(pc.round(3)))
        report.append("")

        fig, ax = plt.subplots(figsize=(14, 6))
        sns.barplot(data=pc, x="class", y="ap50", hue="model", ax=ax)
        ax.set_title("AP@0.5 по классам")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        fig.savefig(os.path.join(plots, "ap50_by_class.png"))
        plt.close(fig)

        # выбросы
        top_t = frames.nlargest(20, "T_total_ms")[["model", "view", "T_total_ms",
                                                   "T_infer_ms", "n_det", "cpu_pct"]]
        top_t.to_csv(os.path.join(tables, "outliers_latency.csv"), index=False)
        top_err = (frames.assign(err=frames["fp"] + frames["fn"])
                   .nlargest(20, "err")[["model", "view", "n_gt", "tp", "fp", "fn"]])
        top_err.to_csv(os.path.join(tables, "outliers_errors.csv"), index=False)
        report.append("### Худшие кадры по ошибкам\n")
        report.append(md(top_err))
        report.append("")

    # ---------- 4. F1-свип ----------
    sweep_files = sorted(glob.glob(os.path.join(base, "sweep_*.json")))
    if sweep_files:
        report.append("## 4. F1 по порогам\n")
        fig, ax = plt.subplots(figsize=(10, 5))
        best_rows = []
        for f in sweep_files:
            model = os.path.basename(f).replace("sweep_", "").replace(".json", "")
            rows = load_json(f, [])
            if not rows:
                continue
            df = pd.DataFrame(rows)
            ax.plot(df["conf"], df["f1"], label=model)
            i = int(df["f1"].idxmax())
            best_rows.append({"model": model, "best_conf": df.loc[i, "conf"],
                              "best_f1": df.loc[i, "f1"], "p": df.loc[i, "precision"],
                              "r": df.loc[i, "recall"]})
        ax.set_title("F1 vs confidence")
        ax.set_xlabel("confidence")
        ax.set_ylabel("F1")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(plots, "f1_vs_conf.png"))
        plt.close(fig)
        best_f1_df = pd.DataFrame(best_rows).sort_values("best_f1", ascending=False)
        best_f1_df.to_csv(os.path.join(tables, "f1_best.csv"), index=False)
        report.append(md(best_f1_df.round(3)))
        report.append("")

    # ---------- 5. Confusion ----------
    conf_files = sorted(glob.glob(os.path.join(base, "confusion_*.json")))
    for f in conf_files:
        model = os.path.basename(f).replace("confusion_", "").replace(".json", "")
        data = load_json(f, {})
        confusion = data.get("confusion", {})
        if not confusion:
            continue
        classes = sorted({k.split(" -> ")[0] for k in confusion})
        preds = sorted({k.split(" -> ")[1] for k in confusion})
        mat = pd.DataFrame(0, index=classes, columns=preds)
        for k, v in confusion.items():
            gt, pred = k.split(" -> ")
            mat.loc[gt, pred] += v
        mat.to_csv(os.path.join(tables, f"confusion_{model}.csv"))
        fig, ax = plt.subplots(figsize=(10, 7))
        sns.heatmap(mat, annot=True, fmt="d", cmap="Blues", ax=ax)
        ax.set_title(f"Confusion: {model} (GT → prediction)")
        ax.set_xlabel("prediction")
        ax.set_ylabel("GT")
        fig.tight_layout()
        fig.savefig(os.path.join(plots, f"confusion_{model}.png"))
        plt.close(fig)

    # ---------- 6. RSS / ROS ----------
    if rss.get("models"):
        report.append("## 5. RSS и ROS\n")
        rows = []
        for model, v in rss["models"].items():
            rows.append({"model": model, "peak_mb": v["peak_mb"], "delta_mb": v["delta_mb"]})
        r = pd.DataFrame(rows)
        r.to_csv(os.path.join(tables, "rss.csv"), index=False)
        report.append("### Пиковый RSS\n")
        report.append(md(r.round(1)))
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=r, x="model", y="peak_mb", ax=ax)
        ax.set_title("Пиковый RSS процесса")
        ax.set_xlabel("")
        ax.set_ylabel("МБ")
        fig.tight_layout()
        fig.savefig(os.path.join(plots, "rss.png"))
        plt.close(fig)

    if ros:
        report.append("### ROS\n")
        report.append(md(pd.DataFrame([ros])))
        bag = ros.get("bag", "")
        if bag and not os.path.exists(bag):
            alt = os.path.join(base, "rosbag_det", os.path.basename(bag))
            bag = alt if os.path.exists(alt) else ""
        if bag and os.path.exists(bag):
            try:
                con = sqlite3.connect(bag)
                ts = [r[0] for r in con.execute("select timestamp from messages order by timestamp")]
                con.close()
                if len(ts) > 1:
                    gaps = np.diff(ts) / 1e6  # ns -> ms
                    fig, ax = plt.subplots(figsize=(9, 5))
                    sns.histplot(gaps, bins=30, ax=ax)
                    ax.set_title("Интервалы между /detections (bag)")
                    ax.set_xlabel("мс")
                    fig.tight_layout()
                    fig.savefig(os.path.join(plots, "ros_gaps.png"))
                    plt.close(fig)
                    report.append(f"Интервалы bag: p50={np.percentile(gaps,50):.1f} мс, "
                                  f"p95={np.percentile(gaps,95):.1f} мс, max={gaps.max():.1f} мс.")
                    report.append("")
            except Exception as e:
                report.append(f"Bag не прочитан: {e}\n")

    # ---------- 7. Итог ----------
    report.append("## 6. Итоговые наблюдения\n")
    if not frames.empty:
        fastest = agg.sort_values("T_p50").iloc[0]
        slowest = agg.sort_values("T_p50").iloc[-1]
        report.append(f"- Самая быстрая модель по p50: `{fastest['model']}` "
                      f"({fastest['T_p50']:.1f} мс, {fastest['fps']:.1f} Гц).")
        report.append(f"- Самая медленная: `{slowest['model']}` "
                      f"({slowest['T_p50']:.1f} мс).")
    if bench.get("results"):
        best = max(bench["results"], key=lambda r: r.get("mAP50", 0))
        report.append(f"- Лучший mAP@0.5: `{best['model']}` ({best['mAP50']:.3f}); "
                      f"mAP@0.5:0.95={best['mAP50_95']:.3f}.")
    if sweep_files and "best_f1_df" in locals() and not best_f1_df.empty:
        b = best_f1_df.iloc[0]
        report.append(f"- Лучший F1 по свипу: `{b['model']}` "
                      f"({b['best_f1']:.3f} при conf {b['best_conf']:.2f}, "
                      f"P={b['p']:.3f}, R={b['r']:.3f}).")
    elif not dets.empty:
        best_f1 = qual.sort_values("f1", ascending=False).iloc[0]
        report.append(f"- F1 при conf 0.05: `{best_f1['model']}` "
                      f"({best_f1['f1']:.3f}).")
    report.append("- Ограничения: синтетические нетекстурированные ассеты, "
                  "88 GT, RAPL недоступен; доменный сдвиг подтверждается confusion "
                  "(couch/bed → airplane, vase → bird).")
    report.append("")

    with open(os.path.join(out, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    summary_out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overview": overview,
        "latency": agg.round(4).to_dict(orient="records"),
        "quality": qual.round(4).to_dict(orient="records") if not dets.empty else [],
        "best_map50": max(bench.get("results", []), key=lambda r: r.get("mAP50", 0), default=None),
        "ros": ros,
        "rss": rss,
        "files": {
            "plots": sorted(os.listdir(plots)),
            "tables": sorted(os.listdir(tables)),
        },
    }
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary_out, f, ensure_ascii=False, indent=2)

    print("EDA готово:", out)
    print("plots:", len(os.listdir(plots)), "tables:", len(os.listdir(tables)))
    print("REPORT.md и summary.json записаны")


if __name__ == "__main__":
    main()
