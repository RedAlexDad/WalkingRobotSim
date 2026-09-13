#!/usr/bin/env python3
"""Лаунчер go2_isaac_ros2 (IsaacLab) с записью телеметрии и усиленным логом.

Отличия от внешнего ``go2_isaac_ros2/main.py``:
  * запись состояния корпуса/суставов в CSV (``telemetry.TelemetryLogger``);
  * публикация IMU в ``/robot1/imu`` (``sensor_msgs/Imu``) — контроллер
    использует ориентацию для компенсации крена/тангажа; без неё робот
    заваливается;
  * подробный структурированный лог: REPORT раз в N шагов (поза, углы,
    ошибка суставов, команда), детекция NaN/Inf, смена команды.

Внешний пакет не изменяется — модули ``go2_isaac_ros2.*`` берутся из
``PYTHONPATH`` (см. ``run_isaaclab.sh``).

Переменные окружения:
    GO2_TELEMETRY_CSV  — путь к CSV (иначе путь по умолчанию)
    GO2_TELEMETRY_TAG  — метка в имени файла (ik | rl)
    GO2_TELEMETRY=0    — отключить запись
    GO2_IMU=0          — не публиковать IMU
    GO2_REPORT_EVERY   — период REPORT-строки в шагах (по умолчанию 50)

Запуск:
    bash src/isaac/run_isaaclab.sh [--headless]
"""

# start Isaac Sim
print("Starting Isaac Sim")
from isaaclab.app import AppLauncher

app_launcher = AppLauncher()
simulation_app = app_launcher.app

import math
import os
import signal
import sys
import threading
import time

# rclpy Isaac Sim (Jazzy) — добавляем после AppLauncher, чтобы не мешать старту
_JAZZY = os.path.expanduser(
    "~/isaacsim-venv/lib/python3.12/site-packages/isaacsim/exts/isaacsim.ros2.core/jazzy/rclpy"
)
if _JAZZY not in sys.path:
    sys.path.insert(0, _JAZZY)

# наш модуль telemetry.py лежит рядом с этим файлом
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import omni
from go2_isaac_ros2.env import UnitreeGo2CustomEnvCfg, IsaacSimGo2EnvWrapper
from isaaclab.envs import ManagerBasedEnv
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float64, Float64MultiArray
from go2_isaac_ros2.ros import Go2PubNode
from go2_cmd_sub import Go2CmdSubNode

from telemetry import TelemetryLogger, default_telemetry_path, quat_to_rpy

_T0 = time.time()


def _ts() -> str:
    t = time.time()
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + f".{int((t % 1) * 1000):03d}Z"


def log(tag: str, msg: str) -> None:
    print(f"[{_ts()}] [{tag}] {msg}", flush=True)


def _row(t, n):
    """Первые n элементов тензора/списка → список float (без NaN-падений)."""
    if t is None:
        return [float("nan")] * n
    try:
        flat = t.reshape(-1)
    except AttributeError:
        flat = t
    return [float(flat[i]) for i in range(min(n, len(flat)))]


class ImuBridge(Node):
    """Публикует ориентацию/скорости/ускорения из obs в /robot1/imu."""

    def __init__(self, topic: str = "/robot1/imu"):
        super().__init__("go2_imu_bridge")
        self.pub = self.create_publisher(Imu, topic, 10)
        self.topic = topic
        self.count = 0
        self.last = None

    def publish_obs(self, obs: dict) -> None:
        o = obs["obs"] if "obs" in obs else obs
        qw, qx, qy, qz = _row(o.get("world_quat"), 4)
        wx, wy, wz = _row(o.get("imu_body_ang_vel"), 3)
        ax, ay, az = _row(o.get("imu_body_lin_acc"), 3)

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base"
        msg.orientation.w = qw
        msg.orientation.x = qx
        msg.orientation.y = qy
        msg.orientation.z = qz
        msg.angular_velocity.x = wx
        msg.angular_velocity.y = wy
        msg.angular_velocity.z = wz
        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az
        self.pub.publish(msg)
        self.count += 1
        self.last = (qw, qx, qy, qz, wx, wy, wz)


class PushSubNode(Node):
    """Боковой толчок по топику /robot1/push (std_msgs/Float64, Н, ось Y).

    При получении сообщения применяет силу к базе в течение dur секунд
    (dur/dt шагов) — можно подать в любой момент (например, после TROT).
    """

    def __init__(self, dt: float, dur: float):
        super().__init__("go2_push_sub")
        self.dt = dt
        self.dur = dur
        self.force = 0.0
        self.pending_steps = 0
        self.logged = False
        self.sub = self.create_subscription(Float64, "/robot1/push", self._cb, 1)
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        from rclpy.executors import SingleThreadedExecutor
        ex = SingleThreadedExecutor()
        ex.add_node(self)
        try:
            while rclpy.ok():
                ex.spin_once(timeout_sec=0.01)
        except Exception:
            pass
        finally:
            ex.shutdown()

    def _cb(self, msg: Float64):
        self.force = float(msg.data)
        self.pending_steps = max(1, int(self.dur / self.dt))
        self.logged = False


class SimTimePub(Node):
    """Публикует сим-время на /robot1/sim_time (std_msgs/Float64).

    Позволяет Rust-контроллеру шагать по сим-времени, а не по wall-clock,
    что убирает зависимость результатов от fps/загрузки CPU.
    """

    def __init__(self, topic: str = "/robot1/sim_time"):
        super().__init__("go2_sim_time_pub")
        self.pub = self.create_publisher(Float64MultiArray, topic, 10)
        self.topic = topic

    def publish_t(self, t: float) -> None:
        m = Float64MultiArray()
        m.data = [float(t)]
        self.pub.publish(m)


def _has_nan(values) -> bool:
    for v in values:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return True
    return False


def _make_logger():
    if os.environ.get("GO2_TELEMETRY", "1") == "0":
        return None
    path = os.environ.get("GO2_TELEMETRY_CSV")
    if not path:
        tag = os.environ.get("GO2_TELEMETRY_TAG") or None
        path = default_telemetry_path(tag)
    try:
        return TelemetryLogger(path)
    except Exception as e:
        log("run_sim", f"telemetry init failed: {e}")
        return None


def run_sim():
    log("run_sim", f"старт: argv={sys.argv[1:]} pid={os.getpid()}")
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    log("run_sim", "timeline.play()")

    signal.signal(signal.SIGTERM, lambda s, f: log("run_sim", f"signal {s} (игнорирую)"))
    signal.signal(signal.SIGINT, lambda s, f: log("run_sim", f"signal {s} (игнорирую)"))

    log("run_sim", "create env cfg")
    env_cfg = UnitreeGo2CustomEnvCfg()
    log("run_sim", f"physics_dt={env_cfg.sim.dt} decimation={env_cfg.decimation} "
                   f"num_envs={env_cfg.scene.num_envs}")
    log("run_sim", "create env")
    env = ManagerBasedEnv(env_cfg)
    log("run_sim", "wrap env")
    env = IsaacSimGo2EnvWrapper(env)
    log("run_sim", f"env created: control dt={env.dt}")

    # индексы стоп (для логирования их мировых позиций) — best-effort
    foot_ids = None
    try:
        _robot = env._env.scene.articulations['robot']
        _names = list(_robot.data.body_names)
        _fid = [i for i, n in enumerate(_names) if 'foot' in n.lower()]
        log("run_sim", f"body_names={_names}")
        if len(_fid) == 4:
            foot_ids = _fid
        log("run_sim", f"foot_ids={foot_ids}")
    except Exception as e:
        log("run_sim", f"foot_ids error: {e}")

    obs, _ = env.reset()
    log("run_sim", "reset OK")

    rclpy.init()
    log("run_sim", "rclpy.init OK")
    go2_pub_node = Go2PubNode()
    go2_sub_node = Go2CmdSubNode(env)
    go2_sub_node.start()
    log("run_sim", "ROS-узлы созданы: pub(/clock) + sub(joint commands), spin запущен")

    imu_bridge = None
    if os.environ.get("GO2_IMU", "1") != "0":
        imu_bridge = ImuBridge()
        log("run_sim", f"IMU bridge: публикую {imu_bridge.topic} (sensor_msgs/Imu)")
    else:
        log("run_sim", "IMU bridge ОТКЛЮЧЁН (GO2_IMU=0)")

    sim_time_pub = SimTimePub()
    log("run_sim", "SimTime: /robot1/sim_time (std_msgs/Float64)")

    tel = _make_logger()

    report_every = int(os.environ.get("GO2_REPORT_EVERY", "50"))
    push_dur = float(os.environ.get("GO2_PUSH_DUR", "0.2") or 0.2)
    dt = env.dt
    # параметры для оценки момента и команды скорости
    joint_kp = float(os.environ.get("GO2_KP", "75") or 75)
    joint_kd = float(os.environ.get("GO2_KD", "0.5") or 0.5)
    _vc = (os.environ.get("GO2_VEL_CMD", "") or "").split()
    vel_cmd = [float(v) for v in _vc] if len(_vc) == 3 else None
    mode = os.environ.get("GO2_MODE", "ik")
    # Целевой fps (wall) для свипа: 0 = без ограничения (только dt)
    target_fps = float(os.environ.get("GO2_TARGET_FPS", "0") or 0)
    target_dt = (1.0 / target_fps) if target_fps > 0 else dt
    push_node = None
    if os.environ.get("GO2_PUSH", "1") != "0":
        push_node = PushSubNode(dt, push_dur)
        log("run_sim", "Push: /robot1/push (std_msgs/Float64, Н, ось Y)")
    it = 0
    last_cmd = None
    nan_reported = 0
    t_wall0 = time.time()

    try:
        while True:
            try:
                if not timeline.is_playing():
                    timeline.play()
                start_time = time.time()
                # внешний боковой толчок (по топику /robot1/push)
                if push_node is not None and push_node.pending_steps > 0:
                    try:
                        robot = env._env.scene.articulations['robot']
                        import torch
                        f = torch.zeros((1, robot.num_bodies, 3), device=robot.device)
                        f[0, 0, 1] = push_node.force
                        robot.set_external_force_and_torque(f, torch.zeros_like(f), body_ids=[0])
                        if not push_node.logged:
                            log("SIM", f"PUSH force={push_node.force}N (y), "
                                       f"{push_node.pending_steps} шагов")
                            push_node.logged = True
                        push_node.pending_steps -= 1
                    except Exception as e:
                        log("SIM", f"push error: {e}")
                obs, _ = env.step()
                it += 1
                sim_time = it * dt  # надёжное время: шаг * dt (timeline врёт)
                go2_pub_node.publish(obs, sim_time)
                sim_time_pub.publish_t(sim_time)

                if imu_bridge is not None:
                    try:
                        imu_bridge.publish_obs(obs)
                    except Exception as e:
                        log("imu", f"publish error: {e}")

                cmd = env.action
                if tel is not None:
                    try:
                        foot_pos = None
                        if foot_ids is not None:
                            try:
                                foot_pos = env._env.scene.articulations['robot'].data.body_pos_w[0][foot_ids]
                            except Exception:
                                foot_pos = None
                        tel.log(obs, sim_time, it, cmd=cmd, vel_cmd=vel_cmd,
                                mode=mode, kp=joint_kp, kd=joint_kd, foot_pos=foot_pos)
                    except Exception as e:
                        log("tel", f"log error: {e}")

                # детекция NaN/Inf
                o = obs["obs"] if "obs" in obs else obs
                pos = _row(o.get("world_pos"), 3)
                quat = _row(o.get("world_quat"), 4)
                q = _row(o.get("joint_pos"), 12)
                if _has_nan(pos + quat + q):
                    nan_reported += 1
                    if nan_reported <= 5:
                        log("NaN", f"step={it} pos={pos} quat={quat} q={q[:6]}...")

                # смена команды
                c = _row(cmd, 12)
                if last_cmd is None or max(abs(c[i] - last_cmd[i]) for i in range(12)) > 0.01:
                    log("SIM", f"CMD CHANGE step={it} cmd={[round(v, 3) for v in c]}")
                    last_cmd = c

                # периодический REPORT
                if it % report_every == 0:
                    from telemetry import quat_to_rpy
                    roll, pitch, yaw = quat_to_rpy(*quat)
                    qa = _row(o.get("joint_pos"), 12)
                    err = [abs(c[i] - qa[i]) for i in range(12)]
                    fps = it / max(1e-6, (time.time() - t_wall0))
                    log(
                        "SIM",
                        f"REPORT step={it} t={sim_time:.2f} "
                        f"pos=({pos[0]:+.3f},{pos[1]:+.3f},{pos[2]:+.3f}) "
                        f"rpy=({math.degrees(roll):+.1f},{math.degrees(pitch):+.1f},"
                        f"{math.degrees(yaw):+.1f})° "
                        f"joint_err max={max(err):.3f} mean={sum(err)/12:.3f} "
                        f"fps={fps:.0f} imu={'on' if imu_bridge else 'off'}"
                        f"(n={imu_bridge.count if imu_bridge else 0})",
                    )

                sleep_time = target_dt - (time.time() - start_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except KeyboardInterrupt:
                log("run_sim", "keyboard interrupt")
                break
            except Exception as e:
                log("run_sim", f"main loop error: {e}")
                break
    finally:
        if tel is not None:
            tel.close()
        log("run_sim", f"main loop exited (steps={it})")
        rclpy.shutdown()


if __name__ == "__main__":
    run_sim()
