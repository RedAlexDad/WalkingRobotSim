"""Wrapper-based eval: measure feet motion and base speed of the policy."""

import numpy as np
import jax
import pickle

import go2_env
from mujoco_playground._src import wrapper as _wrapper
from brax.training.agents.ppo import networks as ppo_networks
from mujoco_playground.config import locomotion_params


def main():
    cfg = go2_env.default_config()
    env = go2_env.load_env(cfg)
    wenv = _wrapper.wrap_for_brax_training(env, episode_length=cfg.episode_length,
                                           action_repeat=1)
    pp = locomotion_params.brax_ppo_config("Go1JoystickFlatTerrain")
    net = ppo_networks.make_ppo_networks(
        observation_size=env.observation_size, action_size=env.action_size,
        **pp.network_factory)
    pol = ppo_networks.make_inference_fn(net)(
        pickle.load(open("policy.pkl", "rb")), deterministic=True)

    st = wenv.reset(jax.random.PRNGKey(0))
    rng = jax.random.PRNGKey(1)
    cmd = jax.numpy.array([0.8, 0.0, 0.0])
    foot_ids = [env.mj_model.site(n).id for n in
                ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]]
    xs, vxs, zs, fz = [], [], [], []
    for i in range(500):
        st = st.replace(info={**st.info, "command": cmd,
                              "steps_until_next_cmd": jax.numpy.int32(10**7)})
        rng, k = jax.random.split(rng)
        act, _ = pol(st.obs, k)
        st = wenv.step(st, act)
        if i > 50:
            q = np.asarray(st.data.qpos)
            xs.append(q[0]); zs.append(q[2])
            vxs.append(float(np.asarray(st.data.qvel)[0]))
            fz.append(np.asarray(st.data.site_xpos)[foot_ids, 2])
    fz = np.array(fz)
    print("wrapper eval: dx=%.3f mean vx=%.3f z=%.3f" % (
        xs[-1] - xs[0], np.mean(vxs), np.mean(zs)), flush=True)
    print("foot z: mean=%s std=%s max-min=%s" % (
        np.round(fz.mean(0), 3), np.round(fz.std(0), 4),
        np.round(fz.max(0) - fz.min(0), 3)), flush=True)


if __name__ == "__main__":
    main()
