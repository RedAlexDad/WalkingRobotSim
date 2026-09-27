"""Общие параметры MuJoCo-контура (без зависимости от ROS).

Здесь чистые константы и геометрия, чтобы их можно было тестировать без rclpy.
"""

from __future__ import annotations

import math

import numpy as np

# Порядок суставов MuJoCo = FL, FR, RL, RR × (hip, thigh, calf).
# Порядок контроллера/Isaac = FR, FL, RR, RL.
# CMD_TO_MJ[i]: индекс сустава команды -> индекс сустава MuJoCo.
CMD_TO_MJ = np.array([3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8])

# Стойка (в порядке MuJoCo FL, FR, RL, RR): hip ∓0.1, thigh 0.8/1.0, calf −1.5.
DEFAULT_MJ = np.array(
    [0.1, 0.8, -1.5, -0.1, 0.8, -1.5, 0.1, 1.0, -1.5, -0.1, 1.0, -1.5],
    dtype=np.float32,
)

KP, KD, LIMIT, VMAX = 50.0, 3.5, 23.5, 30.0


def _rpy(quat: np.ndarray) -> tuple[float, float, float]:
    """Кватернион (w,x,y,z) -> roll, pitch, yaw (рад)."""
    w, x, y, z = (float(v) for v in quat)
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


def pd_torque(target: np.ndarray, q: np.ndarray, dq: np.ndarray) -> np.ndarray:
    """Момент PD с конвертом DCMotor (как в эталонной политике Isaac Lab)."""
    tau = KP * (target - q) - KD * dq
    upper = np.clip(LIMIT * (1 - dq / VMAX), 0, LIMIT)
    lower = np.clip(LIMIT * (-1 - dq / VMAX), -LIMIT, 0)
    return np.asarray(np.clip(tau, lower, upper), dtype=np.float32)
