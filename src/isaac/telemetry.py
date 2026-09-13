#!/usr/bin/env python3
"""Телеметрия IsaacLab: максимально полная запись состояния в CSV.

Модуль не зависит от Isaac Sim — принимает готовый obs-словарь и пишет
строку CSV со всеми величинами, нужными для анализа статьи (сравнение
RL и IK/TROT): кинематика корпуса, ориентация, скорости (мировые и
связанные), ускорения, команды скорости, позиции/контакты стоп, углы и
скорости суставов, оценка моментов, мощности и энергии, ошибки слежения,
флаги падения/насыщения/NaN.

Колонки CSV:
    step, sim_time, wall_utc,
    x, y, z,
    qw, qx, qy, qz,
    roll, pitch, yaw,
    vx, vy, vz,            мировые линейные скорости
    vx_b, vy_b, vz_b,      линейные скорости в связанной СК
    ax, ay, az,            ускорения (связанная СК, IMU)
    gx, gy, gz,            направление гравитации в связанной СК
    wx, wy, wz,            мировые угловые скорости
    vel_cmd_x, vel_cmd_y, vel_cmd_z,
    mode,
    fallen, hip_sat, nan_flag,
    foot_x0..3, foot_y0..3, foot_z0..3,   мировые позиции стоп
    contact0..3,
    q0..q11,               углы суставов
    dq0..dq11,             скорости суставов
    tau0..tau11,           оценка момента (kp*(cmd-q) - kd*dq)
    p0..p11,               мощность сустава (tau*dq)
    power_w, energy_j,     суммарная мощность и накопленная энергия
    err0..err11,           ошибка слежения (cmd - q)
    cmd0..cmd11            целевые углы суставов
"""

from __future__ import annotations

import csv
import math
import os
import time
from typing import Optional

JOINT_NAMES = [
    "FR_hip", "FR_thigh", "FR_calf",
    "FL_hip", "FL_thigh", "FL_calf",
    "RR_hip", "RR_thigh", "RR_calf",
    "RL_hip", "RL_thigh", "RL_calf",
]

_BASE_COLS = [
    "step", "sim_time", "wall_utc",
    "x", "y", "z",
    "qw", "qx", "qy", "qz",
    "roll", "pitch", "yaw",
    "vx", "vy", "vz",
    "vx_b", "vy_b", "vz_b",
    "ax", "ay", "az",
    "gx", "gy", "gz",
    "wx", "wy", "wz",
    "vel_cmd_x", "vel_cmd_y", "vel_cmd_z",
    "mode",
    "fallen", "hip_sat", "nan_flag",
]
_FOOT_POS_COLS = [f"foot_{ax}{i}" for i in range(4) for ax in ("x", "y", "z")]
_CONTACT_COLS = [f"contact{i}" for i in range(4)]
_Q_COLS = [f"q{i}" for i in range(12)]
_DQ_COLS = [f"dq{i}" for i in range(12)]
_TAU_COLS = [f"tau{i}" for i in range(12)]
_P_COLS = [f"p{i}" for i in range(12)]
_SUM_COLS = ["power_w", "energy_j"]
_ERR_COLS = [f"err{i}" for i in range(12)]
_CMD_COLS = [f"cmd{i}" for i in range(12)]
HEADER = (_BASE_COLS + _FOOT_POS_COLS + _CONTACT_COLS + _Q_COLS + _DQ_COLS
          + _TAU_COLS + _P_COLS + _SUM_COLS + _ERR_COLS + _CMD_COLS)

HIP_IDX = (0, 3, 6, 9)


def utc_iso() -> str:
    """Текущее время в ISO 8601 UTC (например, 2026-09-13T13:39:27.123Z)."""
    t = time.time()
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + f".{int((t % 1) * 1000):03d}Z"


def quat_to_rpy(qw: float, qx: float, qy: float, qz: float) -> tuple[float, float, float]:
    """Кватернион (w, x, y, z) → углы Эйлера (roll, pitch, yaw) в радианах."""
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2.0 * (qw * qy - qz * qx)
    pitch = math.copysign(math.pi / 2.0, sinp) if abs(sinp) >= 1.0 else math.asin(sinp)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return roll, pitch, yaw


_OBS_SPECS = [
    ("world_pos", 3), ("world_quat", 4), ("world_lin_vel", 3),
    ("world_ang_vel", 3), ("imu_body_lin_acc", 3),
    ("joint_pos", 12), ("joint_vel", 12),
]


def _snapshot(o: dict, cmd=None, foot_pos=None) -> list:
    """Один батч-перевод GPU→CPU всех величин (одна синхронизация).

    Возвращает плоский список: obs(40) + cmd(12) + foot_pos(12).
    """
    try:
        import torch
    except Exception:
        return None
    dev = None
    for k, _ in _OBS_SPECS:
        t = o.get(k)
        if t is not None:
            try:
                dev = t.device
                break
            except Exception:
                pass
    parts = []
    nan = float("nan")
    def _flat(vals, n):
        out = []
        for row in vals:
            if isinstance(row, (list, tuple)):
                out.extend(float(v) for v in row)
            else:
                out.append(float(row))
        return torch.tensor(out[:n], dtype=torch.float32)

    for k, n in _OBS_SPECS:
        t = o.get(k)
        try:
            if hasattr(t, "reshape"):
                parts.append(t.reshape(-1)[:n].float())
            else:
                parts.append(_flat(list(t), n))
        except Exception:
            parts.append(torch.full((n,), nan, device=dev) if dev is not None else torch.full((n,), nan))
    for t, n in ((cmd, 12), (foot_pos, 12)):
        try:
            if hasattr(t, "reshape"):
                parts.append(t.reshape(-1)[:n].float())
            else:
                parts.append(_flat(list(t), n))
        except Exception:
            parts.append(torch.full((n,), nan, device=dev) if dev is not None else torch.full((n,), nan))
    try:
        flat = torch.cat(parts)
        return flat.cpu().tolist()
    except Exception:
        return None


def _tensor_row(t, n: int) -> list[float]:
    """Первые n элементов тензора/списка → список float (NaN при ошибке)."""
    if t is None:
        return [float("nan")] * n
    try:
        flat = t.reshape(-1)
    except AttributeError:
        flat = t
    try:
        return [float(flat[i]) for i in range(min(n, len(flat)))]
    except Exception:
        return [float("nan")] * n


def _rot_body(qw, qx, qy, qz, vx, vy, vz):
    """Мировой вектор → связанная СК: v_b = R^T @ v_world."""
    r00 = 1 - 2 * (qy * qy + qz * qz); r01 = 2 * (qx * qy - qz * qw); r02 = 2 * (qx * qz + qy * qw)
    r10 = 2 * (qx * qy + qz * qw); r11 = 1 - 2 * (qx * qx + qz * qz); r12 = 2 * (qy * qz - qx * qw)
    r20 = 2 * (qx * qz - qy * qw); r21 = 2 * (qy * qz + qx * qw); r22 = 1 - 2 * (qx * qx + qy * qy)
    vbx = r00 * vx + r10 * vy + r20 * vz
    vby = r01 * vx + r11 * vy + r21 * vz
    vbz = r02 * vx + r12 * vy + r22 * vz
    return vbx, vby, vbz


def _safe(x, default=float("nan")):
    try:
        return float(x)
    except Exception:
        return default


class TelemetryLogger:
    """Пишет CSV с полной телеметрией корпуса, стоп и суставов."""

    def __init__(self, path: str, flush_every: int = 200):
        self.path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._fh = open(self.path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._fh)
        self._writer.writerow(HEADER)
        self._flush_every = max(1, int(flush_every))
        self._rows = 0
        self._t0 = time.time()
        self._energy = 0.0
        self._last_t = None
        print(f"[telemetry] пишу CSV: {self.path}", flush=True)

    def log(self, obs: dict, sim_time_sec: float, step: int, cmd=None,
            vel_cmd=None, mode: str = "", kp: float = None, kd: float = None,
            foot_pos=None) -> None:
        o = obs["obs"] if "obs" in obs else obs
        snap = _snapshot(o, cmd=cmd, foot_pos=foot_pos)
        if snap is None:
            return
        x, y, z = snap[0:3]
        qw, qx, qy, qz = snap[3:7]
        vx, vy, vz = snap[7:10]
        wx, wy, wz = snap[10:13]
        ax, ay, az = snap[13:16]
        q = snap[16:28]
        dq = snap[28:40]
        c = snap[40:52]
        fp = snap[52:64]
        roll, pitch, yaw = quat_to_rpy(qw, qx, qy, qz)

        vbx, vby, vbz = _rot_body(qw, qx, qy, qz, vx, vy, vz)
        gx, gy, gz = _rot_body(qw, qx, qy, qz, 0.0, 0.0, -1.0)
        vc = _tensor_row(vel_cmd, 3) if vel_cmd is not None else [float("nan")] * 3

        # моменты, мощности, ошибки
        if kp is not None and kd is not None:
            tau = [kp * (c[i] - q[i]) - kd * dq[i] for i in range(12)]
        else:
            tau = [float("nan")] * 12
        p = [tau[i] * dq[i] for i in range(12)]
        power = sum(p) if all(not math.isnan(v) for v in p) else float("nan")
        if self._last_t is not None and not math.isnan(power):
            self._energy += abs(power) * max(0.0, float(sim_time_sec) - self._last_t)
        self._last_t = float(sim_time_sec)
        err = [c[i] - q[i] for i in range(12)]

        # контакты по высоте стопы (fp из snapshot)
        contacts = [float("nan")] * 4
        for i in range(4):
            fz = fp[i * 3 + 2]
            contacts[i] = 1.0 if (not math.isnan(fz) and fz < 0.06) else 0.0

        # флаги
        nan_flag = 1 if any(math.isnan(v) for v in (x, y, z) + (qw, qx, qy, qz) + tuple(q)) else 0
        fallen = 1 if (not math.isnan(z) and z < 0.12) else 0
        hip_sat = 1 if any(abs(c[i]) > 0.29 for i in HIP_IDX) else 0

        row = (
            [int(step), float(sim_time_sec), utc_iso(),
             x, y, z,
             qw, qx, qy, qz,
             roll, pitch, yaw,
             vx, vy, vz,
             vbx, vby, vbz,
             ax, ay, az,
             gx, gy, gz,
             wx, wy, wz,
             vc[0], vc[1], vc[2], mode,
             fallen, hip_sat, nan_flag]
            + fp + contacts
            + q + dq + tau + p + [power, round(self._energy, 4)] + err + c
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
        print(f"[telemetry] закрыт: {self.path} ({self._rows} строк, {dt:.1f} с)", flush=True)


def default_telemetry_path(tag: Optional[str] = None) -> str:
    root = os.path.expanduser("~/GitHub/WalkingRobotSim/logs/isaac")
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = f"telemetry_{tag}_{ts}.csv" if tag else f"telemetry_{ts}.csv"
    return os.path.join(root, name)
