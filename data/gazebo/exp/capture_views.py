"""Съёмка всех ракурсов бенчмарка через /world/exp/set_pose."""
import argparse
import json
import math
import subprocess

SCENE = "data/gazebo/exp/scene.json"
FRAMES = "/root/ws/data/exp/frames"


def quat(pitch, yaw):
    sy, cy = math.sin(pitch / 2), math.cos(pitch / 2)
    sz, cz = math.sin(yaw / 2), math.cos(yaw / 2)
    return (-sz * sy, cz * sy, sz * cy, cz * cy)


def run(inner):
    return subprocess.run(
        ["docker", "compose", "exec", "-T", "simulator", "bash", "-lc", inner],
        text=True, capture_output=True,
    )


def main():
    global SCENE, FRAMES
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default=SCENE)
    ap.add_argument("--frames", default=FRAMES)
    args = ap.parse_args()
    SCENE, FRAMES = args.scene, args.frames

    with open(SCENE, encoding="utf-8") as f:
        scene = json.load(f)
    views = scene["views"]
    for i, v in enumerate(views):
        x, y, z, roll, pitch, yaw = v["pose"]
        qx, qy, qz, qw = quat(pitch, yaw)
        req = (
            f'name: "camera", position: {{x: {x:.4f}, y: {y:.4f}, z: {z:.4f}}}, '
            f"orientation: {{x: {qx:.6f}, y: {qy:.6f}, z: {qz:.6f}, w: {qw:.6f}}}"
        )
        inner = (
            "source /opt/ros/jazzy/setup.bash; "
            "gz service -s /world/exp/set_pose --reqtype gz.msgs.Pose "
            f"--reptype gz.msgs.Boolean --timeout 5000 --req '{req}'"
        )
        r = run(inner)
        if "data: true" not in r.stdout:
            print(f"[{i}] set_pose FAIL: {r.stdout.strip()[:120]} {r.stderr.strip()[:120]}")
            continue

        out = f"{FRAMES}/{v['name']}"
        inner = (
            f"mkdir -p {out}; rm -f {out}/*.png; "
            "source /opt/ros/jazzy/setup.bash; "
            f"timeout 40 python3 /root/ws/data/exp/capture.py 3 {out}"
        )
        c = run(inner)
        if "saved 1" not in c.stdout:
            print(f"[{i}] capture FAIL: {c.stdout.strip()[-120:]}")
            continue
        print(f"[{i + 1}/{len(views)}] {v['name']}", flush=True)
    print("done")


if __name__ == "__main__":
    main()
