#!/usr/bin/env python3
"""Генератор рельефа для Gazebo под 5 сценариев НИР.

Пишет grayscale-PNG (16-бит) — карту высот — и OBJ-меш той же поверхности.
Меш используется в model.sdf вместо <heightmap>: визуальный <heightmap>
рендерится через OGRE-Next Terra HLMS и роняет gz-rendering на встроенной
AMD (radeonsi), а физика dartsim не поддерживает heightmap-коллизию
(см. gazebosim/gz-sim#3479). Меш работает и в рендере, и в физике.

Пути менять в `--out-dir`; имена сценариев — по docs/NIRS (ch3_11_testing.md).

Запуск:
    python3 scripts/generate_terrain.py --out-dir src/gazebo_sim/models/terrain
"""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

import numpy as np

SIZE = 256  # разрешение карты высот (PNG)
MESH = 129  # число вершин меша по стороне (2^7+1)
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


def scenarios(size: int = SIZE) -> dict[str, np.ndarray]:
    """5 сценариев НИР (docs/NIRS/ch3/ch3_11_testing.md)."""
    x = np.linspace(-WORLD / 2, WORLD / 2, size)
    y = np.linspace(-WORLD / 2, WORLD / 2, size)
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


def _write_obj(path: Path, z: np.ndarray) -> None:
    """Записать OBJ-меш поверхности z (метры, вершины n x n, шаг по сетке)."""
    n = z.shape[0]
    step = WORLD / (n - 1)
    x0 = -WORLD / 2
    y0 = -WORLD / 2

    lines = [f"# terrain mesh {n}x{n}, {WORLD}x{WORLD} m"]
    for j in range(n):
        y = y0 + j * step
        for i in range(n):
            lines.append(f"v {x0 + i * step:.4f} {y:.4f} {z[j, i]:.4f}")

    dzdx = np.gradient(z, step, axis=1)
    dzdy = np.gradient(z, step, axis=0)
    for j in range(n):
        for i in range(n):
            nx, ny, nz = -dzdx[j, i], -dzdy[j, i], 1.0
            norm = float(np.sqrt(nx * nx + ny * ny + nz * nz))
            lines.append(f"vn {nx / norm:.4f} {ny / norm:.4f} {nz / norm:.4f}")

    for j in range(n - 1):
        for i in range(n - 1):
            a = j * n + i + 1
            b = a + 1
            c = a + n
            d = c + 1
            lines.append(f"f {a}//{a} {b}//{b} {c}//{c}")
            lines.append(f"f {b}//{b} {d}//{d} {c}//{c}")

    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="src/gazebo_sim/models/terrain")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    maps_hi = scenarios(SIZE)
    maps_lo = scenarios(MESH)
    for name, z in maps_hi.items():
        _write_png16(out / f"{name}.png", _norm(z))
        _write_obj(out / f"{name}.obj", maps_lo[name])
        print(f"{name}: {name}.png + {name}.obj")

    print(f"\nготово: {out}")


if __name__ == "__main__":
    main()
