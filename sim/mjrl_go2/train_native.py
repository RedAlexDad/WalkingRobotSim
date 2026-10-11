"""Control experiment: train a native Playground env with the same harness."""

import argparse
import functools
import pickle

import jax
import numpy as np

import _compat  # noqa: F401  (restore jax pmap-style helpers)
from brax.training.agents.ppo import networks as ppo_networks
from brax.training.agents.ppo import train as ppo
from mujoco_playground import locomotion
from mujoco_playground._src import wrapper
from mujoco_playground.config import locomotion_params


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="Go1JoystickFlatTerrain")
    ap.add_argument("--timesteps", type=int, default=40_000_000)
    ap.add_argument("--num-envs", type=int, default=8192)
    ap.add_argument("--out", default="sim/mjrl_go2/native.pkl")
    a = ap.parse_args()

    cfg = locomotion.get_default_config(a.env)
    env = locomotion.load(a.env, config=cfg)
    eval_env = locomotion.load(a.env, config=locomotion.get_default_config(a.env))
    randomizer = locomotion.get_domain_randomizer(a.env)
    pp = locomotion_params.brax_ppo_config(a.env)
    pp.num_timesteps = a.timesteps
    pp.num_envs = a.num_envs
    pp.num_evals = 5
    net = functools.partial(ppo_networks.make_ppo_networks, **pp.network_factory)
    tp = dict(pp)
    del tp["network_factory"]
    fn = functools.partial(
        ppo.train, **tp, network_factory=net,
        progress_fn=lambda s, m: print(f"[{s}] {m.get('eval/episode_reward')}", flush=True),
        wrap_env_fn=wrapper.wrap_for_brax_training, randomization_fn=randomizer,
    )
    _, params, _ = fn(environment=env, eval_env=eval_env)
    pickle.dump(jax.tree_util.tree_map(lambda x: np.asarray(x), params), open(a.out, "wb"))
    print("saved", a.out, flush=True)

    # eval with forced forward command
    inf = ppo_networks.make_inference_fn(
        ppo_networks.make_ppo_networks(
            observation_size=env.observation_size, action_size=env.action_size,
            **pp.network_factory))(params, deterministic=True)
    st = env.reset(jax.random.PRNGKey(0))
    cmd = jax.numpy.array([0.8, 0.0, 0.0])
    xs = []
    for i in range(600):
        st = st.replace(info={**st.info, "command": cmd, "steps_until_next_cmd": jax.numpy.int32(10**7)})
        act, _ = inf(st.obs["state"] if isinstance(st.obs, dict) else st.obs, jax.random.PRNGKey(i))
        st = env.step(st, act)
        if i > 100:
            xs.append(float(np.asarray(st.data.qpos)[0]))
    print("native eval dx=%.3f" % (xs[-1] - xs[0]), flush=True)


if __name__ == "__main__":
    main()
