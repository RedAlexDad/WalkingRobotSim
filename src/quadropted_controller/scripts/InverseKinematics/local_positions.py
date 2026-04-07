#!/usr/bin/env python3
"""
Вычисление локальных позиций точек опор в системе координат плеч.
Вынесено из InverseKinematics/robot_IK.py при декомпозиции.
"""

import numpy as np
from RoboticsUtilities.homogeneous_transforms import (
    homog_transform,
    homog_transform_inverse,
)
from RoboticsUtilities.rotation_matrices import rotxyz


def compute_local_positions(
    leg_positions, body_length, body_width, dx, dy, dz, roll, pitch, yaw
):
    """
    Вычисление локальных позиций точек опор в системе координат плеч.
    Точная копия C++ алгоритма:
    - R_legs = rotxyz(pi/2, -pi/2, 0)
    - T_blwbl = homog_transform(dx, dy, dz, roll, pitch, yaw)
    - T_leg[i] = T_blwbl * make_leg_T(tx, ty, tz) где make_leg_T = R_legs + translation

    :param leg_positions: Позиции ног (3x4 массив - как в C++: 3 координаты x 4 ноги)
    :return: Локальные позиции (3x4 массив - как в C++: 3 координаты x 4 ноги)
    """
    leg_positions = np.asarray(leg_positions)

    R_legs = rotxyz(np.pi / 2, -np.pi / 2, 0)

    T_blwbl = homog_transform(dx, dy, dz, roll, pitch, yaw)

    hl = 0.5 * body_length
    hw = 0.5 * body_width

    leg_offsets = [
        (hl, -hw, 0),  # FR
        (hl, hw, 0),  # FL
        (-hl, -hw, 0),  # RR
        (-hl, hw, 0),  # RL
    ]

    result = np.zeros((3, 4))

    for i in range(4):
        tx, ty, tz = leg_offsets[i]

        T_leg = np.eye(4)
        T_leg[:3, :3] = R_legs
        T_leg[0, 3] = tx
        T_leg[1, 3] = ty
        T_leg[2, 3] = tz

        T_leg_total = T_blwbl @ T_leg

        leg_pos_h = np.append(leg_positions[:, i], 1.0)
        inv_T = homog_transform_inverse(T_leg_total)
        pos_local = inv_T @ leg_pos_h
        result[:, i] = pos_local[:3]

    return result
