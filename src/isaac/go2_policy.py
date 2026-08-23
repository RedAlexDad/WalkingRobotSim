#!/usr/bin/env python3
"""go2_policy.py — автономный запуск Go2 с готовой обученной политикой NVIDIA.

Использует встроенный в Isaac Sim ассет (Mujoco_Menagerie go2.usda) и
обученную политику (physx_policy.pt). Управление — команды скорости
(vx, vy, wz) через клавиатуру или stdin:

  WASD / стрелки            — движение (как в Isaac Lab)
  N / M (или numpad 7/9)    — поворот
  Space                     — остановка (команда 0,0,0)
  Q                         — выход

Также команду можно подавать через stdin: три числа (vx vy wz), строка.

Физика 200 Гц (dt=0.005), как при обучении политики. Робот спавнится на
высоте 0.5 м и падает на землю, политика стабилизирует стойку.
"""

import argparse
import os
import sys
import threading

import numpy as np

# --- Логирование через isaac_debug (как в isaac_bridge) ---
from isaac_debug import log, setup_debug

TAG = "go2_policy"

# Локальный корень ассетов: сначала в проекте (src/isaac/assets/Isaac),
# fallback — ~/isaac_assets/Isaac (скачаны вручную, S3 нестабилен).
_PROJECT_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Isaac")
_HOME_ASSETS = os.path.expanduser("~/isaac_assets/Isaac")
LOCAL_ASSET_ROOT = _PROJECT_ASSETS if os.path.isdir(_PROJECT_ASSETS) else _HOME_ASSETS
GO2_USD = f"file://{LOCAL_ASSET_ROOT}/Samples/Mujoco_Menagerie/unitree_go2/go2/go2.usda"
POLICY_DIR = f"{LOCAL_ASSET_ROOT}/Samples/Policies/go2"
POLICY_PATH = f"{POLICY_DIR}/physx_policy.pt"
ENV_CONFIG_PATH = f"{POLICY_DIR}/physx_env.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Go2 policy demo (NVIDIA trained policy)")
    parser.add_argument("--headless", action="store_true", help="run without GUI")
    parser.add_argument("--ns", default="/robot1", help="ROS namespace (зарезервировано)")
    parser.add_argument("--min-ram", type=float, default=12.0, help="минимальная RAM (ГБ)")
    parser.add_argument("--debug", action="store_true", help="verbose debug output")
    args = parser.parse_args()

    setup_debug()
    if args.debug or os.environ.get("ISAAC_DEBUG") == "1":
        log.set_level("debug")
    log.info(TAG, f"start: headless={args.headless}")

    from isaac_debug import require_memory
    require_memory(args.min_ram, tag=TAG)

    # --- SimulationApp (должен быть ДО import остальных модулей isaacsim) ---
    from isaacsim import SimulationApp

    sim_app = SimulationApp(
        {
            "headless": args.headless,
            "width": 1280,
            "height": 720,
        }
    )
    log.info(TAG, f"Isaac Sim started (headless={args.headless})")

    import omni
    import omni.appwindow
    import carb
    from pxr import UsdGeom, UsdPhysics, UsdShade

    from isaacsim.core.simulation_manager import SimulationManager
    from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents
    from isaacsim.robot.policy.examples.robots import Go2FlatTerrainPolicy

    # Указываем ЛОКАЛЬНЫЙ asset_root (S3 в нашей сети нестабилен).
    # get_assets_root_path() проверяет наличие /Isaac И /NVIDIA — обе папки
    # создаём. Проверка через omni.client.stat(file://...) вернёт OK.
    LOCAL_ROOT = os.path.dirname(LOCAL_ASSET_ROOT)
    os.makedirs(f"{LOCAL_ROOT}/NVIDIA", exist_ok=True)
    os.makedirs(f"{LOCAL_ROOT}/Isaac", exist_ok=True)
    carb.settings.get_settings().set(
        "/persistent/isaac/asset_root/default", f"file://{LOCAL_ROOT}"
    )
    log.info(TAG, f"asset_root → file://{LOCAL_ROOT}")

    # Проверка локальных ассетов
    for p in (GO2_USD, POLICY_PATH, ENV_CONFIG_PATH):
        p_local = p.replace("file://", "")
        if not os.path.exists(p_local):
            log.error(TAG, f"отсутствует ассет: {p_local} (скачайте с S3 Isaac Sim 6.0)")
            sim_app.close()
            return 1
    log.debug(TAG, f"go2.usda: {GO2_USD}")
    log.debug(TAG, f"policy: {POLICY_PATH}")
    log.debug(TAG, f"env: {ENV_CONFIG_PATH}")

    # Физика 200 Гц (как при обучении политики), GPU dynamics
    SimulationManager.set_backend("torch")
    SimulationManager.set_physics_sim_device("cuda")
    SimulationManager.set_physics_dt(0.005)
    log.info(TAG, "physics: dt=0.005 (200 Hz), device=cuda, backend=torch")

    # --- Ground plane из локального default_environment.usd (правильный
    # CollisionPlane, как в примерах NVIDIA). Программный Cube не даёт
    # коллизии — робот проваливался сквозь пол.
    import isaacsim.core.experimental.utils.stage as stage_utils

    GROUND_USD = f"file://{LOCAL_ASSET_ROOT}/Environments/Grid/default_environment.usd"
    if not os.path.exists(GROUND_USD.replace("file://", "")):
        log.error(TAG, f"отсутствует ground: {GROUND_USD}")
        sim_app.close()
        return 1
    log.info(TAG, "add ground plane reference...")
    stage_utils.add_reference_to_stage(usd_path=GROUND_USD, path="/World")
    for _ in range(10):
        sim_app.update()
    log.info(TAG, "ground plane added")

    # Создание робота Go2 из локального USD.
    # СНАЧАЛА загружаем reference в stage (prim становится валидным), потом
    # Go2FlatTerrainPolicy находит его и не пересоздаёт (иначе define_prim+
    # AddReference не успевают до создания Articulation → resolve_paths(None)).
    log.info(TAG, "add reference to stage...")
    stage_utils.add_reference_to_stage(
        usd_path=GO2_USD,
        path="/World/Go2",
        variants=[("Physics", "physx")],
    )
    for _ in range(20):
        sim_app.update()
    log.info(TAG, "reference loaded")

    # Диагностика иерархии prim'ов под /World/Go2
    from pxr import UsdPhysics as _UsdPhysics
    stage = omni.usd.get_context().get_stage()
    root = stage.GetPrimAtPath("/World/Go2")
    if root.IsValid():
        from pxr import Usd
        for prim in Usd.PrimRange(root):
            has_api = prim.HasAPI(_UsdPhysics.ArticulationRootAPI)
            marker = " <== ARTICULATION_ROOT" if has_api else ""
            log.debug(TAG, f"prim: {prim.GetPath()}{marker}")
    else:
        log.error(TAG, "/World/Go2 prim НЕ валиден")

    log.info(TAG, "creating Go2FlatTerrainPolicy...")
    go2 = Go2FlatTerrainPolicy(
        prim_path="/World/Go2",
        position=[0, 0, 0.5],
        policy_path=POLICY_PATH,
        env_config_path=ENV_CONFIG_PATH,
    )
    log.info(TAG, f"Go2 created: num_dofs={go2.robot.num_dofs}")
    log.info(TAG, f"dof_names={go2.robot.dof_names}")

    # --- Управление: клавиатура + stdin ---
    command = [0.0, 0.0, 0.0]  # vx, vy, wz
    lock = threading.Lock()
    running = [True]

    key_map = {
        "W": [0.5, 0.0, 0.0], "UP": [0.5, 0.0, 0.0],
        "S": [-0.5, 0.0, 0.0], "DOWN": [-0.5, 0.0, 0.0],
        "A": [0.0, 0.5, 0.0], "LEFT": [0.0, 0.5, 0.0],
        "D": [0.0, -0.5, 0.0], "RIGHT": [0.0, -0.5, 0.0],
        "N": [0.0, 0.0, 0.5], "NUMPAD_7": [0.0, 0.0, 0.5],
        "M": [0.0, 0.0, -0.5], "NUMPAD_9": [0.0, 0.0, -0.5],
        "SPACE": [0.0, 0.0, 0.0],
    }

    def on_keyboard(event, *a, **kw):
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            name = event.input.name
            if name == "Q":
                with lock:
                    running[0] = False
            elif name in key_map:
                with lock:
                    command[:] = key_map[name]
                log.info(TAG, f"key {name}: cmd={command}")

    if not args.headless:
        try:
            appwindow = omni.appwindow.get_default_app_window()
            input_iface = carb.input.acquire_input_interface()
            keyboard = appwindow.get_keyboard()
            input_iface.subscribe_to_keyboard_events(keyboard, on_keyboard)
            log.info(TAG, "keyboard: WASD/стрелки — движение, N/M — поворот, Space — стоп, Q — выход")
        except Exception as e:
            log.warn(TAG, f"keyboard init failed: {e}")

    def stdin_reader():
        log.info(TAG, "stdin: подавайте команды 'vx vy wz' (например '0.5 0 0') или 'q'")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            if line.lower() in ("q", "quit", "exit"):
                with lock:
                    running[0] = False
                break
            try:
                parts = [float(x) for x in line.replace(",", " ").split()]
                if len(parts) != 3:
                    log.warn(TAG, f"ожидалось 3 числа (vx vy wz), получено: {line!r}")
                    continue
                with lock:
                    command[:] = parts
                log.info(TAG, f"stdin cmd: {command}")
            except ValueError:
                log.warn(TAG, f"не распознано: {line!r}")

    t = threading.Thread(target=stdin_reader, daemon=True)
    t.start()

    # --- Физика: каллибровка робота на первом шаге, затем policy ---
    from isaacsim.core.experimental.prims import Articulation

    physics_ready = False
    timestep = 0

    def on_physics_step(dt, context):
        nonlocal physics_ready, timestep
        if not running[0]:
            return
        if physics_ready:
            with lock:
                cmd = list(command)
            import torch
            cmd_t = torch.tensor(cmd, dtype=torch.float32, device="cuda")
            go2.forward(dt, cmd_t)
        else:
            physics_ready = True
            go2.initialize()
            go2.post_reset()
            log.info(TAG, "policy initialized, robot standing")

    cb_id = SimulationManager.register_callback(on_physics_step, IsaacEvents.POST_PHYSICS_STEP)

    # Запуск симуляции
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    log.info(TAG, "simulation started")

    # --- Цикл: обновление + периодический отчёт позы ---
    it = 0
    try:
        while sim_app.is_running() and running[0]:
            sim_app.update()
            it += 1
            if it % 200 == 0 and not args.headless:
                try:
                    pos, ori = go2.robot.get_world_poses()
                    p = pos.numpy()[0] if hasattr(pos, "numpy") else np.array(pos)[0]
                    log.info(TAG, f"[REPORT] pos=({p[0]:+.2f},{p[1]:+.2f},{p[2]:+.2f}) cmd={command}")
                except Exception as e:
                    log.warn(TAG, f"pose report error: {e}")
    except KeyboardInterrupt:
        pass

    SimulationManager.deregister_callback(cb_id)
    timeline.stop()
    sim_app.close()
    log.info(TAG, "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
