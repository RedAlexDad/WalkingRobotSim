#!/usr/bin/env python3
"""
QuadrupedOdometry — пакет одометрии четвероногого робота.
Декомпозированная версия QuadrupedOdometryNode.py.
"""

from .odometry_state import OdometryState
from .odometry_update import update_odometry, normalize_angle

__all__ = ["OdometryState", "update_odometry", "normalize_angle"]
