"""Запуск обученной политики Go2 (IsaacLab physx_policy.pt) в MuJoCo.

Идея: политика уже обучена (48 наблюдений → 12 действий). В MuJoCo момент
можно прикладывать напрямую, поэтому повторяем закон эталона
(isaacsim-river-bridge): tau = kp*(target-q) - kd*dq с конвертом DCMotor.

Запуск:
    .venv-mujoco/bin/python src/mujoco/go2_policy_mj.py --duration 10 --vx 0.5
"""
from __future__ import annotations

import argparse
from pathlib import Path

import mujoco
import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
SCENE = REPO / "external" / "mujoco_menagerie" / "unitree_go2" / "scene.xml"
POLICY = REPO / "src" / "isaac" / "assets" / "Isaac" / "Samples" / "Policies" / "go2" / "physx_policy.pt"

# Порядок суставов MuJoCo = FL, FR, RL, RR × (hip, thigh, calf) — совпадает
# с порядком Go2 в IsaacLab.
DEFAULT = np.array(
    [0.1, 0.8, -1.5,   # FL
     -0.1, 0.8, -1.5,  # FR
     0.1, 1.0, -1.5,   # RL
     -0.1, 1.0, -1.5], # RR
    dtype=np.float32,
)

KP, KD, LIMIT, VMAX = 25.0, 0.5, 23.5, 30.0
ACTION_SCALE = 0.25


def quat_to_mat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=10.0)
    ap.add_argument("--vx", type=float, default=0.5)
    args = ap.parse_args()

    model = mujoco.MjModel.from_xml_path(str(SCENE))
    data = mujoco.MjData(model)
    policy = torch.jit.load(str(POLICY), map_location="cpu").eval()
    torch.set_num_threads(1)

    # Начальная поза — стоячая (default), корпус чуть выше.
    mujoco.mj_resetData(model, data)
    data.qpos[2] = 0.30
    data.qpos[3:7] = [1, 0, 0, 0]
    for i in range(12):
        data.qpos[7 + i] = DEFAULT[i]
    mujoco.mj_forward(model, data)

    cmd = np.array([args.vx, 0.0, 0.0], dtype=np.float32)
    last_action = np.zeros(12, dtype=np.float32)

    n = int(args.duration / model.opt.timestep)
    decimation = 10  # политика 50 Гц при dt=0.002
    min_z = 1e9
    for step in range(n):
        if step % decimation == 0:
            mat = quat_to_mat(data.qpos[3:7])
            vel = np.concatenate([data.qvel[:3], data.qvel[3:6]])  # [lin, ang] в мире
            obs = np.concatenate([
                mat.T @ vel[:3],            # lin vel (body)
                mat.T @ vel[3:],            # ang vel (body)
                mat.T @ np.array([0, 0, -1], dtype=np.float32),  # gravity (body)
                cmd,
                (data.qpos[7:19] - DEFAULT).astype(np.float32),
                data.qvel[6:18].astype(np.float32),
                last_action,
            ]).astype(np.float32)
            with torch.inference_mode():
                last_action = policy(torch.from_numpy(obs[None]))[0].numpy().copy()
            target = DEFAULT + ACTION_SCALE * last_action
        q = data.qpos[7:19]
        dq = data.qvel[6:18]
        tau = KP * (target - q) - KD * dq
        upper = np.clip(LIMIT * (1 - dq / VMAX), 0, LIMIT)
        lower = np.clip(LIMIT * (-1 - dq / VMAX), -LIMIT, 0)
        data.ctrl[:] = np.clip(tau, lower, upper)
        mujoco.mj_step(model, data)
        min_z = min(min_z, float(data.qpos[2]))

    print(f"после {args.duration:.1f}с: base x={data.qpos[0]:+.3f} y={data.qpos[1]:+.3f} z={data.qpos[2]:.3f} | min_z={min_z:.3f}")
    print(f"скорость x (м/с) ≈ {data.qpos[0] / args.duration:+.3f}")


if __name__ == "__main__":
    main()
