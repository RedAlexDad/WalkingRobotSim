"""Train a Go2 locomotion policy in MuJoCo Playground (GPU, brax PPO).

Reuses the Go1 joystick task via ``go2_env`` (patched to run the Go2 MJCF)
and Playground's tuned PPO hyperparameters, with domain randomization
adapted to Go2 ids.

Example:
    .venv-mjrl/bin/python sim/mjrl_go2/train_go2.py --timesteps 5000000
"""

from __future__ import annotations

import argparse
import functools
import os
import pickle
import time

import jax

# brax 0.14 still calls jax.device_put_replicated / device_put_sharded,
# removed in jax >= 0.10. Both use pmap-style leading device axis.
if not hasattr(jax, "device_put_replicated"):

    def _device_put_replicated(tree, devices):
        n = len(devices)
        return jax.tree_util.tree_map(
            lambda v: jax.numpy.broadcast_to(v, (n,) + jax.numpy.shape(v)),
            tree,
        )

    jax.device_put_replicated = _device_put_replicated

if not hasattr(jax, "device_put_sharded"):

    def _device_put_sharded(shards, devices):
        return jax.device_put(jax.numpy.stack(shards, axis=0), devices[0])

    jax.device_put_sharded = _device_put_sharded

import numpy as np
from brax.training.agents.ppo import networks as ppo_networks
from brax.training.agents.ppo import train as ppo
from mujoco_playground._src import wrapper
from mujoco_playground.config import locomotion_params

import go2_env


def make_randomizer(env):
    """Domain randomization for Go2 (friction, mass, armature, CoM)."""
    mj = env.mj_model
    floor_geom_id = mj.geom("floor").id
    torso_body_id = mj.body("base").id
    n_joint_dofs = mj.nv - 6  # all dofs except the base freejoint

    from mujoco import mjx

    def domain_randomize(model: mjx.Model, rng: jax.Array):
        @jax.vmap
        def rand_dynamics(rng):
            rng, k = jax.random.split(rng)
            geom_friction = model.geom_friction.at[floor_geom_id, 0].set(
                jax.random.uniform(k, minval=0.4, maxval=1.0)
            )
            rng, k = jax.random.split(rng)
            frictionloss = model.dof_frictionloss[6:] * jax.random.uniform(
                k, shape=(n_joint_dofs,), minval=0.9, maxval=1.1
            )
            dof_frictionloss = model.dof_frictionloss.at[6:].set(frictionloss)
            rng, k = jax.random.split(rng)
            armature = model.dof_armature[6:] * jax.random.uniform(
                k, shape=(n_joint_dofs,), minval=1.0, maxval=1.05
            )
            dof_armature = model.dof_armature.at[6:].set(armature)
            rng, k = jax.random.split(rng)
            dpos = jax.random.uniform(k, (3,), minval=-0.05, maxval=0.05)
            body_ipos = model.body_ipos.at[torso_body_id].set(
                model.body_ipos[torso_body_id] + dpos
            )
            rng, k = jax.random.split(rng)
            dmass = jax.random.uniform(
                k, shape=(model.nbody,), minval=0.9, maxval=1.1
            )
            body_mass = model.body_mass.at[:].set(model.body_mass * dmass)
            rng, k = jax.random.split(rng)
            torso_extra = jax.random.uniform(k, minval=-1.0, maxval=1.0)
            body_mass = body_mass.at[torso_body_id].set(
                body_mass[torso_body_id] + torso_extra
            )
            rng, k = jax.random.split(rng)
            qpos0 = model.qpos0
            qpos0 = qpos0.at[7:].set(
                qpos0[7:]
                + jax.random.uniform(
                    k, shape=(n_joint_dofs,), minval=-0.05, maxval=0.05
                )
            )
            return (
                geom_friction,
                body_ipos,
                body_mass,
                qpos0,
                dof_frictionloss,
                dof_armature,
            )

        (
            friction,
            body_ipos,
            body_mass,
            qpos0,
            dof_frictionloss,
            dof_armature,
        ) = rand_dynamics(rng)

        in_axes = jax.tree_util.tree_map(lambda x: None, model)
        in_axes = in_axes.tree_replace({
            "geom_friction": 0,
            "body_ipos": 0,
            "body_mass": 0,
            "qpos0": 0,
            "dof_frictionloss": 0,
            "dof_armature": 0,
        })
        model = model.tree_replace({
            "geom_friction": friction,
            "body_ipos": body_ipos,
            "body_mass": body_mass,
            "qpos0": qpos0,
            "dof_frictionloss": dof_frictionloss,
            "dof_armature": dof_armature,
        })
        return model, in_axes

    return domain_randomize


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=5_000_000)
    ap.add_argument("--num-envs", type=int, default=4096)
    ap.add_argument("--num-evals", type=int, default=5)
    ap.add_argument("--action-scale", type=float, default=0.25)
    ap.add_argument("--tracking-lin", type=float, default=1.0)
    ap.add_argument("--pose", type=float, default=None)
    ap.add_argument("--orientation", type=float, default=None)
    ap.add_argument("--feet-air-time", type=float, default=None)
    ap.add_argument("--entropy-cost", type=float, default=None)
    ap.add_argument("--impl", type=str, default="warp", choices=["jax", "warp"])
    ap.add_argument("--no-dr", action="store_true")
    ap.add_argument("--trot", action="store_true")
    ap.add_argument("--trot-scale", type=float, default=2.0)
    ap.add_argument("--residual", action="store_true")
    ap.add_argument("--out", type=str, default="sim/mjrl_go2/policy.pkl")
    args = ap.parse_args()

    cfg = go2_env.default_config()
    cfg.impl = args.impl
    cfg.action_scale = args.action_scale
    cfg.reward_config.scales.tracking_lin_vel = args.tracking_lin
    if args.pose is not None:
        cfg.reward_config.scales.pose = args.pose
    if args.orientation is not None:
        cfg.reward_config.scales.orientation = args.orientation
    if args.feet_air_time is not None:
        cfg.reward_config.scales.feet_air_time = args.feet_air_time
    if args.trot:
        import go2_trot_env

        cfg.reward_config.scales.trot = args.trot_scale
        env = go2_trot_env.load_env(cfg)
        eval_env = go2_trot_env.load_env(go2_trot_env.default_config())
    elif args.residual:
        import go2_residual_env

        env = go2_residual_env.load_env(cfg)
        eval_env = go2_residual_env.load_env(go2_residual_env.default_config())
    else:
        env = go2_env.load_env(cfg)
        eval_env = go2_env.load_env(go2_env.default_config())

    ppo_params = locomotion_params.brax_ppo_config("Go1JoystickFlatTerrain")
    ppo_params.num_timesteps = args.timesteps
    ppo_params.num_envs = args.num_envs
    ppo_params.num_evals = args.num_evals
    ppo_params.episode_length = cfg.episode_length
    if args.entropy_cost is not None:
        ppo_params.entropy_cost = args.entropy_cost

    network_factory = functools.partial(
        ppo_networks.make_ppo_networks,
        **ppo_params.network_factory,
    )

    times = [time.time()]
    csv_path = os.path.splitext(args.out)[0] + "_train.csv"
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    csv_file = open(csv_path, "w", encoding="utf-8")
    csv_file.write("num_steps,eval_reward,wall_s\n")

    def progress(num_steps, metrics):
        rew = metrics.get("eval/episode_reward", float("nan"))
        wall = time.time() - times[0]
        csv_file.write(f"{num_steps},{rew:.6f},{wall:.3f}\n")
        csv_file.flush()
        print(f"[{num_steps:>10}] eval_reward={rew:.3f} wall={wall:.0f}s",
              flush=True)

    train_params = dict(ppo_params)
    del train_params["network_factory"]

    train_fn = functools.partial(
        ppo.train,
        **train_params,
        network_factory=network_factory,
        progress_fn=progress,
        wrap_env_fn=wrapper.wrap_for_brax_training,
        randomization_fn=None if args.no_dr else make_randomizer(env),
    )

    make_policy, params, _ = train_fn(environment=env, eval_env=eval_env)
    csv_file.close()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "wb") as f:
        pickle.dump(
            jax.tree_util.tree_map(lambda x: np.asarray(x), params), f
        )
    print("saved policy ->", args.out)


if __name__ == "__main__":
    main()
