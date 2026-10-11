"""Go2 locomotion env in MuJoCo Playground (fork of the Go1 env).

Playground ships a Go1 quadruped env; there is no Go2. This module reuses
the Go1 joystick task unchanged, but patches the Go1 constants and asset
loader so the task runs on the Unitree Go2 MJCF from MuJoCo Menagerie.

Patching (done once on import):

* ``ROOT_BODY``        -> ``base``          (Go2 torso, Go1 uses ``trunk``)
* ``FEET_SITES``       -> ``*_foot``        (Go2 foot sites)
* ``FEET_GEOMS``       -> ``FR/FL/RR/RL``   (Go2 foot geoms)
* ``FEET_POS_SENSOR``  -> ``*_foot_pos``
* ``task_to_xml``      -> our Go2 flat scene
* ``base.get_assets``  -> our scene + Go2 menagerie assets

The Go2 scene (``xmls/scene_go2_flat.xml``) adds the sensors the Go1 task
expects (upvector, local_linvel, foot pos/linvel, floor contacts), which
are missing from the stock Go2 MJCF.
"""

from __future__ import annotations

import os

from etils import epath

from mujoco_playground._src import mjx_env
from mujoco_playground._src.locomotion.go1 import base as go1_base
from mujoco_playground._src.locomotion.go1 import go1_constants as consts
from mujoco_playground._src.locomotion.go1 import joystick as go1_joystick

XML_DIR = epath.Path(os.path.dirname(os.path.abspath(__file__))) / "xmls"
SCENE_FLAT = XML_DIR / "scene_go2_flat.xml"


def _patch_constants() -> None:
    consts.ROOT_BODY = "base"
    consts.FEET_SITES = ["FR_foot", "FL_foot", "RR_foot", "RL_foot"]
    consts.FEET_GEOMS = ["FR", "FL", "RR", "RL"]
    consts.FEET_POS_SENSOR = [f"{site}_pos" for site in consts.FEET_SITES]

    def task_to_xml(task_name: str) -> epath.Path:
        return SCENE_FLAT

    consts.task_to_xml = task_to_xml


def _patch_assets() -> None:
    def get_assets() -> dict[str, bytes]:
        assets: dict[str, bytes] = {}
        mjx_env.update_assets(assets, XML_DIR, "*.xml")
        menagerie_go2 = mjx_env.MENAGERIE_PATH / "unitree_go2"
        mjx_env.update_assets(assets, menagerie_go2, "*.xml")
        mjx_env.update_assets(assets, menagerie_go2 / "assets")
        return assets

    go1_base.get_assets = get_assets


def default_config():
    """Go2 config: Go1 joystick task with Go2 gains and action scale."""
    cfg = go1_joystick.default_config()
    cfg.Kp = 40.0
    cfg.Kd = 0.5
    cfg.action_scale = 0.25
    # Go2 has more contacts than Go1; avoid nefc overflow.
    cfg.njmax = 100
    cfg.naconmax = 8 * 8192
    return cfg


def load_env(config=None, **overrides):
    """Create the Go2 joystick env (flat terrain)."""
    if config is None:
        config = default_config()
    for key, value in overrides.items():
        config[key] = value
    return go1_joystick.Joystick(task="flat_terrain", config=config)


_patch_constants()
_patch_assets()


if __name__ == "__main__":
    import jax
    import numpy as np

    env = load_env()
    rng = jax.random.PRNGKey(0)
    state = env.reset(rng)
    print("reset ok; obs keys:", list(state.obs.keys()))
    step = jax.jit(env.step)
    for _ in range(30):
        rng, key = jax.random.split(rng)
        action = jax.random.uniform(key, (env.action_size,), minval=-1, maxval=1)
        state = step(state, action)
    print("30 steps ok; reward:", float(state.reward), "done:", bool(state.done))
    print("device:", jax.devices())
