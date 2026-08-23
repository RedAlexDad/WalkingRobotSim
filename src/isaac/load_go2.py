#!/usr/bin/env python3
"""
load_go2.py — загрузка URDF робота Go2 в Isaac Sim.

Импортирует src/go2_description/urdf/go2_description.urdf через
URDFImporter, размещает робота над ground plane и включает физику.
Использует актуальный API Isaac Sim 6.0 (SimulationManager,
stage_utils) — устаревший isaacsim.core.api.world не используется.

Запуск из venv Isaac Sim (headless или GUI):
    source ~/isaacsim-venv/bin/activate
    python src/isaac/load_go2.py [--headless] [--usd OUT.usd] [--debug]

Отладка: --debug (или env ISAAC_DEBUG=1) включает подробный вывод.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from isaac_debug import log, setup_debug, require_memory  # noqa: E402

TAG = "load_go2"

# Корень проекта (для поиска URDF и meshes)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Используем xacro-URDF (как в Gazebo) — joint имена и лимиты совпадают
# с ros_control.yaml: rf/lf/rh/lh × hip/upper_leg/lower_leg.
# SolidWorks go2_description.urdf имеет ДРУГИЕ имена (FR_thigh_joint) и
# лимит calf [-2.72,-0.84], из-за чего робот падал в Isaac.
GO2_URDF = os.path.join(PROJECT_ROOT, "src", "go2_description", "urdf", "go2_gazebo.urdf")
GO2_DESC = os.path.join(PROJECT_ROOT, "src", "go2_description")

# 12 управляемых joint в порядке команд контроллера (совпадает с
# ros_control.yaml): rf=FR, lf=FL, rh=RR, lh=RL × (hip, upper_leg, lower_leg)
JOINT_ORDER = [
    "rf_hip_joint", "rf_upper_leg_joint", "rf_lower_leg_joint",
    "lf_hip_joint", "lf_upper_leg_joint", "lf_lower_leg_joint",
    "rh_hip_joint", "rh_upper_leg_joint", "rh_lower_leg_joint",
    "lh_hip_joint", "lh_upper_leg_joint", "lh_lower_leg_joint",
]


def build_ground_plane(stage):
    """Создать ground plane + свет + физический материал."""
    from pxr import UsdGeom, UsdLux, UsdPhysics, UsdShade

    log.debug(TAG, "ground plane: создаём свет")
    UsdLux.DistantLight.Define(stage, "/World/ground/Sun")

    log.debug(TAG, "ground plane: создаём пол")
    ground = UsdGeom.Cube.Define(stage, "/World/ground/GroundPlane")
    ground.AddTranslateOp().Set((0, 0, -0.025))
    ground.AddScaleOp().Set((1000, 1000, 0.05))
    ground.CreateDisplayColorAttr([(0.2, 0.25, 0.3)])

    log.debug(TAG, "ground plane: физический материал (трение=1.0)")
    mat_path = "/World/ground/Looks/PhysicsMaterial"
    material = UsdShade.Material.Define(stage, mat_path)
    physics_mat = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    physics_mat.CreateStaticFrictionAttr().Set(1.0)
    physics_mat.CreateDynamicFrictionAttr().Set(1.0)
    physics_mat.CreateRestitutionAttr().Set(0.0)
    UsdShade.MaterialBindingAPI.Apply(ground.GetPrim()).Bind(material)
    log.info(TAG, "ground plane created")


def find_articulation(stage):
    """Найти первый prim с ArticulationRootAPI. Вернуть путь или None."""
    from pxr import UsdPhysics

    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            log.debug(TAG, f"ArticulationRoot найден: {prim.GetPath()}")
            return str(prim.GetPath())
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Load Go2 URDF into Isaac Sim")
    parser.add_argument("--headless", action="store_true", help="run without GUI")
    parser.add_argument("--usd", default=None, help="save imported stage to .usd")
    parser.add_argument("--keep-open", action="store_true",
                        help="keep simulation running (physics loop), don't exit")
    parser.add_argument("--debug", action="store_true",
                        help="enable verbose debug output (or env ISAAC_DEBUG=1)")
    args = parser.parse_args()
    setup_debug()
    if args.debug:
        log.set_level("debug")
    log.info(TAG, f"start: headless={args.headless}, usd={args.usd}, keep_open={args.keep_open}")

    # Защита от OOM: Isaac Sim требует ~11 GB RAM
    require_memory(12.0, tag=TAG)

    from isaacsim import SimulationApp

    sim_app = SimulationApp({"headless": args.headless, "width": 1280, "height": 720})
    log.info(TAG, f"Isaac Sim started (headless={args.headless})")

    import omni.usd
    from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig

    if not os.path.exists(GO2_URDF):
        log.error(TAG, f"URDF not found: {GO2_URDF}")
        sim_app.close()
        return 1

    log.debug(TAG, f"URDF: {GO2_URDF}")
    log.debug(TAG, f"package: {GO2_DESC}")

    # Настроить импорт URDF
    config = URDFImporterConfig()
    config.urdf_path = GO2_URDF
    config.fix_base = False              # floating-base робот
    config.merge_fixed_joints = False
    config.allow_self_collision = False
    config.ros_package_paths = [{"go2_description": GO2_DESC}]
    config.joint_target_type = "position"   # управление позициями суставов
    config.joint_drive_type = "force"
    # Gains как в isaac_bridge (см. set_dof_gains): hip мягкие, upper/lower жёсткие
    config.override_joint_stiffness = 100.0
    config.override_joint_damping = 5.0
    # Отключаем multi-physics конверсию (перезаписывает drive stiffness)
    config.run_multi_physics_conversion = False
    config.run_asset_transformer = False

    log.debug(TAG, f"config: stiffness={config.override_joint_stiffness} "
                   f"damping={config.override_joint_damping} "
                   f"multi_physics={config.run_multi_physics_conversion}")
    log.debug(TAG, "импортируем URDF через URDFImporter...")
    importer = URDFImporter(config)
    usd_path = importer.import_urdf()
    log.info(TAG, f"URDF imported → {usd_path}")

    # Явно открыть stage (import_urdf не всегда делает это надёжно)
    log.debug(TAG, "открываем stage в контексте")
    ctx = omni.usd.get_context()
    ctx.open_stage(usd_path)
    for _ in range(20):
        sim_app.update()

    stage = ctx.get_stage()
    if stage is None:
        log.error(TAG, "stage == None после open_stage")
        sim_app.close()
        return 1

    # Ground plane
    build_ground_plane(stage)

    # Сохранить stage если запрошено
    if args.usd:
        log.debug(TAG, f"сохраняем stage → {args.usd}")
        stage.GetRootLayer().Export(args.usd)
        log.info(TAG, f"stage saved → {args.usd}")

    # Проверить articulation
    art_path = find_articulation(stage)
    if art_path is None:
        log.warn(TAG, "no ArticulationRoot found")
    else:
        log.info(TAG, f"articulation found: {art_path}")

    # Запустить физический цикл
    if args.keep_open:
        log.info(TAG, "starting physics loop (Ctrl+C to stop)")
        import omni.timeline
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        it = 0
        try:
            while sim_app.is_running():
                sim_app.update()
                it += 1
                if it % 60 == 0:
                    log.debug(TAG, f"physics loop tick {it}")
        except KeyboardInterrupt:
            pass
        timeline.stop()

    sim_app.close()
    log.info(TAG, "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
