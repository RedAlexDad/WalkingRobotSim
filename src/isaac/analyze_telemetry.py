#!/usr/bin/env python3
"""Разбор CSV телеметрии IsaacLab → метрики для статьи.

Читает один или несколько CSV, записанных ``telemetry.TelemetryLogger``,
и считает метрики сравнения контроллеров:
    длительность, шаги, путь, средняя скорость,
    среднее/отклонение высоты Z, дрейф по Y,
    максимальные крены (roll/pitch), время до устойчивой походки,
    оценка энергозатрат (CoT).

Использование:
    python3 src/isaac/analyze_telemetry.py run_ik.csv run_rl.csv
    python3 src/isaac/analyze_telemetry.py --mass 15 --kp 75 --kd 0.5 *.csv
    python3 src/isaac/analyze_telemetry.py --json summary.json run.csv
    python3 src/isaac/analyze_telemetry.py --plot run.csv   # если есть matplotlib

Оценка CoT: момент считается как tau_i = kp*(cmd_i - q_i) - kd*dq_i
(неявный PD-актуатор), мощность P = Σ tau_i * dq_i, энергия E = ∫P dt,
CoT = E / (m * g * d). Это приближение (без учёта КПД и потерь), но
одинаковое для обоих контроллеров — годится для сравнения.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from statistics import mean, pstdev

G = 9.81


def _f(row: dict, key: str, default: float = float("nan")) -> float:
    v = row.get(key, "")
    if v == "" or v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def load_csv(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def compute_metrics(rows: list[dict], mass: float, kp: float, kd: float) -> dict:
    if not rows:
        return {"error": "пустой CSV"}

    t = [_f(r, "sim_time") for r in rows]
    x = [_f(r, "x") for r in rows]
    y = [_f(r, "y") for r in rows]
    z = [_f(r, "z") for r in rows]
    roll = [_f(r, "roll") for r in rows]
    pitch = [_f(r, "pitch") for r in rows]

    n = len(rows)
    t0, t1 = t[0], t[-1]
    duration = t1 - t0

    x0 = x[0]
    distance_x = x[-1] - x0
    y0 = y[0]
    drift_y = max(abs(v - y0) for v in y)

    # длина пути по горизонтали
    path = 0.0
    for i in range(1, n):
        path += math.hypot(x[i] - x[i - 1], y[i] - y[i - 1])

    mean_speed = path / duration if duration > 0 else float("nan")
    forward_speed = distance_x / duration if duration > 0 else float("nan")

    z_mean = mean(z)
    z_std = pstdev(z) if n > 1 else 0.0
    max_roll = max(abs(v) for v in roll)
    max_pitch = max(abs(v) for v in pitch)

    # время до устойчивой походки: первый момент, после которого |vx| > 0.05 м/с
    # удерживается не менее 0.5 с
    vx = [_f(r, "vx") for r in rows]
    t_steady = float("nan")
    hold = 0
    for i in range(n):
        if abs(vx[i]) > 0.05:
            hold += 1
            if hold >= 25:  # ~0.5 с при 50 Гц
                t_steady = t[i - hold + 1] - t0
                break
        else:
            hold = 0

    # энергозатраты (CoT)
    energy = 0.0
    for i in range(n):
        power = 0.0
        for j in range(12):
            q = _f(rows[i], f"q{j}")
            dq = _f(rows[i], f"dq{j}")
            cmd = _f(rows[i], f"cmd{j}")
            if math.isnan(q) or math.isnan(dq) or math.isnan(cmd):
                continue
            tau = kp * (cmd - q) - kd * dq
            power += tau * dq
        if i > 0:
            energy += abs(power) * (t[i] - t[i - 1])
    cot = energy / (mass * G * path) if path > 0 else float("nan")

    return {
        "rows": n,
        "duration_s": round(duration, 3),
        "distance_x_m": round(distance_x, 3),
        "path_length_m": round(path, 3),
        "mean_speed_mps": round(mean_speed, 4),
        "forward_speed_mps": round(forward_speed, 4),
        "z_mean_m": round(z_mean, 4),
        "z_std_m": round(z_std, 4),
        "max_roll_deg": round(math.degrees(max_roll), 2),
        "max_pitch_deg": round(math.degrees(max_pitch), 2),
        "drift_y_m": round(drift_y, 4),
        "t_steady_s": round(t_steady, 3) if not math.isnan(t_steady) else None,
        "energy_j": round(energy, 2),
        "cot": round(cot, 3) if not math.isnan(cot) else None,
        "params": {"mass_kg": mass, "kp": kp, "kd": kd},
    }


def maybe_plot(path: str, rows: list[dict]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"[analyze] matplotlib недоступен, график пропущен ({e})", flush=True)
        return

    t = [_f(r, "sim_time") for r in rows]
    x = [_f(r, "x") for r in rows]
    y = [_f(r, "y") for r in rows]
    z = [_f(r, "z") for r in rows]
    roll = [math.degrees(_f(r, "roll")) for r in rows]
    pitch = [math.degrees(_f(r, "pitch")) for r in rows]

    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].plot(x, y)
    ax[0, 0].set_title("Траектория X-Y (м)")
    ax[0, 0].set_xlabel("x, м")
    ax[0, 0].set_ylabel("y, м")
    ax[0, 0].axis("equal")
    ax[0, 1].plot(t, z)
    ax[0, 1].set_title("Высота Z(t)")
    ax[0, 1].set_xlabel("t, с")
    ax[0, 1].set_ylabel("z, м")
    ax[1, 0].plot(t, roll, label="roll")
    ax[1, 0].plot(t, pitch, label="pitch")
    ax[1, 0].set_title("Крен/тангаж (град)")
    ax[1, 0].set_xlabel("t, с")
    ax[1, 0].legend()
    ax[1, 1].plot(t, [_f(r, "vx") for r in rows], label="vx")
    ax[1, 1].set_title("Скорость vx(t)")
    ax[1, 1].set_xlabel("t, с")
    ax[1, 1].legend()

    fig.tight_layout()
    out = os.path.splitext(path)[0] + "_plot.png"
    fig.savefig(out, dpi=150)
    print(f"[analyze] график сохранён: {out}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Метрики телеметрии IsaacLab")
    ap.add_argument("csv", nargs="+", help="CSV-файлы телеметрии")
    ap.add_argument("--mass", type=float, default=15.0, help="масса робота, кг (Go2 ≈ 15)")
    ap.add_argument("--kp", type=float, default=75.0, help="stiffness (для оценки CoT)")
    ap.add_argument("--kd", type=float, default=0.5, help="damping (для оценки CoT)")
    ap.add_argument("--json", dest="json_out", default=None, help="сохранить сводку в JSON")
    ap.add_argument("--plot", action="store_true", help="построить графики (нужен matplotlib)")
    args = ap.parse_args()

    summary = {}
    for path in args.csv:
        if not os.path.isfile(path):
            print(f"[analyze] нет файла: {path}", file=sys.stderr)
            continue
        rows = load_csv(path)
        m = compute_metrics(rows, args.mass, args.kp, args.kd)
        summary[os.path.basename(path)] = m

        print(f"\n=== {os.path.basename(path)} ===")
        for k, v in m.items():
            if k == "params":
                continue
            print(f"  {k:20s} {v}")

        if args.plot:
            maybe_plot(path, rows)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
        print(f"\n[analyze] сводка сохранена: {args.json_out}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
