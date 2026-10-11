"""Evaluate the trained Go2 policy: rollout and locomotion metrics."""

from __future__ import annotations

import functools
import os
import pickle

import jax
import numpy as np
from brax.training.agents.ppo import networks as ppo_networks
from mujoco_playground.config import locomotion_params

import go2_env


def build_policy(params_path: str, env):
    ppo_params = locomotion_params.brax_ppo_config("Go1JoystickFlatTerrain")
    network = ppo_networks.make_ppo_networks(
        observation_size=env.observation_size,
        action_size=env.action_size,
        **ppo_params.network_factory,
    )
    inference_fn = ppo_networks.make_inference_fn(network)
    with open(params_path, "rb") as f:
        params = pickle.load(f)
    return inference_fn(params, deterministic=True)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="sim/mjrl_go2/policy.pkl")
    ap.add_argument("--steps", type=int, default=800)
    ap.add_argument("--vx", type=float, default=0.8)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--residual", action="store_true")
    args = ap.parse_args()

    if args.residual:
        import go2_residual_env

        env = go2_residual_env.load_env(go2_residual_env.default_config())
    else:
        env = go2_env.load_env(go2_env.default_config())
    policy = build_policy(args.policy, env)

    rng = jax.random.PRNGKey(1)
    state = env.reset(rng)
    cmd = jax.numpy.array([args.vx, 0.0, 0.0])
    xs, ys, zs, vxs = [], [], [], []
    for _ in range(args.steps):
        state = state.replace(
            info={
                **state.info,
                "command": cmd,
                "steps_until_next_cmd": jax.numpy.int32(10**7),
            }
        )
        rng, k = jax.random.split(rng)
        obs = state.obs["state"] if isinstance(state.obs, dict) else state.obs
        action, _ = policy(obs, k)
        state = env.step(state, action)
        q = np.asarray(state.data.qpos)
        xs.append(q[0])
        ys.append(q[1])
        zs.append(q[2])
        vxs.append(float(np.asarray(state.data.qvel)[0]))

    xs, ys, zs, vxs = map(np.array, (xs, ys, zs, vxs))
    n = len(xs)
    dt = 0.02
    print(f"steps={n} dur={n * dt:.1f}s")
    print(f"x: first={xs[10]:.3f} last={xs[-1]:.3f} dx={xs[-1] - xs[10]:.3f}")
    print(f"mean vx={vxs[50:].mean():.3f} m/s")
    print(f"z: mean={zs.mean():.3f} min={zs.min():.3f} max={zs.max():.3f}")
    print(f"|y| drift={abs(ys[-1] - ys[10]):.3f}")

    csv_path = args.csv or (
        "sim/mjrl_go2/results/" + os.path.splitext(os.path.basename(args.policy))[0] + "_eval.csv"
    )
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("t,x,y,z,vx,cmd_vx\n")
        for i in range(n):
            f.write(f"{i * dt:.3f},{xs[i]:.5f},{ys[i]:.5f},{zs[i]:.5f},"
                    f"{vxs[i]:.5f},{args.vx}\n")
    print("saved eval csv ->", csv_path)


if __name__ == "__main__":
    main()
