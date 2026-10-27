#!/usr/bin/env python3
"""Проверка окна RViz на мерцание.

Снимает N кадров окна и считает долю изменившихся пикселей между
соседними кадрами. Порог 10 % отделяет полное почернение окна от
локальных обновлений маркеров (те дают единицы процентов).

Код возврата: 0 — чисто, 1 — мерцание, 2 — окно не найдено.
"""

import argparse
import subprocess
import sys
import time

import numpy as np
from PIL import Image


def find_window(title: str):
    out = subprocess.run(
        ["wmctrl", "-lG"], capture_output=True, text=True, check=True
    ).stdout
    for line in out.splitlines():
        parts = line.split(None, 7)
        if len(parts) < 8:
            continue
        if title in parts[7]:
            return parts[0], int(parts[4]), int(parts[5])
    return None


def grab(win: str, width: int, height: int, path: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "x11grab",
            "-draw_mouse",
            "0",
            "-window_id",
            win,
            "-video_size",
            f"{width}x{height}",
            "-i",
            ":0.0",
            "-frames:v",
            "1",
            path,
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--interval", type=float, default=0.4)
    parser.add_argument("--threshold", type=float, default=10.0)
    parser.add_argument("--settle", type=float, default=10.0)
    args = parser.parse_args()

    time.sleep(args.settle)
    win = find_window(args.title)
    if win is None:
        print(f"flicker: окно с '{args.title}' не найдено")
        return 2
    win_id, width, height = win

    previous = None
    worst = 0.0
    bad = 0
    for i in range(args.samples):
        path = f"/tmp/wrs_flicker_{i}.png"
        grab(win_id, width, height, path)
        frame = np.array(Image.open(path).convert("RGB"), dtype=np.int16)
        if previous is not None:
            diff = np.abs(frame - previous)
            changed = float((diff.max(axis=2) > 20).mean() * 100.0)
            worst = max(worst, changed)
            if changed > args.threshold:
                bad += 1
        previous = frame
        time.sleep(args.interval)

    print(
        f"flicker: кадров={args.samples} худший переход={worst:.2f}% "
        f"плохих={bad} порог={args.threshold}%"
    )
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
