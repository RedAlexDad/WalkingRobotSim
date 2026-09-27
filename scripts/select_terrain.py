#!/usr/bin/env python3
"""Выбор сценария рельефа (копирует PNG в models/terrain/terrain.png).

    python3 scripts/select_terrain.py s3_hills
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

SC = ["s1_flat", "s2_bumps", "s3_hills", "s4_mixed", "s5_obstacles"]
BASE = Path(__file__).resolve().parent.parent / "src/gazebo_sim/models/terrain"


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in SC:
        print(f"укажите сценарий: {' | '.join(SC)}")
        raise SystemExit(2)
    shutil.copyfile(BASE / f"{sys.argv[1]}.png", BASE / "terrain.png")
    print(f"рельеф: {sys.argv[1]} -> models/terrain/terrain.png")


if __name__ == "__main__":
    main()
