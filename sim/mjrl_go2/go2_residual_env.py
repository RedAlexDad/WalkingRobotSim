"""Go2 joystick env with residual RL on top of an open-loop trot.

The base trot (open-loop, time-based) already translates the robot; the
policy learns a residual on top of it to stabilise and track commands.
The phase is known to the base generator, so it need not be observed.
"""

from __future__ import annotations

import jax
import jax.numpy as jp

import go2_env
from mujoco_playground._src.locomotion.go1 import joystick as go1_joystick

FREQ = 2.0
AMP = 0.15
PHASE_OFFSET = jp.array([0.0, jp.pi, jp.pi, 0.0])  # FL, FR, RL, RR
LEG_DEFAULT = jp.array([0.0, 0.9, -1.8])
RESIDUAL_SCALE = 0.25


class ResidualJoystick(go1_joystick.Joystick):
    """Joystick task; action = base_trot(phase) + scale * policy_residual."""

    def _base_action(self, phase: jax.Array) -> jax.Array:
        p = phase + PHASE_OFFSET
        thigh = LEG_DEFAULT[1] + AMP * jp.sin(p)
        calf = LEG_DEFAULT[2] - AMP * jp.sin(p)
        qref = jp.stack([jp.zeros(4), thigh, calf], axis=1).reshape(-1)
        default = jp.tile(LEG_DEFAULT, 4)
        return (qref - default) / self._config.action_scale

    def reset(self, rng):
        state = super().reset(rng)
        info = dict(state.info)
        info["phase"] = jp.array(0.0)
        return state.replace(info=info)

    def step(self, state, action):
        phase = state.info["phase"]
        total = jp.clip(
            self._base_action(phase) + RESIDUAL_SCALE * action, -1.0, 1.0
        )
        state = super().step(state, total)
        info = dict(state.info)
        info["phase"] = (phase + 2 * jp.pi * FREQ * self.dt) % (2 * jp.pi)
        return state.replace(info=info)


def default_config(residual_scale: float = RESIDUAL_SCALE):
    cfg = go2_env.default_config()
    return cfg


def load_env(config=None):
    if config is None:
        config = default_config()
    return ResidualJoystick(task="flat_terrain", config=config)
