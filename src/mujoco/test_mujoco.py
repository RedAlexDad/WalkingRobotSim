"""Unit-тесты MuJoCo-контура без ROS (модель Go2, геометрия, стойка).

Запуск:
    .venv-mujoco/bin/python -m pytest src/mujoco/test_mujoco.py -q
"""

from __future__ import annotations

import go2_sim
import numpy as np
import pytest
from go2_policy_mj import ACTION_SCALE, DEFAULT, POLICY_TO_MJ, quat_to_mat


def test_model_loads() -> None:
    model = go2_sim.build_model()
    assert model.nq == 19
    assert model.nv == 18
    assert model.nu == 12
    assert model.nbody == 14


def test_model_joint_order() -> None:
    import mujoco  # type: ignore[import-untyped]

    model = go2_sim.build_model()
    names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        for i in range(model.njnt)
    ]
    assert names[1:4] == ["FL_hip_joint", "FL_thigh_joint", "FL_calf_joint"]


def test_quat_identity() -> None:
    mat = quat_to_mat(np.array([1, 0, 0, 0], dtype=np.float64))
    assert np.allclose(mat, np.eye(3), atol=1e-6)


def test_quat_yaw_90() -> None:
    s = np.sqrt(0.5)
    mat = quat_to_mat(np.array([s, 0, 0, s], dtype=np.float64))  # yaw +90°
    assert np.allclose(mat @ np.array([1, 0, 0]), [0, 1, 0], atol=1e-6)


def test_policy_to_mj_is_permutation() -> None:
    assert sorted(POLICY_TO_MJ.tolist()) == list(range(12))


def test_default_length() -> None:
    assert len(DEFAULT) == 12


def test_default_pose_flat_feet() -> None:
    # Все calf = -1.5, thigh 0.8 (front) / 1.0 (rear).
    assert np.allclose(DEFAULT[[2, 5, 8, 11]], -1.5)
    assert np.allclose(DEFAULT[[1, 4]], 0.8)
    assert np.allclose(DEFAULT[[7, 10]], 1.0)


def test_action_scale_reference() -> None:
    assert ACTION_SCALE == 0.25


@pytest.mark.parametrize("val", [0.0, 0.5, 1.0, -0.5])
def test_quat_to_mat_orthonormal(val: float) -> None:
    ang = val * np.pi
    quat = np.array([np.cos(ang / 2), np.sin(ang / 2), 0, 0])
    mat = quat_to_mat(quat)
    assert np.allclose(mat @ mat.T, np.eye(3), atol=1e-6)
    assert abs(np.linalg.det(mat) - 1.0) < 1e-6
