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
    python src/isaac/isaac_bridge.py [--headless] [--sim-rate 100] [--ns /robot1]

Зависит от:
    - rclpy (встроенный Jazzy в Isaac Sim, py3.12)
    - quadropted_msgs (сгенерированные типы для RobotFootContact)
"""

import argparse
import os
import sys
import threading
import time

import numpy as np

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

ROBOT_PRIM = "/World/Go2"
# Путь articulation после импорта URDF: корневой prim /go2_description
# (Xform с variantSet Physics; ArticulationRoot API на этом prim)
ARTICULATION_PRIM = "/go2_description"

# Имена DOF после импорта (URDF → USD): обычно совпадают с joint именами
DOF_PREFIX = "dof_"  # Isaac добавляет префикс dof_ к DOF именам? Проверить


class IsaacBridge:
    """Мост Rust-контроллер ↔ Isaac Sim articulation."""

    def __init__(self, ns: str = "/robot1", rate: float = 100.0):
        import rclpy
        from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

        rclpy.init()
        self.node = rclpy.create_node(f"{ns.strip('/')}_isaac_bridge", namespace=ns)
        self.node.get_logger().info(f"IsaacBridge: namespace={ns}, rate={rate}")

        # QoS как в C++ (BEST_EFFORT depth 10) — совместимость с Rust-нодами
        self.qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.qos_durable = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        # Подписка на команды от Rust-контроллера (12 углов)
        from std_msgs.msg import Float64MultiArray
        self.cmd_sub = self.node.create_subscription(
            Float64MultiArray, "joint_group_controller/commands", self.on_joint_command, self.qos
        )
        self.node.get_logger().info("Subscribed: joint_group_controller/commands")

        # Публикация фактических суставов
        from sensor_msgs.msg import JointState
        self.js_pub = self.node.create_publisher(JointState, "joint_states", self.qos)
        self.node.get_logger().info("Publisher: joint_states")

        # Публикация IMU
        from sensor_msgs.msg import Imu
        self.imu_pub = self.node.create_publisher(Imu, "imu", self.qos)
        self.node.get_logger().info("Publisher: imu")

        # Публикация foot_contact
        try:
            from quadropted_msgs.msg import RobotFootContact
            self.fc_pub = self.node.create_publisher(RobotFootContact, "foot_contact", self.qos)
            self.node.get_logger().info("Publisher: foot_contact (quadropted_msgs)")
        except ImportError as e:
            self.node.get_logger().warn(f"quadropted_msgs not available: {e}; foot_contact disabled")
            self.fc_pub = None

        self.last_cmd = np.zeros(12, dtype=np.float64)
        self.cmd_time = 0.0
        self.rate = rate
        self.articulation = None

    # --- Isaac Sim интерфейс -------------------------------------------

    def attach(self, articulation):
        """Привязать articulation-обёртку Isaac Sim."""
        self.articulation = articulation
        try:
            names = articulation.joint_names
            self.node.get_logger().info(f"Articulation attached. joint_names={names}")
        except Exception as e:
            self.node.get_logger().warn(f"could not read joint_names: {e}")

    def on_joint_command(self, msg):
        """Применить 12 углов к articulation (position targets)."""
        if self.articulation is None:
            return
        data = np.array(msg.data, dtype=np.float64)
        if data.size != 12:
            self.node.get_logger().warn(f"Expected 12 joints, got {data.size}")
            return
        self.last_cmd = data
        self.cmd_time = time.time()
        try:
            # Ожидаемый shape (N, D) — один робот, 12 DOF
            self.articulation.set_dof_position_targets(data.reshape(1, -1))
        except Exception as e:
            self.node.get_logger().warn(f"set_dof_position_targets failed: {e}")

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
                self.node.get_logger().warn(f"spin_once error: {e}")
                break

    def run(self):
        """Запустить фоновый поток rclpy."""
        self.ros_thread = threading.Thread(target=self.spin_ros, daemon=True)
        self.ros_thread.start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Isaac Sim ↔ Rust controller bridge")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--ns", default="/robot1", help="ROS namespace")
    parser.add_argument("--sim-rate", type=float, default=100.0)
    parser.add_argument("--dt", type=float, default=0.005, help="physics dt")
    args = parser.parse_args()

    from isaacsim import SimulationApp
    sim_app = SimulationApp({"headless": args.headless, "width": 1280, "height": 720})
    print(f"[bridge] Isaac Sim started (headless={args.headless})", flush=True)

    # --- Импорт URDF + ground plane (общий код с load_go2.py) ----------
    import os
    import sys as _sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    _sys.path.insert(0, os.path.join(project_root, "src", "isaac"))
    from load_go2 import GO2_URDF, GO2_DESC, ARTICULATION_PRIM  # noqa: E402

    if not os.path.exists(GO2_URDF):
        print(f"[bridge] ERROR: URDF not found: {GO2_URDF}", flush=True)
        sim_app.close()
        return 1

    import omni.usd
    from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig
    from isaacsim.core.experimental.prims import Articulation
    from pxr import Sdf, UsdGeom, UsdLux, UsdPhysics, UsdShade

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

    importer = URDFImporter(config)
    usd_path = importer.import_urdf()
    print(f"[bridge] URDF imported → {usd_path}", flush=True)

    # Явно открыть сгенерированный stage в контексте (import_urdf не делает это надёжно)
    import omni.usd
    ctx = omni.usd.get_context()
    ctx.open_stage(usd_path)
    for _ in range(20):
        sim_app.update()

    # Ground plane + свет
    stage = omni.usd.get_context().get_stage()
    UsdLux.DistantLight.Define(stage, "/World/ground/Sun")
    ground = UsdGeom.Cube.Define(stage, "/World/ground/GroundPlane")
    ground.AddTranslateOp().Set((0, 0, -0.025))
    ground.AddScaleOp().Set((1000, 1000, 0.05))
    ground.CreateDisplayColorAttr([(0.2, 0.25, 0.3)])
    mat_path = "/World/ground/Looks/PhysicsMaterial"
    material = UsdShade.Material.Define(stage, mat_path)
    physics_mat = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    physics_mat.CreateStaticFrictionAttr().Set(1.0)
    physics_mat.CreateDynamicFrictionAttr().Set(1.0)
    physics_mat.CreateRestitutionAttr().Set(0.0)
    UsdShade.MaterialBindingAPI.Apply(ground.GetPrim()).Bind(material)
    print("[bridge] ground plane created", flush=True)

    bridge = IsaacBridge(ns=args.ns, rate=args.sim_rate)

    # Найти реальный articulation prim (имя может отличаться после композиции)
    from pxr import UsdPhysics
    art_path = None
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            art_path = str(prim.GetPath())
            print(f"[bridge] articulation found: {art_path}", flush=True)
            break
    if art_path is None:
        print("[bridge] ERROR: no ArticulationRoot found in stage", flush=True)
        sim_app.close()
        return 1

    # Articulation (уже загруженный load_go2.py или импорт здесь)
    articulation = Articulation(art_path)
    bridge.attach(articulation)

    # Запуск rclpy в фоне
    bridge.run()
    print("[bridge] bridge running. Ctrl+C to stop.", flush=True)

    # Физический цикл
    import omni.timeline
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()

    # Первые шаги для инициализации тензорных данных
    for _ in range(30):
        sim_app.update()

    try:
        while sim_app.is_running():
            sim_app.update()
            # Чтение фактических углов
            try:
                pos = articulation.get_dof_positions()[0]  # warp-массив (N, D)
                bridge.publish_joint_states(np.array(pos, dtype=np.float64))
            except Exception:
                pass
    except KeyboardInterrupt:
        pass

    timeline.stop()
    sim_app.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
