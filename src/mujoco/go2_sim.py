"""Базовый запуск Unitree Go2 в MuJoCo.

Загружает модель menagerie, прогоняет физику и (опционально) рендерит кадр.
Используется как фундамент для ROS 2-моста и RL-похода (см. docs/mujoco/).

Запуск:
    .venv-mujoco/bin/python src/mujoco/go2_sim.py --duration 3 --render out.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import mujoco
import numpy as np

REPO = Path(__file__).resolve().parents[2]
MENAGERIE = REPO / "external" / "mujoco_menagerie" / "unitree_go2"
SCENE = MENAGERIE / "scene.xml"


def build_model() -> mujoco.MjModel:
    if not SCENE.exists():
        raise FileNotFoundError(f"нет модели: {SCENE}")
    return mujoco.MjModel.from_xml_path(str(SCENE))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=3.0)
    ap.add_argument("--render", type=str, default=None)
    args = ap.parse_args()

    model = build_model()
    data = mujoco.MjData(model)
    print(
        f"model: nq={model.nq} nv={model.nv} nu={model.nu} "
        f"dt={model.opt.timestep} bodies={model.nbody}",
    )
    print("joints:", [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
                      for i in range(model.njnt)])

    n_steps = int(args.duration / model.opt.timestep)
    for _ in range(n_steps):
        mujoco.mj_step(model, data)

    base = data.qpos[:3]
    print(f"после {args.duration:.1f}с: base pos={base.round(3)} z={base[2]:.3f}")

    if args.render:
        renderer = mujoco.Renderer(model, height=480, width=640)
        renderer.update_scene(data)
        img = renderer.render()
        import imageio.v3 as iio

        iio.imwrite(args.render, img)
        print("кадр:", args.render)


if __name__ == "__main__":
    main()
