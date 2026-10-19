"""Генерация вариантов сцены: свет, джиттер камеры и видео-облёт."""
import argparse
import json
import os

import numpy as np

BASE = "data/gazebo/exp"


def light_world(world: str, diffuse: str, direction: str, ambient: str) -> str:
    world = world.replace("<diffuse>0.9 0.9 0.9 1</diffuse>",
                          f"<diffuse>{diffuse}</diffuse>")
    world = world.replace("<direction>0 0.3 -0.9</direction>",
                          f"<direction>{direction}</direction>")
    world = world.replace(
        "<material><ambient>0.45 0.45 0.45 1</ambient><diffuse>0.45 0.45 0.45 1</diffuse></material>",
        f"<material><ambient>{ambient}</ambient><diffuse>{ambient}</diffuse></material>",
    )
    return world


def jitter_views(scene, seed, dz=0.10, dxy=0.20, dyaw=0.035, dpitch=0.015):
    rng = np.random.default_rng(seed)
    out = json.loads(json.dumps(scene))
    for v in out["views"]:
        x, y, z, roll, pitch, yaw = v["pose"]
        v["pose"] = [
            x + float(rng.uniform(-dxy, dxy)),
            y + float(rng.uniform(-dxy, dxy)),
            max(0.8, z + float(rng.uniform(-dz, dz))),
            roll,
            pitch + float(rng.uniform(-dpitch, dpitch)),
            yaw + float(rng.uniform(-dyaw, dyaw)),
        ]
    return out


def video_scene(scene, n=30, radius=0.0, z=1.7, pitch=0.08):
    out = json.loads(json.dumps(scene))
    out["views"] = []
    for i in range(n):
        a = 2.0 * np.pi * i / n
        out["views"].append({
            "name": f"video_{i:02d}",
            "pose": [radius * np.cos(a), radius * np.sin(a), z, 0.0, pitch, a],
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    args = ap.parse_args()
    base = args.base
    scene = json.load(open(os.path.join(base, "scene.json"), encoding="utf-8"))
    world = open(os.path.join(base, "world.sdf"), encoding="utf-8").read()

    v1 = jitter_views(scene, seed=11, dz=0.08, dxy=0.15)
    v2 = jitter_views(scene, seed=22, dz=0.15, dxy=0.30, dyaw=0.05)
    video = video_scene(scene, n=30)

    for name, data in [("v1", v1), ("v2", v2), ("video", video)]:
        with open(os.path.join(base, f"scene_{name}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    w1 = light_world(world, "1.0 0.93 0.82 1", "0.6 0.4 -0.7", "0.42 0.40 0.36 1")
    w2 = light_world(world, "0.70 0.78 1.0 1", "-0.5 0.45 -0.8", "0.30 0.33 0.40 1")
    open(os.path.join(base, "world_v1.sdf"), "w", encoding="utf-8").write(w1)
    open(os.path.join(base, "world_v2.sdf"), "w", encoding="utf-8").write(w2)
    print("scenes:", [f"scene_{n}.json" for n in ("v1", "v2", "video")])
    print("worlds:", ["world_v1.sdf", "world_v2.sdf"])
    print("views:", len(v1["views"]), len(v2["views"]), len(video["views"]))


if __name__ == "__main__":
    main()
