#!/usr/bin/env python3
"""
isaac_bridge.py — мост между Rust-контроллером (rclrs) и Isaac Sim.

Работает ВНУТРИ процесса Isaac Sim (нужен доступ к omni/isaacsim API).

Задача:
  1. Подписан на /joint_group_controller/commands (Float64MultiArray, 12 углов)
     от Rust-контроллера → применяет к articulation Go2 (position targets)
  2. Публикует /joint_states (sensor_msgs/JointState) — фактические углы
  3. Публикует /imu (sensor_msgs/Imu) — ориентация тела из позы робота
  4. Публикует /foot_contact (quadropted_msgs/RobotFootContact) — контакт лап

Порядок joint в командах (совпадает с robot_control.yaml и URDF):
    FR_hip, FR_thigh, FR_calf, FL_hip, FL_thigh, FL_calf,
    RR_hip, RR_thigh, RR_calf, RL_hip, RL_thigh, RL_calf

Запуск из venv Isaac Sim:
    source ~/isaacsim-venv/bin/activate
    python src/isaac/isaac_bridge.py [--headless] [--sim-rate 100] [--ns /robot1] [--debug]

Отладка: --debug (или env ISAAC_DEBUG=1) включает подробный вывод.
"""

import argparse
import os
import sys
import threading
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from isaac_debug import log, setup_debug, freq, require_memory  # noqa: E402

TAG = "bridge"

# --- ROS2 rclpy (встроенный Jazzy в Isaac Sim) -------------------------
# Пути к rclpy внутри venv Isaac Sim
ISAAC_ROS2 = os.path.expanduser(
    "~/isaacsim-venv/lib/python3.12/site-packages/isaacsim/exts/isaacsim.ros2.core/jazzy"
)

# Сбросить PYTHONPATH/AMENT_PREFIX_PATH от хост-ROS (Lyrical, py3.14) —
# иначе он перекрывает встроенный rclpy Isaac Sim (Jazzy, py3.12)
# и ломает типы (geometry_msgs .so conflict).
os.environ["PYTHONPATH"] = ""
os.environ.pop("AMENT_PREFIX_PATH", None)

# LD_LIBRARY_PATH: только библиотеки rclpy Isaac Sim
lib_paths = [f"{ISAAC_ROS2}/lib"]
existing = os.environ.get("LD_LIBRARY_PATH", "")
# Оставляем только системные пути (не /opt/ros/lyrical)
kept = [p for p in existing.split(":") if p and "/opt/ros/lyrical" not in p]
os.environ["LD_LIBRARY_PATH"] = ":".join(lib_paths + kept)

for p in (f"{ISAAC_ROS2}/rclpy", f"{ISAAC_ROS2}/lib"):
    if p not in sys.path:
        sys.path.insert(0, p)

# RMW = CycloneDDS (как в остальном стеке), domain 0.
# Без этого rclpy Isaac Sim не увидит топики Rust-контроллера.
os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")
os.environ.setdefault("ROS_DOMAIN_ID", "0")
os.environ.setdefault("CYCLONEDDS_URI", "file:///home/redalexdad/.cyclonedds.xml")

# Порядок управляемых joint (совпадает с robot_control.yaml)
JOINT_ORDER = [
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
]

# Имена лап [FR, FL, RR, RL] — порядок как в RobotFootContact.msg
FOOT_NAMES = ["FR_foot", "FL_foot", "RR_foot", "RL_foot"]


class IsaacBridge:
    """Мост Rust-контроллер ↔ Isaac Sim articulation."""

    def __init__(self, ns: str = "/robot1", rate: float = 100.0):
        import rclpy
        from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

        rclpy.init()
        self.node = rclpy.create_node(f"{ns.strip('/')}_isaac_bridge", namespace=ns)
        log.info(TAG, f"rclpy node created: ns={ns}, rate={rate}")

        # QoS RELIABLE — Rust-ноды (rclrs) используют RELIABLE по умолчанию.
        # BEST_EFFORT несовместим: подписчик RELIABLE не получает сообщения
        # от издателя BEST_EFFORT (Last incompatible policy: RELIABILITY).
        self.qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.qos_durable = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        # Подписка на команды от Rust-контроллера (12 углов)
        from std_msgs.msg import Float64MultiArray
        self.cmd_sub = self.node.create_subscription(
            Float64MultiArray, "joint_group_controller/commands", self.on_joint_command, self.qos
        )
        log.info(TAG, "Subscribed: joint_group_controller/commands")

        # Публикация фактических суставов
        from sensor_msgs.msg import JointState
        self.js_pub = self.node.create_publisher(JointState, "joint_states", self.qos)
        log.info(TAG, "Publisher: joint_states")

        # Публикация IMU
        from sensor_msgs.msg import Imu
        self.imu_pub = self.node.create_publisher(Imu, "imu", self.qos)
        log.info(TAG, "Publisher: imu")

        # Публикация foot_contact
        try:
            from quadropted_msgs.msg import RobotFootContact
            self.fc_pub = self.node.create_publisher(RobotFootContact, "foot_contact", self.qos)
            log.info(TAG, "Publisher: foot_contact (quadropted_msgs)")
        except ImportError as e:
            log.warn(TAG, f"quadropted_msgs not available: {e}; foot_contact disabled")
            self.fc_pub = None

        self.last_cmd = np.zeros(12, dtype=np.float64)
        self.cmd_time = 0.0
        self.rate = rate
        self.articulation = None

        # Контакты лап [FR, FL, RR, RL]
        self.contacts = np.zeros(4, dtype=bool)
        self._contact_sub = None

        # Счётчики команд (для отладки частоты)
        self.cmd_count = 0
        self.js_count = 0
        # Готовность: True после init-цикла (иначе команды игнорируются,
        # т.к. set_dof_position_targets на неинициализированных тензорах
        # может блокировать sim_app.update())
        self.ready = False

    # --- Isaac Sim интерфейс -------------------------------------------

    def attach(self, articulation):
        """Привязать articulation-обёртку Isaac Sim."""
        self.articulation = articulation
        try:
            names = articulation.joint_names
            log.info(TAG, f"Articulation attached. {len(names)} joint_names")
            log.debug(TAG, f"joint_names={names}")
            self.articulation_num_dofs = articulation.num_dofs
            log.debug(TAG, f"num_dofs={self.articulation_num_dofs}")
        except Exception as e:
            log.warn(TAG, f"could not read articulation info: {e}")

    def subscribe_contacts(self):
        """Подписка на отчёты о контактах PhysX.

        Лапы должны иметь PhysxContactReportAPI (см. main — включается
        при импорте). При каждом контакте сопоставляем актора с лапой
        и полом (GroundPlane).
        """
        try:
            from omni.physx import get_physx_simulation_interface
            iface = get_physx_simulation_interface()
            self._contact_sub = iface.subscribe_contact_report_events(self._on_contact_report)
            log.info(TAG, "Subscribed: PhysX contact report")
        except Exception as e:
            log.warn(TAG, f"could not subscribe contact report: {e}")

    def _on_contact_report(self, contact_headers, contact_data):
        """Обработка отчёта о контактах: помечаем лапы, касающиеся пола."""
        from pxr import PhysicsSchemaTools

        self.contacts[:] = False
        for header in contact_headers:
            # actor0/actor1 — int-индексы; преобразуем в SdfPath
            try:
                actor0 = str(PhysicsSchemaTools.intToSdfPath(header.actor0))
                actor1 = str(PhysicsSchemaTools.intToSdfPath(header.actor1))
            except Exception:
                continue
            for i, foot in enumerate(FOOT_NAMES):
                if foot in actor0 or foot in actor1:
                    self.contacts[i] = True
        log.debug(TAG, f"contacts={self.contacts.tolist()}")

    def publish_sensors(self):
        """Публикация IMU (из позы робота) и foot_contact."""
        if self.articulation is None:
            return
        try:
            pos, ori = self.articulation.get_world_poses(indices=[0])
            lin_vel, ang_vel = self.articulation.get_velocities(indices=[0])
            # quaternion из Isaac в wxyz, numpy → python
            q = np.array(ori[0], dtype=np.float64)   # (4,) wxyz
            p = np.array(pos[0], dtype=np.float64)   # (3,)
            av = np.array(ang_vel[0], dtype=np.float64)
            lv = np.array(lin_vel[0], dtype=np.float64)
            log.debug(TAG, f"pose pos={p.round(3)}, quat={q.round(3)}")
            log.debug(TAG, f"vel lin={lv.round(3)}, ang={av.round(3)}")
            # Ускорение аппроксимируем из скорости (по умолчанию 0)
            self.publish_imu(q, av, np.zeros(3))
        except Exception as e:
            log.warn(TAG, f"publish_sensors IMU error: {e}")
        # foot_contact
        if self.fc_pub is not None:
            self.publish_foot_contact(self.contacts)

    def on_joint_command(self, msg):
        """Применить 12 углов к articulation (position targets)."""
        if not self.ready:
            log.debug(TAG, "command пропущена: мост ещё не готов (init)")
            return
        if self.articulation is None:
            log.debug(TAG, "command пропущена: articulation не привязан")
            return
        data = np.array(msg.data, dtype=np.float64)
        if data.size != 12:
            log.warn(TAG, f"Expected 12 joints, got {data.size}")
            return
        self.last_cmd = data
        self.cmd_time = time.time()
        self.cmd_count += 1
        log.debug(TAG, f"command #{self.cmd_count}: {data.round(3)}")

    def apply_pending_command(self):
        """Применить последнюю команду к articulation.

        Вызывается из ОСНОВНОГО цикла (между шагами физики), НЕ из
        потока rclpy. PhysX запрещает setDriveTarget() из другого
        потока во время симуляции.
        """
        if self.articulation is None or not self.ready:
            return
        try:
            self.articulation.set_dof_position_targets(self.last_cmd.reshape(1, -1))
        except Exception as e:
            log.warn(TAG, f"set_dof_position_targets failed: {e}")

    def publish_joint_states(self, positions: np.ndarray):
        """Публикация фактических углов."""
        from sensor_msgs.msg import JointState
        js = JointState()
        now = self.node.get_clock().now()
        js.header.stamp = now.to_msg()
        js.header.frame_id = "base"
        js.name = list(JOINT_ORDER)
        js.position = positions.tolist()
        self.js_pub.publish(js)
        self.js_count += 1

    def publish_imu(self, orientation_wxyz, angular_velocity, linear_acceleration):
        """Публикация IMU из позы робота."""
        from sensor_msgs.msg import Imu
        imu = Imu()
        imu.header.stamp = self.node.get_clock().now().to_msg()
        imu.header.frame_id = "imu"
        # Isaac отдаёт quaternion в формате wxyz
        imu.orientation.w = float(orientation_wxyz[0])
        imu.orientation.x = float(orientation_wxyz[1])
        imu.orientation.y = float(orientation_wxyz[2])
        imu.orientation.z = float(orientation_wxyz[3])
        imu.angular_velocity.x = float(angular_velocity[0])
        imu.angular_velocity.y = float(angular_velocity[1])
        imu.angular_velocity.z = float(angular_velocity[2])
        imu.linear_acceleration.x = float(linear_acceleration[0])
        imu.linear_acceleration.y = float(linear_acceleration[1])
        imu.linear_acceleration.z = float(linear_acceleration[2])
        self.imu_pub.publish(imu)

    def publish_foot_contact(self, contacts: np.ndarray):
        """Публикация контактов лап [FR, FL, RR, RL]."""
        if self.fc_pub is None:
            return
        from quadropted_msgs.msg import RobotFootContact
        msg = RobotFootContact()
        msg.contacts = [bool(c) for c in contacts]
        self.fc_pub.publish(msg)

    def spin_ros(self):
        """Вращать rclpy в фоновом потоке.

        ExternalShutdownException бросается, когда контекст rclpy
        завершается извне — ловим и продолжаем, пока rclpy.ok().
        Без этого поток умирает и узел перестаёт обрабатывать топики.
        """
        import rclpy
        while rclpy.ok():
            try:
                rclpy.spin_once(self.node, timeout_sec=0.01)
            except rclpy.executors.ExternalShutdownException:
                continue
            except Exception as e:
                log.warn(TAG, f"spin_once error: {e}")
                break

    def run(self):
        """Запустить фоновый поток rclpy."""
        self.ros_thread = threading.Thread(target=self.spin_ros, daemon=True)
        self.ros_thread.start()


def build_ground_plane(stage):
    """Создать ground plane + свет + физический материал (общий код)."""
    from pxr import UsdGeom, UsdLux, UsdPhysics, UsdShade

    log.debug(TAG, "ground plane: свет")
    UsdLux.DistantLight.Define(stage, "/World/ground/Sun")

    log.debug(TAG, "ground plane: пол")
    ground = UsdGeom.Cube.Define(stage, "/World/ground/GroundPlane")
    ground.AddTranslateOp().Set((0, 0, -0.025))
    ground.AddScaleOp().Set((1000, 1000, 0.05))
    ground.CreateDisplayColorAttr([(0.2, 0.25, 0.3)])

    log.debug(TAG, "ground plane: коллизия (CollisionAPI + static RigidBody)")
    UsdPhysics.CollisionAPI.Apply(ground.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(ground.GetPrim())  # static (не физическое тело)
    UsdPhysics.RigidBodyAPI(ground.GetPrim()).CreateKinematicEnabledAttr(True)

    log.debug(TAG, "ground plane: материал")
    mat_path = "/World/ground/Looks/PhysicsMaterial"
    material = UsdShade.Material.Define(stage, mat_path)
    physics_mat = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    physics_mat.CreateStaticFrictionAttr().Set(1.0)
    physics_mat.CreateDynamicFrictionAttr().Set(1.0)
    physics_mat.CreateRestitutionAttr().Set(0.0)
    UsdShade.MaterialBindingAPI.Apply(ground.GetPrim()).Bind(material)
    log.info(TAG, "ground plane created")


def enable_foot_contacts(stage):
    """Включить PhysxContactReportAPI на лапах. Вернуть найденные лапы."""
    from pxr import PhysxSchema

    foot_prims = {}
    for prim in stage.Traverse():
        name = str(prim.GetName())
        if name in FOOT_NAMES:
            foot_prims[name] = prim
            PhysxSchema.PhysxContactReportAPI.Apply(prim)
            log.info(TAG, f"contact report enabled on {prim.GetPath()}")
    for foot in FOOT_NAMES:
        if foot not in foot_prims:
            log.warn(TAG, f"лапа не найдена: {foot}")
    log.debug(TAG, f"лап найдено: {len(foot_prims)}")
    return foot_prims


def find_articulation(stage):
    """Найти первый prim с ArticulationRootAPI."""
    from pxr import UsdPhysics

    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            log.debug(TAG, f"ArticulationRoot найден: {prim.GetPath()}")
            return str(prim.GetPath())
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Isaac Sim ↔ Rust controller bridge")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--ns", default="/robot1", help="ROS namespace")
    parser.add_argument("--sim-rate", type=float, default=100.0)
    parser.add_argument("--dt", type=float, default=0.005, help="physics dt")
    parser.add_argument("--debug", action="store_true",
                        help="enable verbose debug output (or env ISAAC_DEBUG=1)")
    args = parser.parse_args()
    setup_debug()
    if args.debug:
        log.set_level("debug")
    log.info(TAG, f"start: headless={args.headless}, ns={args.ns}, sim_rate={args.sim_rate}")

    # Защита от OOM: Isaac Sim требует ~11 GB RAM
    require_memory(12.0, tag=TAG)

    from isaacsim import SimulationApp
    sim_app = SimulationApp({"headless": args.headless, "width": 1280, "height": 720})
    log.info(TAG, f"Isaac Sim started (headless={args.headless})")

    # --- Импорт URDF + ground plane -----------------------------------
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    _sys = sys
    _sys.path.insert(0, os.path.join(project_root, "src", "isaac"))
    from load_go2 import GO2_URDF, GO2_DESC  # noqa: E402

    if not os.path.exists(GO2_URDF):
        log.error(TAG, f"URDF not found: {GO2_URDF}")
        sim_app.close()
        return 1

    import omni.usd
    from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig
    from isaacsim.core.experimental.prims import Articulation

    config = URDFImporterConfig()
    config.urdf_path = GO2_URDF
    config.fix_base = False
    config.merge_fixed_joints = False
    config.allow_self_collision = False
    config.ros_package_paths = [{"go2_description": GO2_DESC}]
    config.joint_target_type = "position"
    config.joint_drive_type = "force"
    config.override_joint_stiffness = 40.0
    config.override_joint_damping = 2.0

    log.debug(TAG, "импортируем URDF...")
    importer = URDFImporter(config)
    usd_path = importer.import_urdf()
    log.info(TAG, f"URDF imported → {usd_path}")

    # Явно открыть сгенерированный stage в контексте
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

    # Контакты лап
    enable_foot_contacts(stage)

    # Найти articulation
    art_path = find_articulation(stage)
    if art_path is None:
        log.error(TAG, "no ArticulationRoot found in stage")
        sim_app.close()
        return 1
    log.info(TAG, f"articulation found: {art_path}")

    bridge = IsaacBridge(ns=args.ns, rate=args.sim_rate)

    # Articulation
    articulation = Articulation(art_path)
    bridge.attach(articulation)

    # Запуск rclpy в фоне
    bridge.run()
    log.info(TAG, "bridge running. Ctrl+C to stop.")

    # Поднять робота над полом, иначе он проваливается сквозь ground plane
    try:
        articulation.set_world_poses(
            positions=np.array([[0.0, 0.0, 0.5]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
        )
        log.info(TAG, "robot positioned at z=0.5")
    except Exception as e:
        log.warn(TAG, f"set_world_poses failed: {e}")

    # Физический цикл
    import omni.timeline
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    log.info(TAG, "timeline.play() called")

    # Первые шаги для инициализации тензорных данных
    log.debug(TAG, "инициализация тензорных данных (30 шагов)...")
    for _ in range(30):
        sim_app.update()
    bridge.ready = True
    log.debug(TAG, "init done, entering main loop")

    # Подписка на контакты — ПОСЛЕ play (как в демо ContactReportDemo)
    bridge.subscribe_contacts()

    try:
        it = 0
        while sim_app.is_running():
            sim_app.update()
            it += 1
            freq.tick("loop")

            # Применить последнюю команду (из основного потока — PhysX
            # запрещает setDriveTarget из потока rclpy во время симуляции)
            bridge.apply_pending_command()

            # Чтение фактических углов
            try:
                pos = articulation.get_dof_positions()[0]  # warp-массив (N, D)
                bridge.publish_joint_states(np.array(pos, dtype=np.float64))
            except Exception as e:
                if it % 100 == 0:
                    log.warn(TAG, f"get_dof_positions error: {e}")

            # IMU + foot_contact
            bridge.publish_sensors()

            # Периодический отчёт о частотах (раз в ~2 сек)
            if it % 100 == 0:
                log.info(
                    TAG,
                    f"loop {freq.report('loop')}, js={bridge.js_count}, "
                    f"cmd={bridge.cmd_count}, imu_subs={bridge.imu_pub.get_subscription_count()}, "
                    f"js_subs={bridge.js_pub.get_subscription_count()}",
                )
    except KeyboardInterrupt:
        pass

    timeline.stop()
    sim_app.close()
    log.info(TAG, "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
