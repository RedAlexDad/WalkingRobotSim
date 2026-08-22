#!/usr/bin/env python3
"""
load_go2.py — загрузка URDF робота Go2 в Isaac Sim.

Импортирует src/go2_description/urdf/go2_description.urdf через
URDFImporter, размещает робота над ground plane и включает физику.
Использует актуальный API Isaac Sim 6.0 (SimulationManager,
stage_utils) — устаревший isaacsim.core.api.world не используется.

Запуск из venv Isaac Sim (headless или GUI):
    source ~/isaacsim-venv/bin/activate
    python src/isaac/load_go2.py [--headless] [--usd OUT.usd]

После импорта робот доступен как articulation prim:
    /go2_description/Physics  (ArticulationRoot)
    DOF joint: FR_hip_joint, FR_thigh_joint, FR_calf_joint, FL_*, RR_*, RL_*
"""

import argparse
import os
import sys

# Корень проекта (для поиска URDF и meshes)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GO2_URDF = os.path.join(PROJECT_ROOT, "src", "go2_description", "urdf", "go2_description.urdf")
GO2_DESC = os.path.join(PROJECT_ROOT, "src", "go2_description")

# Путь articulation после импорта: корневой prim — /go2_description
# (Xform с variantSet Physics; ArticulationRoot API на этом prim)
ARTICULATION_PRIM = "/go2_description"

# 12 управляемых joint в порядке команд контроллера (совпадает с
# robot_control.yaml): FR, FL, RR, RL × (hip, thigh, calf)
JOINT_ORDER = [
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Load Go2 URDF into Isaac Sim")
    parser.add_argument("--headless", action="store_true", help="run without GUI")
    parser.add_argument("--usd", default=None, help="save imported stage to .usd")
    parser.add_argument("--keep-open", action="store_true",
                        help="keep simulation running (physics loop), don't exit")
    args = parser.parse_args()

    from isaacsim import SimulationApp

    sim_app = SimulationApp({"headless": args.headless, "width": 1280, "height": 720})
    print(f"[load_go2] Isaac Sim started (headless={args.headless})", flush=True)

    import omni.usd
    from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig

    if not os.path.exists(GO2_URDF):
        print(f"[load_go2] ERROR: URDF not found: {GO2_URDF}", flush=True)
        sim_app.close()
        return 1

    # Настроить импорт URDF
    config = URDFImporterConfig()
    config.urdf_path = GO2_URDF
    config.fix_base = False              # floating-base робот
    config.merge_fixed_joints = False
    config.allow_self_collision = False
    config.ros_package_paths = [{"go2_description": GO2_DESC}]
    config.joint_target_type = "position"   # управление позициями суставов
    config.joint_drive_type = "force"
    config.override_joint_stiffness = 40.0
    config.override_joint_damping = 2.0

    importer = URDFImporter(config)
    usd_path = importer.import_urdf()
    print(f"[load_go2] URDF imported → {usd_path}", flush=True)

    # Ground plane через USD API (не требует ассетов Isaac)
    from pxr import Sdf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade

    stage = omni.usd.get_context().get_stage()

    # Простое солнце (направленный свет), иначе сцена тёмная
    UsdLux.DistantLight.Define(stage, "/World/ground/Sun")

    # Плоскость-пол
    ground = UsdGeom.Cube.Define(stage, "/World/ground/GroundPlane")
    ground.AddTranslateOp().Set((0, 0, -0.025))
    ground.AddScaleOp().Set((1000, 1000, 0.05))
    ground.CreateDisplayColorAttr([(0.2, 0.25, 0.3)])

    # Физический материал пола (трение)
    mat_path = "/World/ground/Looks/PhysicsMaterial"
    material = UsdShade.Material.Define(stage, mat_path)
    physics_mat = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    physics_mat.CreateStaticFrictionAttr().Set(1.0)
    physics_mat.CreateDynamicFrictionAttr().Set(1.0)
    physics_mat.CreateRestitutionAttr().Set(0.0)
    UsdShade.MaterialBindingAPI.Apply(ground.GetPrim()).Bind(material)
    print("[load_go2] ground plane created", flush=True)

    # Сохранить stage если запрошено
    if args.usd:
        stage = omni.usd.get_context().get_stage()
        stage.GetRootLayer().Export(args.usd)
        print(f"[load_go2] stage saved → {args.usd}", flush=True)

    # Проверить, что articulation присутствует
    from pxr import Usd, UsdPhysics
    stage = omni.usd.get_context().get_stage()
    found = False
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            print(f"[load_go2] articulation found: {prim.GetPath()}", flush=True)
            found = True
    if not found:
        print("[load_go2] WARNING: no ArticulationRoot found", flush=True)

    # Запустить физический цикл
    if args.keep_open:
        print("[load_go2] starting physics loop (Ctrl+C to stop)", flush=True)
        import omni.timeline
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        try:
            while sim_app.is_running():
                sim_app.update()
        except KeyboardInterrupt:
            pass
        timeline.stop()

    sim_app.close()
    print("[load_go2] done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
