"""Go2 joystick env with an added trot-reference reward (bootstrap)."""

from __future__ import annotations

import jax
import jax.numpy as jp

import go2_env
from mujoco_playground._src.locomotion.go1 import joystick as go1_joystick

# Trot: diagonals in phase. Joint/actuator order is FL, FR, RL, RR.
FREQ = 2.0
AMP_THIGH = 0.15
AMP_CALF = 0.15
PHASE_OFFSET = jp.array([0.0, jp.pi, jp.pi, 0.0])
Q_REF_DEFAULT = jp.array([0.0, 0.9, -1.8])


def _trot_reference(phase: jax.Array) -> jax.Array:
    p = phase + PHASE_OFFSET
    thigh = Q_REF_DEFAULT[1] + AMP_THIGH * jp.sin(p)
    calf = Q_REF_DEFAULT[2] - AMP_CALF * jp.sin(p)
    return jp.stack([jp.zeros(4), thigh, calf], axis=1).reshape(-1)


class TrotJoystick(go1_joystick.Joystick):
    """Joystick task plus a reward for tracking a trot joint reference."""

    def reset(self, rng):
        state = super().reset(rng)
        info = dict(state.info)
        info["phase"] = jp.array(0.0)
        return state.replace(info=info)

    def step(self, state, action):
        state = super().step(state, action)
        info = dict(state.info)
        info["phase"] = (info["phase"] + 2 * jp.pi * FREQ * self.dt) % (
            2 * jp.pi
        )
        return state.replace(info=info)

    def _get_reward(self, data, action, info, metrics, done,
                    first_contact, contact):
        rew = super()._get_reward(
            data, action, info, metrics, done, first_contact, contact)
        qref = _trot_reference(info["phase"])
        rew["trot"] = jp.exp(-jp.sum((data.qpos[7:] - qref) ** 2) / 0.5)
        return rew


def default_config(trot_scale: float = 2.0):
    cfg = go2_env.default_config()
    cfg.reward_config.scales.trot = trot_scale
    return cfg


def load_env(config=None):
    if config is None:
        config = default_config()
    return TrotJoystick(task="flat_terrain", config=config)
