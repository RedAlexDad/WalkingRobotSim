"""Unit-тесты параметров MuJoCo-моста (маппинги, PD, RPY).

Чистые функции без ROS — запускаются всегда.
Запуск:
    .venv-mujoco/bin/python -m pytest src/mujoco/test_mujoco_bridge.py -q
"""

from __future__ import annotations

import numpy as np
from mujoco_params import (
    CMD_TO_MJ,
    DEFAULT_MJ,
    KD,
    KP,
    LIMIT,
    VMAX,
    _rpy,
)


def test_cmd_to_mj_is_permutation() -> None:
    assert sorted(CMD_TO_MJ.tolist()) == list(range(12))


def test_cmd_maps_fr_to_mj_fl() -> None:
    # CMD порядок FR,FL,RR,RL -> MJ порядок FL,FR,RL,RR.
    assert CMD_TO_MJ[0] == 3  # FR_hip -> MJ-индекс 3
    assert CMD_TO_MJ[3] == 0  # FL_hip -> MJ-индекс 0


def test_default_mj_length() -> None:
    assert len(DEFAULT_MJ) == 12


def test_gains_match_reference() -> None:
    assert (KP, KD, LIMIT, VMAX) == (50.0, 3.5, 23.5, 30.0)


def test_rpy_identity() -> None:
    r, p, y = _rpy(np.array([1.0, 0.0, 0.0, 0.0]))
    assert abs(r) < 1e-9
    assert abs(p) < 1e-9
    assert abs(y) < 1e-9


def test_rpy_yaw_90() -> None:
    s = np.sqrt(0.5)
    _, _, y = _rpy(np.array([s, 0.0, 0.0, s]))
    assert abs(y - np.pi / 2) < 1e-6


def test_cmd_reindex_roundtrip() -> None:
    cmd = np.arange(12, dtype=np.float32)
    mj = np.zeros(12, dtype=np.float32)
    mj[CMD_TO_MJ] = cmd
    back = mj[CMD_TO_MJ]
    assert np.array_equal(back, cmd)
