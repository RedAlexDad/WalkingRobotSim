"""Render the Go2 policy rollout to PNG frames (CPU MuJoCo + JAX policy)."""

import os
os.environ.setdefault("MUJOCO_GL", "egl")

import numpy as np
import jax
import mujoco
import pickle

import go2_env
from mujoco_playground._src.locomotion.go1 import base as go1_base
from brax.training.agents.ppo import networks as ppo_networks
from mujoco_playground.config import locomotion_params


def main():
    cfg = go2_env.default_config()
    env = go2_env.load_env(cfg)
    model = env.mj_model
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    model.opt.timestep = cfg.sim_dt

    pp = locomotion_params.brax_ppo_config("Go1JoystickFlatTerrain")
    net = ppo_networks.make_ppo_networks(
        observation_size=env.observation_size, action_size=env.action_size,
        **pp.network_factory)
    pol = ppo_networks.make_inference_fn(net)(
        pickle.load(open("policy.pkl", "rb")), deterministic=True)

    default = np.array(model.keyframe("home").qpos[7:])
    imu = model.site("imu").id
    local = model.sensor("local_linvel").id
    gyro = model.sensor("gyro").id
    n_sub = int(round(cfg.ctrl_dt / cfg.sim_dt))
    action_scale = cfg.action_scale
    cmd = np.array([0.8, 0.0, 0.0], dtype=np.float32)
    last = np.zeros(12, dtype=np.float32)

    os.makedirs("/tmp/go2_frames", exist_ok=True)
    renderer = mujoco.Renderer(model, height=360, width=480)
    rng = jax.random.PRNGKey(0)

    def obs():
        lin = data.sensor("local_linvel").data.astype(np.float32)
        g = data.sensor("gyro").data.astype(np.float32)
        xm = data.site_xmat[imu].reshape(3, 3)
        grav = (xm.T @ np.array([0, 0, -1], dtype=np.float32)).astype(np.float32)
        return np.hstack([lin, g, grav,
                          (data.qpos[7:] - default).astype(np.float32),
                          data.qvel[6:].astype(np.float32),
                          last, cmd]).astype(np.float32)

    saved = 0
    for i in range(400):
        if i % n_sub == 0:
            o = obs().reshape(1, -1)
            a = np.asarray(pol(o, rng)[0]).reshape(-1)
            last = a.astype(np.float32)
            data.ctrl[:] = default + a * action_scale
        mujoco.mj_step(model, data)
        if i % 25 == 0 and saved < 12:
            renderer.update_scene(data, camera="track")
            px = renderer.render()
            from PIL import Image
            Image.fromarray(px).save(f"/tmp/go2_frames/f{saved:02d}.png")
            saved += 1
    q = data.qpos
    print("frames=%d  x=%.3f z=%.3f  qpos7=%s" % (
        saved, q[0], q[2], np.round(q[7:], 2)), flush=True)


if __name__ == "__main__":
    main()
