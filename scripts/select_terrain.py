#!/usr/bin/env python3
"""Выбор сценария рельефа.

Пишет models/terrain/terrain.png (карта высот, для справки) и
models/terrain/terrain.obj (меш, используемый в model.sdf).

    python3 scripts/select_terrain.py s3_hills
"""
from __future__ import annotations

import sys
from pathlib import Path

SC = ["s1_flat", "s2_bumps", "s3_hills", "s4_mixed", "s5_obstacles"]
BASE = Path(__file__).resolve().parent.parent / "src/gazebo_sim/models/terrain"


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from generate_terrain import MESH, SIZE, _norm, _write_obj, _write_png16, scenarios

    if len(sys.argv) != 2 or sys.argv[1] not in SC:
        print(f"укажите сценарий: {' | '.join(SC)}")
        raise SystemExit(2)
    name = sys.argv[1]
    _write_png16(BASE / "terrain.png", _norm(scenarios(SIZE)[name]))
    _write_obj(BASE / "terrain.obj", scenarios(MESH)[name])
    print(f"рельеф: {name} -> models/terrain/terrain.png + terrain.obj")


if __name__ == "__main__":
    main()
