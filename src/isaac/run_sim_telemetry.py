#!/usr/bin/env python3
"""Лаунчер go2_isaac_ros2 (IsaacLab) с записью телеметрии в CSV.

Отличие от внешнего ``go2_isaac_ros2/main.py``: в главный цикл добавлена
запись состояния корпуса и суставов через ``telemetry.TelemetryLogger``.
Внешний пакет при этом не изменяется — модули ``go2_isaac_ros2.env`` и
``go2_isaac_ros2.ros`` берутся из ``PYTHONPATH`` (см. ``run_isaaclab.sh``).

Управление путём CSV:
    GO2_TELEMETRY_CSV  — полный путь к файлу (иначе путь по умолчанию)
    GO2_TELEMETRY_TAG  — метка в имени файла (например, ik или rl)
    GO2_TELEMETRY=0    — полностью отключить запись

Запуск:
    bash src/isaac/run_isaaclab.sh [--headless]
"""

# start Isaac Sim
print("Starting Isaac Sim")
from isaaclab.app import AppLauncher

app_launcher = AppLauncher()
simulation_app = app_launcher.app

import os
import sys

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
from go2_isaac_ros2.ros import Go2PubNode, Go2SubNode
import time
import signal

from telemetry import TelemetryLogger, default_telemetry_path


def _handler(sig, frame):
    print(f"[run_sim] got signal {sig} (игнорирую)", flush=True)


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
        print(f"[run_sim] telemetry init failed: {e}", flush=True)
        return None


def run_sim():
    # ROS2 bridge extension не включаем (может крашить Isaac Sim 6.0);
    # наш rclpy (Jazzy из Isaac Sim) подключается сам через sys.path.
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    print("[run_sim] timeline.play()")

    signal.signal(signal.SIGTERM, _handler)
    signal.signal(signal.SIGINT, _handler)
    print("[run_sim] create env cfg")
    env_cfg = UnitreeGo2CustomEnvCfg()
    print("[run_sim] create env")
    env = ManagerBasedEnv(env_cfg)
    print("[run_sim] wrap env")
    env = IsaacSimGo2EnvWrapper(env)
    print("[run_sim] env created, reset...")

    obs, _ = env.reset()
    print("[run_sim] reset OK")

    print("[run_sim] rclpy.init()...")
    rclpy.init()
    print("[run_sim] rclpy.init OK")
    go2_pub_node = Go2PubNode()
    print("[run_sim] Go2PubNode OK")
    go2_sub_node = Go2SubNode(env)
    print("[run_sim] Go2SubNode OK")
    go2_sub_node.start()

    tel = _make_logger()

    it = 0
    try:
        while True:
            try:
                if not timeline.is_playing():
                    timeline.play()
                start_time = time.time()
                obs, _ = env.step()
                sim_time_sec = timeline.get_current_time()
                go2_pub_node.publish(obs, sim_time_sec)
                it += 1

                if tel is not None:
                    try:
                        tel.log(obs, sim_time_sec, it, cmd=env.action)
                    except Exception as e:
                        print(f"[run_sim] telemetry log error: {e}", flush=True)

                if it % 50 == 0:
                    try:
                        pos = env._env.scene.articulations['robot'].data.root_pos_w
                        print(f"[run_sim] step {it}: sim_time={sim_time_sec:.2f} robot_pos=({pos[0,0]:.3f},{pos[0,1]:.3f},{pos[0,2]:.3f})", flush=True)
                    except Exception as e:
                        print(f"[run_sim] step {it}: sim_time={sim_time_sec:.2f} (pos err {e})", flush=True)

                sleep_time = env.dt - (time.time() - start_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except KeyboardInterrupt:
                print("[run_sim] keyboard interrupt", flush=True)
                break
            except Exception as e:
                print(f"[run_sim] main loop error: {e}", flush=True)
                break
    finally:
        if tel is not None:
            tel.close()
        print("[run_sim] main loop exited", flush=True)
        rclpy.shutdown()


if __name__ == "__main__":
    run_sim()
