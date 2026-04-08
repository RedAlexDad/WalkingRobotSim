#!/usr/bin/env python3
"""
QuadrupedOdometry — пакет одометрии четвероногого робота.
Декомпозированная версия QuadrupedOdometryNode.py.
"""

from .node_config import NodeConfig, declare_parameters
from .node_main import MainLoop
from .node_publishers import MarkerPublisher, OdometryPublisher
from .node_subscriptions import SubscriptionCallbacks
from .odometry_state import OdometryState
from .odometry_update import normalize_angle, update_odometry

__all__ = [
    "OdometryState",
    "update_odometry",
    "normalize_angle",
    "NodeConfig",
    "declare_parameters",
    "SubscriptionCallbacks",
    "OdometryPublisher",
    "MarkerPublisher",
    "MainLoop",
]
