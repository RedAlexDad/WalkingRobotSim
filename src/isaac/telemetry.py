#!/usr/bin/env python3
"""Телеметрия IsaacLab: запись состояния робота в CSV.

Модуль не зависит от Isaac Sim — принимает уже готовый obs-словарь из
ManagerBasedEnv и пишет строку CSV. Используется лаунчером
``run_sim_telemetry.py`` и разбирается скриптом ``analyze_telemetry.py``.

Колонки CSV:
    step, sim_time,
    x, y, z,
    qw, qx, qy, qz,
    vx, vy, vz,
    wx, wy, wz,
    roll, pitch, yaw,
    q0..q11,        (углы суставов, порядок JOINT_NAMES)
    dq0..dq11,      (скорости суставов)
    cmd0..cmd11     (последняя поданная команда целевых углов)
"""

from __future__ import annotations

import csv
import math
import os
import time
from typing import Optional, Sequence

JOINT_NAMES = [
    "FR_hip", "FR_thigh", "FR_calf",
    "FL_hip", "FL_thigh", "FL_calf",
    "RR_hip", "RR_thigh", "RR_calf",
    "RL_hip", "RL_thigh", "RL_calf",
]

_BASE_COLS = [
    "step", "sim_time",
    "x", "y", "z",
    "qw", "qx", "qy", "qz",
    "vx", "vy", "vz",
    "wx", "wy", "wz",
    "roll", "pitch", "yaw",
]
_JOINT_COLS = [f"q{i}" for i in range(12)]
_JOINT_VEL_COLS = [f"dq{i}" for i in range(12)]
_CMD_COLS = [f"cmd{i}" for i in range(12)]
HEADER = _BASE_COLS + _JOINT_COLS + _JOINT_VEL_COLS + _CMD_COLS


def quat_to_rpy(qw: float, qx: float, qy: float, qz: float) -> tuple[float, float, float]:
    """Кватернион (w, x, y, z) → углы Эйлера (roll, pitch, yaw) в радианах."""
    # roll (x-axis rotation)
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2.0 * (qw * qy - qz * qx)
    if abs(sinp) >= 1.0:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def _tensor_row(t, n: int) -> list[float]:
    """Первые n элементов тензора (возможно, батч [1, n]) → список float."""
    if t is None:
        return [float("nan")] * n
    try:
        flat = t.reshape(-1)
    except AttributeError:
        flat = t
    return [float(flat[i]) for i in range(min(n, len(flat)))]


class TelemetryLogger:
    """Пишет CSV с телеметрией корпуса и суставов.

    Пример:
        tel = TelemetryLogger("/path/run.csv")
        tel.log(obs, sim_time_sec=0.5, step=100, cmd=env.action)
        tel.close()
    """

    def __init__(self, path: str, flush_every: int = 50):
        self.path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._fh = open(self.path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._fh)
        self._writer.writerow(HEADER)
        self._flush_every = max(1, int(flush_every))
        self._rows = 0
        self._t0 = time.time()
        print(f"[telemetry] пишу CSV: {self.path}", flush=True)

    def log(self, obs: dict, sim_time_sec: float, step: int, cmd=None) -> None:
        o = obs["obs"] if "obs" in obs else obs

        x, y, z = _tensor_row(o.get("world_pos"), 3)
        qw, qx, qy, qz = _tensor_row(o.get("world_quat"), 4)
        vx, vy, vz = _tensor_row(o.get("world_lin_vel"), 3)
        wx, wy, wz = _tensor_row(o.get("world_ang_vel"), 3)
        roll, pitch, yaw = quat_to_rpy(qw, qx, qy, qz)

        q = _tensor_row(o.get("joint_pos"), 12)
        dq = _tensor_row(o.get("joint_vel"), 12)
        c = _tensor_row(cmd, 12)

        row = (
            [int(step), float(sim_time_sec),
             x, y, z,
             qw, qx, qy, qz,
             vx, vy, vz,
             wx, wy, wz,
             roll, pitch, yaw]
            + q + dq + c
        )
        self._writer.writerow(row)
        self._rows += 1
        if self._rows % self._flush_every == 0:
            self._fh.flush()

    def close(self) -> None:
        try:
            self._fh.flush()
            self._fh.close()
        except Exception:
            pass
        dt = time.time() - self._t0
        print(
            f"[telemetry] закрыт: {self.path} "
            f"({self._rows} строк, {dt:.1f} с)",
            flush=True,
        )


def default_telemetry_path(tag: Optional[str] = None) -> str:
    """Путь по умолчанию: logs/isaac/telemetry_<tag>_<ts>.csv."""
    root = os.path.expanduser("~/GitHub/WalkingRobotSim/logs/isaac")
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = f"telemetry_{tag}_{ts}.csv" if tag else f"telemetry_{ts}.csv"
    return os.path.join(root, name)
