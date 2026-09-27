#!/usr/bin/env python3
"""Генератор рельефа для Gazebo (heightmap PNG + SDF) под 5 сценариев НИР.

Пишет grayscale-PNG (16-бит) карты высот и фрагмент `<heightmap>` для SDF.
Пути менять в `--out-dir`; имена сценариев — по docs/NIRS (ch3_11_testing.md).

Запуск:
    python3 scripts/generate_terrain.py --out-dir src/gazebo_sim/world/terrain
"""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

import numpy as np

SIZE = 256  # разрешение карты высот
WORLD = 20.0  # размер мира (м)


def _write_png16(path: Path, img: np.ndarray) -> None:
    """Записать 16-битный grayscale PNG без внешних зависимостей."""
    h, w = img.shape
    raw = b"".join(b"\x00" + img[r].astype(">u2").tobytes() for r in range(h))
    chunks = []

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    chunks.append(b"\x89PNG\r\n\x1a\n")
    chunks.append(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 16, 0, 0, 0, 0)))
    chunks.append(chunk(b"IDAT", zlib.compress(raw, 9)))
    chunks.append(chunk(b"IEND", b""))
    path.write_bytes(b"".join(chunks))


def _norm(z: np.ndarray) -> np.ndarray:
    """Нормализовать высоты в 0..65535."""
    z = z - z.min()
    if z.max() > 0:
        z = z / z.max()
    return (z * 65535).astype(np.uint16)


def scenarios() -> dict[str, np.ndarray]:
    """5 сценариев НИР (docs/NIRS/ch3/ch3_11_testing.md)."""
    x = np.linspace(-WORLD / 2, WORLD / 2, SIZE)
    y = np.linspace(-WORLD / 2, WORLD / 2, SIZE)
    xx, yy = np.meshgrid(x, y)
    rng = np.random.default_rng(42)

    out: dict[str, np.ndarray] = {}
    # 1 — ровная дорога (baseline)
    out["s1_flat"] = np.zeros_like(xx)
    # 2 — лёгкие неровности (трава/гравий/камни 0.02..0.05 м)
    out["s2_bumps"] = 0.03 * (np.sin(3 * xx) * np.sin(3 * yy)) + 0.01 * rng.standard_normal(xx.shape)
    # 3 — холмы и подъёмы: z = A sin(wx x) cos(wy y), A=0.3
    out["s3_hills"] = 0.3 * np.sin(0.5 * xx) * np.cos(0.5 * yy)
    # 4 — смешанный (плоско + бугры + холм)
    out["s4_mixed"] = out["s2_bumps"] + 0.15 * np.exp(-(xx**2 + yy**2) / 25.0)
    # 5 — препятствия (ящики/бордюры 0.1..0.3 м — ступени)
    z5 = np.zeros_like(xx)
    z5[(np.abs(xx) < 1.5) & (np.abs(yy) < 1.5)] = 0.25  # плато-препятствие
    z5[(xx > 4) & (xx < 6)] = 0.15  # бордюр
    out["s5_obstacles"] = z5
    return out


def sdf_snippet(name: str, z_max: float) -> str:
    """Фрагмент SDF с heightmap для вставки в world."""
    return f"""
    <model name="{name}">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <heightmap>
              <uri>model://terrain/{name}.png</uri>
              <size>{WORLD} {WORLD} {z_max:.3f}</size>
              <pos>0 0 0</pos>
            </heightmap>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <heightmap>
              <uri>model://terrain/{name}.png</uri>
              <size>{WORLD} {WORLD} {z_max:.3f}</size>
              <pos>0 0 0</pos>
              <texture><diffuse>0.6 0.6 0.5</diffuse></texture>
              <blend><min_height>0.0</min_height><fade_dist>0.1</fade_dist></blend>
            </heightmap>
          </geometry>
        </visual>
      </link>
    </model>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="src/gazebo_sim/world/terrain")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    sc = scenarios()
    snippets = []
    for name, z in sc.items():
        _write_png16(out / f"{name}.png", _norm(z))
        snippets.append(sdf_snippet(name, max(float(z.max()), 0.01)))
        print(f"{name}: z_max={z.max():.3f} -> {name}.png")

    (out / "terrain_snippets.sdf").write_text(
        "<!-- вставки <model> в .world (по одному сценарию) -->\n" + "".join(snippets)
    )
    print(f"\nготово: {out} (+ terrain_snippets.sdf)")


if __name__ == "__main__":
    main()
