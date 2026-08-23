#!/usr/bin/env python3
"""
isaac_rust_bridge.py — мост между Rust-контроллером (rclrs) и Isaac Sim
с ассетом NVIDIA (Mujoco_Menagerie go2.usda + правильная физика).

Отличается от isaac_bridge.py тем, что робот загружается из ГОТОВОГО
ассета NVIDIA (не из xacro-URDF): правильные массы/инерции/коллизии,
поэтому робот не падает/не уходит в NaN при TROT.

Работает ВНУТРИ процесса Isaac Sim (нужен доступ к omni/isaacsim API).

Задача:
  1. Подписан на /joint_group_controller/commands (Float64MultiArray, 12
     углов) от Rust-контроллера → применяет к articulation Go2
  2. Публикует /joint_states, /imu, /foot_contact (фактические данные)

Порядок joint в командах Rust-контроллера (по ногам FR,FL,RR,RL):
    FR: hip, upper, lower; FL: hip, upper, lower;
    RR: hip, upper, lower; RL: hip, upper, lower

Порядок DOF в ассете NVIDIA (группы hip/thigh/calf, ноги FL,FR,RL,RR):
    [FL_hip, FR_hip, RL_hip, RR_hip,
     FL_thigh, FR_thigh, RL_thigh, RR_thigh,
     FL_calf, FR_calf, RL_calf, RR_calf]

Запуск из venv Isaac Sim:
    source ~/isaacsim-venv/bin/activate
    python src/isaac/isaac_rust_bridge.py [--headless] [--sim-rate 100] [--ns /robot1] [--debug]

Отладка: --debug (или env ISAAC_DEBUG=1) включает подробный вывод.
"""

import argparse
import os
import sys
import threading
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from isaac_debug import log, setup_debug, freq, require_memory, fmt_pose, fmt_joints, quat_to_rpy_deg  # noqa: E402

TAG = "rust_bridge"

# --- ROS2 rclpy (встроенный Jazzy в Isaac Sim) -------------------------
# Запускать через run_rust_bridge.sh: он ставит PYTHONPATH/AMENT_PREFIX_PATH
# на jazzy/rclpy ДО старта python, иначе Lyrical (py3.14) перекроет
# встроенный rclpy (Jazzy, py3.12) и сломает типы (rosidl_typesupport_c).
ISAAC_ROS2 = os.path.expanduser(
    "~/isaacsim-venv/lib/python3.12/site-packages/isaacsim/exts/isaacsim.ros2.core/jazzy"
)

lib_paths = [f"{ISAAC_ROS2}/lib"]
existing = os.environ.get("LD_LIBRARY_PATH", "")
kept = [p for p in existing.split(":") if p and "/opt/ros/lyrical" not in p]
os.environ["LD_LIBRARY_PATH"] = ":".join(lib_paths + kept)
for p in (f"{ISAAC_ROS2}/rclpy", f"{ISAAC_ROS2}/lib"):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")
os.environ.setdefault("ROS_DOMAIN_ID", "0")
os.environ.setdefault("CYCLONEDDS_URI", "file:///home/redalexdad/.cyclonedds.xml")

# --- Ассет NVIDIA Go2 (локальные копии в проекте) ----------------------
_PROJECT_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Isaac")
_HOME_ASSETS = os.path.expanduser("~/isaac_assets/Isaac")
LOCAL_ASSET_ROOT = _PROJECT_ASSETS if os.path.isdir(_PROJECT_ASSETS) else _HOME_ASSETS
GO2_USD = f"file://{LOCAL_ASSET_ROOT}/Samples/Mujoco_Menagerie/unitree_go2/go2/go2.usda"
GROUND_USD = f"file://{LOCAL_ASSET_ROOT}/Environments/Grid/default_environment.usd"

# Имена DOF в ассете NVIDIA (порядок в articulation)
DOF_NAMES_NVIDIA = [
    "FL_hip_joint", "FR_hip_joint", "RL_hip_joint", "RR_hip_joint",
    "FL_thigh_joint", "FR_thigh_joint", "RL_thigh_joint", "RR_thigh_joint",
    "FL_calf_joint", "FR_calf_joint", "RL_calf_joint", "RR_calf_joint",
]

# Порядок joint в КОМАНДАХ Rust-контроллера (по ногам FR,FL,RR,RL)
# (для публикации joint_states в командном порядке)
CMD_JOINT_NAMES = [
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
]

# Ремаппинг команда (cmd idx) → DOF Isaac (dof idx):
#  cmd0 FR_hip -> dof1 (FR_hip)      cmd1 FR_upper -> dof5 (FR_thigh)
#  cmd2 FR_lower -> dof9 (FR_calf)   cmd3 FL_hip -> dof0 (FL_hip)
#  cmd4 FL_upper -> dof4 (FL_thigh)  cmd5 FL_lower -> dof8 (FL_calf)
#  cmd6 RR_hip -> dof3 (RR_hip)      cmd7 RR_upper -> dof7 (RR_thigh)
#  cmd8 RR_lower -> dof11 (RR_calf)  cmd9 RL_hip -> dof2 (RL_hip)
#  cmd10 RL_upper -> dof6 (RL_thigh) cmd11 RL_lower -> dof10 (RL_calf)
CMD_TO_DOF_REORDER = np.array([
    1, 5, 9,     # FR
    0, 4, 8,     # FL
    3, 7, 11,    # RR
    2, 6, 10,    # RL
], dtype=np.int64)

# Для чтения ФАКТА в командном порядке: fact_cmd[i] = dof_pos[CMD_TO_DOF_REORDER[i]].
# Это ПРЯМОЕ применение CMD_TO_DOF_REORDER (не инверсия): dof_pos[dof] — значение
# сустава, индекс CMD_TO_DOF_REORDER[i] указывает DOF команды i.
DOF_TO_CMD_REORDER = CMD_TO_DOF_REORDER

# Имена лап [FR, FL, RR, RL] — порядок как в RobotFootContact.msg
FOOT_NAMES = ["FR_foot", "FL_foot", "RR_foot", "RL_foot"]


class IsaacBridge:
    """Мост Rust-контроллер → Isaac Sim (ассет NVIDIA)."""

    def __init__(self, ns: str = "/robot1", rate: int = 100):
        import rclpy
        rclpy.init()
        self.node = rclpy.create_node(f"{ns.strip('/')}_isaac_rust_bridge", namespace=ns)
        self.ns = ns
        self.rate = rate
        self.qos = 10

        # --- Подписки ---
        from std_msgs.msg import Float64MultiArray
        cmd_topic = "joint_group_controller/commands"
        self.cmd_sub = self.node.create_subscription(
            Float64MultiArray, cmd_topic, self.on_joint_command, self.qos
        )
        log.info(TAG, f"Subscribed: {ns}/{cmd_topic}")

        # --- Публикаторы ---
        from sensor_msgs.msg import JointState, Imu
        self.js_pub = self.node.create_publisher(JointState, "joint_states", self.qos)
        self.imu_pub = self.node.create_publisher(Imu, "imu", self.qos)
        self.js_count = 0

        self.fc_pub = None
        try:
            from quadropted_msgs.msg import RobotFootContact
            self.fc_pub = self.node.create_publisher(
                RobotFootContact, "foot_contact", self.qos
            )
            log.info(TAG, f"Publisher: {ns}/foot_contact")
        except Exception as e:
            log.warn(TAG, f"foot_contact publisher disabled: {e}")

        # Состояние
        self.articulation = None
        self.ready = False
        self.last_cmd = np.zeros(12, dtype=np.float64)
        self.cmd_count = 0
        self.contacts = np.zeros(4, dtype=bool)
        self.ros_thread = None
        self._spin_ok = True
        self._spin_iters = 0

    def attach(self, articulation):
        self.articulation = articulation

    def on_joint_command(self, msg):
        """Сохранить последнюю команду (применение — в основном цикле)."""
        data = np.array(msg.data, dtype=np.float64)
        if len(data) != 12:
            log.warn(TAG, f"command length {len(data)} != 12, игнор")
            return
        if not np.all(np.isfinite(data)):
            log.warn(TAG, f"command содержит NaN/Inf, игнор: {data}")
            return
        self.last_cmd = data
        self.cmd_count += 1

    def apply_pending_command(self):
        """Применить последнюю команду к articulation (из основного цикла).

        Ремаппинг: CMD_TO_DOF_REORDER[i] = dof-индекс для команды i.
        Правильная операция: targets[dof] = cmd[источник], т.е.
        targets[CMD_TO_DOF_REORDER] = self.last_cmd.
        """
        if self.articulation is None or not self.ready:
            return
        try:
            targets = np.zeros(12, dtype=np.float64)
            targets[CMD_TO_DOF_REORDER] = self.last_cmd
            self.articulation.set_dof_position_targets(targets.reshape(1, -1))
        except Exception as e:
            log.warn(TAG, f"set_dof_position_targets failed: {e}")

    def publish_sensors(self):
        """Публикация IMU + диагностика позы."""
        if self.articulation is None:
            return
        try:
            pos, ori = self.articulation.get_world_poses(indices=[0])
            lin_vel, ang_vel = self.articulation.get_velocities(indices=[0])
            q = np.array(ori[0], dtype=np.float64)
            p = np.array(pos[0], dtype=np.float64)
            av = np.array(ang_vel[0], dtype=np.float64)
            lv = np.array(lin_vel[0], dtype=np.float64)
            log.debug(TAG, fmt_pose(p, q, tag="pose"))
            log.debug(TAG, f"[vel] lin={lv.round(3)} ang={av.round(3)}")

            nan_mask = np.isnan(p).any() or np.isnan(q).any() or np.isnan(lv).any() or np.isnan(av).any()
            if nan_mask:
                log.error(TAG, f"NaN DETECTED! pos={p} quat={q}")

            from sensor_msgs.msg import Imu
            imu = Imu()
            imu.header.stamp = self.node.get_clock().now().to_msg()
            imu.header.frame_id = "imu"
            imu.orientation.w = float(q[0]); imu.orientation.x = float(q[1])
            imu.orientation.y = float(q[2]); imu.orientation.z = float(q[3])
            imu.angular_velocity.x = float(av[0]); imu.angular_velocity.y = float(av[1])
            imu.angular_velocity.z = float(av[2])
            try:
                self.imu_pub.publish(imu)
            except Exception as e:
                log.warn(TAG, f"imu_pub error: {e}")
        except Exception as e:
            log.warn(TAG, f"publish_sensors IMU error: {e}")

        # Команды vs факт (в командном порядке)
        try:
            dof_pos = np.array(self.articulation.get_dof_positions()[0], dtype=np.float64)
            fact_cmd_order = dof_pos[DOF_TO_CMD_REORDER]
            err = self.last_cmd - fact_cmd_order
            log.debug(TAG, "CMD  " + fmt_joints(self.last_cmd, CMD_JOINT_NAMES, tag="cmd").split("\n", 1)[0])
            log.debug(TAG, "FACT " + fmt_joints(fact_cmd_order, CMD_JOINT_NAMES, tag="fact").split("\n", 1)[0])
            log.debug(TAG, f"[joint_err] max_abs={np.abs(err).max():.3f}  mean_abs={np.abs(err).mean():.3f}")

            # Периодически (раз в ~2.5с) — hip-углы в DOF-порядке (FL,FR,RL,RR),
            # чтобы видеть крен/равновесие
            if not hasattr(self, "_hip_diag"):
                self._hip_diag = 0
            self._hip_diag += 1
            if self._hip_diag % 100 == 0:
                hip_dof = dof_pos[0:4]  # FL,FR,RL,RR hip
                hip_cmd = np.zeros(12)
                hip_cmd[CMD_TO_DOF_REORDER] = self.last_cmd
                hip_cmd = hip_cmd[0:4]
                log.info(
                    TAG,
                    f"[HIP] cmd=[{hip_cmd[0]:+.3f} {hip_cmd[1]:+.3f} {hip_cmd[2]:+.3f} {hip_cmd[3]:+.3f}] "
                    f"fact=[{hip_dof[0]:+.3f} {hip_dof[1]:+.3f} {hip_dof[2]:+.3f} {hip_dof[3]:+.3f}] "
                    f"(FL FR RL RR)",
                )

            # Периодически — высоты стоп и тела, чтобы видеть «проседание»
            if not hasattr(self, "_foot_diag"):
                self._foot_diag = 0
            self._foot_diag += 1
            if not hasattr(self, "_links_logged"):
                log.info(TAG, f"link_names={list(self.articulation.link_names)}")
                self._links_logged = True
            if self._foot_diag % 100 == 0:
                try:
                    link_names = list(self.articulation.link_names)
                    foot_idx = {}
                    for leg in ["FL", "FR", "RL", "RR"]:
                        for ln in link_names:
                            if ln.endswith(f"{leg}_foot"):
                                foot_idx[leg] = self.articulation.get_link_indices([ln])
                                break
                    heights = {}
                    for leg, idx in foot_idx.items():
                        fp, _ = self.articulation.get_world_poses(indices=idx)
                        heights[leg] = float(np.array(fp[0])[2])
                    log.info(
                        TAG,
                        f"[FEET] z={heights.get('FL', float('nan')):+.3f} "
                        f"{heights.get('FR', float('nan')):+.3f} "
                        f"{heights.get('RL', float('nan')):+.3f} "
                        f"{heights.get('RR', float('nan')):+.3f} (FL FR RL RR) | "
                        f"body_z={p[2]:+.3f}",
                    )
                except Exception as e:
                    log.debug(TAG, f"foot diag skipped: {e}")
        except Exception as e:
            log.debug(TAG, f"joint diag skipped: {e}")

        # Контакты
        if self.fc_pub is not None:
            self.publish_foot_contact(self.contacts)

    def publish_joint_states(self, positions: np.ndarray):
        """Публикация фактических углов (в командном порядке)."""
        from sensor_msgs.msg import JointState
        js = JointState()
        js.header.stamp = self.node.get_clock().now().to_msg()
        js.name = list(CMD_JOINT_NAMES)
        js.position = [float(x) for x in positions[DOF_TO_CMD_REORDER]]
        try:
            self.js_pub.publish(js)
            self.js_count += 1
        except Exception as e:
            log.warn(TAG, f"js_pub error: {e}")

    def publish_foot_contact(self, contacts: np.ndarray):
        if self.fc_pub is None:
            return
        from quadropted_msgs.msg import RobotFootContact
        msg = RobotFootContact()
        msg.contacts = [bool(c) for c in contacts]
        try:
            self.fc_pub.publish(msg)
        except Exception as e:
            log.warn(TAG, f"fc_pub error: {e}")

    def spin_ros(self):
        import rclpy
        from rclpy.executors import SingleThreadedExecutor
        self._spin_ok = True
        while True:
            try:
                if not rclpy.ok():
                    log.error(TAG, "rclpy не ok, переинициализирую...")
                    try:
                        rclpy.shutdown()
                    except Exception:
                        pass
                    rclpy.init()
                    self.node = rclpy.create_node(
                        f"{self.ns.strip('/')}_isaac_rust_bridge", namespace=self.ns
                    )
                    self._recreate_pubsub()
                    log.info(TAG, "rclpy переинициализирован")
                    continue
                # Свой executor (НЕ глобальный): он создаёт guard_condition от
                # ТЕКУЩЕГО контекста. Глобальный executor Isaac Sim привязан
                # к старому контексту → guard_condition невалиден.
                self._executor = SingleThreadedExecutor()
                self._executor.add_node(self.node)
                while rclpy.ok():
                    try:
                        self._executor.spin_once(timeout_sec=0.01)
                        self._spin_iters += 1
                    except rclpy.executors.ExternalShutdownException:
                        break
                    except Exception as e:
                        log.error(TAG, f"spin_once error: {e}")
                        break
                self._executor.shutdown()
            except Exception as e:
                log.error(TAG, f"spin_ros outer error: {e}")
                time.sleep(0.5)

    def _recreate_pubsub(self):
        """Пересоздать подписки/публикаторы после переинициализации rclpy."""
        from std_msgs.msg import Float64MultiArray
        from sensor_msgs.msg import JointState, Imu
        self.cmd_sub = self.node.create_subscription(
            Float64MultiArray, "joint_group_controller/commands", self.on_joint_command, self.qos
        )
        self.js_pub = self.node.create_publisher(JointState, "joint_states", self.qos)
        self.imu_pub = self.node.create_publisher(Imu, "imu", self.qos)
        try:
            from quadropted_msgs.msg import RobotFootContact
            self.fc_pub = self.node.create_publisher(RobotFootContact, "foot_contact", self.qos)
        except Exception:
            self.fc_pub = None
        log.info(TAG, "pub/sub пересозданы после rclpy-реинициализации")

    def run(self):
        self.ros_thread = threading.Thread(target=self.spin_ros, daemon=True)
        self.ros_thread.start()


def main() -> int:
    parser = argparse.ArgumentParser(description="Rust-controller bridge → Isaac (NVIDIA asset)")
    parser.add_argument("--headless", action="store_true", help="run without GUI")
    parser.add_argument("--sim-rate", type=int, default=100, help="simulation rate (Hz)")
    parser.add_argument("--ns", default="/robot1", help="ROS namespace")
    parser.add_argument("--min-ram", type=float, default=12.0, help="минимальная RAM (ГБ)")
    parser.add_argument("--debug", action="store_true", help="verbose debug output")
    parser.add_argument("--hold-stance", action="store_true",
                        help="держать STAND-позу [0,0.67,-1.3], не применять команды контроллера")
    args = parser.parse_args()

    setup_debug()
    if args.debug or os.environ.get("ISAAC_DEBUG") == "1":
        log.set_level("debug")
    log.info(TAG, f"start: headless={args.headless}, ns={args.ns}, rate={args.sim_rate}")

    require_memory(args.min_ram, tag=TAG)

    from isaacsim import SimulationApp

    sim_app = SimulationApp({"headless": args.headless, "width": 1280, "height": 720})
    log.info(TAG, f"Isaac Sim started (headless={args.headless})")

    import omni
    import carb
    from isaacsim.core.experimental.prims import Articulation
    import isaacsim.core.experimental.utils.stage as stage_utils

    # asset_root → локальный (S3 недоступен). Нужны /Isaac и /NVIDIA.
    LOCAL_ROOT = os.path.dirname(LOCAL_ASSET_ROOT)
    os.makedirs(f"{LOCAL_ROOT}/NVIDIA", exist_ok=True)
    os.makedirs(f"{LOCAL_ROOT}/Isaac", exist_ok=True)
    carb.settings.get_settings().set("/persistent/isaac/asset_root/default", f"file://{LOCAL_ROOT}")

    # Ground plane (правильная коллизия — default_environment.usd)
    if not os.path.exists(GROUND_USD.replace("file://", "")):
        log.error(TAG, f"отсутствует ground: {GROUND_USD}")
        sim_app.close()
        return 1
    t0 = time.time()
    stage_utils.add_reference_to_stage(usd_path=GROUND_USD, path="/World")
    for _ in range(10):
        sim_app.update()
    log.info(TAG, f"ground plane added ({time.time()-t0:.1f}s)")

    # Робот Go2 из ассета NVIDIA (variant Physics=physx!)
    if not os.path.exists(GO2_USD.replace("file://", "")):
        log.error(TAG, f"отсутствует ассет: {GO2_USD}")
        sim_app.close()
        return 1
    t0 = time.time()
    stage_utils.add_reference_to_stage(
        usd_path=GO2_USD,
        path="/World/Go2",
        variants=[("Physics", "physx")],
    )
    for _ in range(20):
        sim_app.update()
    log.info(TAG, f"Go2 reference loaded ({time.time()-t0:.1f}s)")

    # Диагностика: примы под /World/Go2 (сколько, есть ли articulation)
    stage = omni.usd.get_context().get_stage()
    from pxr import Usd
    go2_root = stage.GetPrimAtPath("/World/Go2")
    prims_under = sum(1 for _ in Usd.PrimRange(go2_root)) if go2_root.IsValid() else 0
    log.info(TAG, f"prims under /World/Go2: {prims_under} (root valid={go2_root.IsValid()})")

    # Найти articulation root
    from isaacsim.core.experimental.utils.prim import find_matching_prim_paths
    from pxr import UsdPhysics

    art_path = None
    if go2_root.IsValid():
        for prim in Usd.PrimRange(go2_root):
            if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                art_path = str(prim.GetPath())
                break
    if art_path is None:
        log.error(TAG, "no ArticulationRoot found under /World/Go2")
        log.error(TAG, f"prims under /World/Go2: {prims_under}, root valid={go2_root.IsValid()}")
        sim_app.close()
        return 1
    log.info(TAG, f"articulation found: {art_path}")

    bridge = IsaacBridge(ns=args.ns, rate=args.sim_rate)
    articulation = Articulation(art_path)
    bridge.attach(articulation)
    log.info(TAG, f"dof_names={articulation.dof_names}")

    # Расширить лимиты суставов: команды контроллера (STAND calf=0, TROT
    # от -2.6 до 0) выходят за пределы ассета NVIDIA (MJCF: calf [-2.72,
    # -0.84], hip [-1.047, 1.047]). В Gazebo ros2_control применял команды
    # мягко, игнорируя жёсткие лимиты — здесь разрешаем широкий диапазон.
    try:
        lower_limits = np.full(12, -100.0)
        upper_limits = np.full(12, 100.0)
        articulation.set_dof_limits(lower_limits, upper_limits)
        log.info(TAG, "joint limits расширены до [-100, 100]")
    except Exception as e:
        log.warn(TAG, f"set_dof_limits failed: {e}")

    # PD-параметры. Политика NVIDIA использует stiffness=25/0.5 и успешно
    # держит робота на этом ассете. Наш контроллер шлёт резкие команды,
    # поэтому upper/lower делаем жёсткими (100), hip — 25 (как политика,
    # не 2: при stiffness=2 hip не держит вес и робот проседает до Z=0.08).
    try:
        stiffness = np.full(12, 100.0)
        damping = np.full(12, 5.0)
        stiffness[0:4] = 25.0   # hip (DOF 0..3: FL,FR,RL,RR)
        damping[0:4] = 0.5
        articulation.set_dof_gains(stiffness, damping)
        log.info(TAG, "gains: hip_k=25 (как политика NVIDIA), upper/lower_k=100")
    except Exception as e:
        log.warn(TAG, f"set_dof_gains failed: {e}")

    bridge.run()
    log.info(TAG, "bridge running. Ctrl+C to stop.")

    # Робот над полом (как в go2_policy: 0.5 м)
    try:
        articulation.set_world_poses(
            positions=np.array([[0.0, 0.0, 0.5]]),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
        )
        log.info(TAG, "robot positioned at z=0.5")
    except Exception as e:
        log.warn(TAG, f"set_world_poses failed: {e}")

    import omni.timeline
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    log.info(TAG, "timeline.play() called")

    log.debug(TAG, "инициализация тензорных данных (5 шагов)...")
    for _ in range(5):
        sim_app.update()

    # Начальная поза суставов — правильная стойка Go2 из готового решения
    # CLeARoboticsLab/go2_isaac_ros2: STANDING_JOINT_ANGLES = [hip, thigh,
    # calf] = [0.0, 0.67, -1.3] × 4 (порядок ног не важен — все одинаковые).
    # Ранее использовалась поза из env.yaml политики (hip=±0.1, thigh=0.8,
    # calf=-1.5) и поза контроллера (thigh=1.57, calf=0) — робот «сидел»
    # (Z≈0.08). Правильная стойка — thigh=0.67, calf=-1.3.
    try:
        default_dof = np.array([
            0.0, 0.0, 0.0, 0.0,       # FL,FR,RL,RR hip
            0.67, 0.67, 0.67, 0.67,   # FL,FR,RL,RR thigh
            -1.3, -1.3, -1.3, -1.3,   # FL,FR,RL,RR calf
        ], dtype=np.float64)
        articulation.set_dof_positions(default_dof.reshape(1, -1))
        log.info(TAG, f"default stance set (go2_isaac_ros2 STANDING): {default_dof.round(2)}")
    except Exception as e:
        log.warn(TAG, f"set_dof_positions (default stance) failed: {e}")

    bridge.ready = True
    log.debug(TAG, "bridge ready, entering main loop")
    last_cmd = 0
    last_it = 0

    try:
        it = 0
        while sim_app.is_running():
            sim_app.update()
            it += 1
            freq.tick("loop")
            if args.hold_stance:
                # Калибровка: держим правильную STAND-позу, игнорируя команды
                # контроллера (проверка, что поза [0,0.67,-1.3] поднимает робота)
                try:
                    stance = np.array([
                        0.0, 0.0, 0.0, 0.0,
                        0.67, 0.67, 0.67, 0.67,
                        -1.3, -1.3, -1.3, -1.3,
                    ], dtype=np.float64)
                    articulation.set_dof_position_targets(stance.reshape(1, -1))
                except Exception as e:
                    if it % 100 == 0:
                        log.warn(TAG, f"hold_stance error: {e}")
            else:
                bridge.apply_pending_command()
            try:
                pos = articulation.get_dof_positions()[0]
                bridge.publish_joint_states(np.array(pos, dtype=np.float64))
            except Exception as e:
                if it % 100 == 0:
                    log.warn(TAG, f"get_dof_positions error: {e}")
            bridge.publish_sensors()
            if it % 100 == 0:
                pose_line = "?"
                try:
                    pp, oo = articulation.get_world_poses(indices=[0])
                    qq = np.array(oo[0], dtype=np.float64)
                    ppp = np.array(pp[0], dtype=np.float64)
                    r, p, y = quat_to_rpy_deg(qq)
                    pose_line = f"pos=({ppp[0]:+.2f},{ppp[1]:+.2f},{ppp[2]:+.2f}) rpy=({r:+.1f}°,{p:+.1f}°,{y:+.1f}°)"
                except Exception as e:
                    pose_line = f"? ({e})"
                # Скорость поступления команд за последние 100 итераций
                dc = bridge.cmd_count - last_cmd
                cmd_rate = dc * freq.rate("loop") / 100.0
                last_cmd = bridge.cmd_count
                # Ошибки следования суставов
                err_line = "?"
                try:
                    dp = np.array(articulation.get_dof_positions()[0], dtype=np.float64)
                    fact = dp[DOF_TO_CMD_REORDER]
                    err = bridge.last_cmd - fact
                    err_line = f"joint_err max={np.abs(err).max():.3f} mean={np.abs(err).mean():.3f}"
                except Exception:
                    pass
                # Сжатая команда (в командном порядке): первые 6 + последние 6
                c = bridge.last_cmd
                cmd_line = (f"[{c[0]:+.2f} {c[1]:+.2f} {c[2]:+.2f} | "
                            f"{c[3]:+.2f} {c[4]:+.2f} {c[5]:+.2f} | "
                            f"{c[6]:+.2f} {c[7]:+.2f} {c[8]:+.2f} | "
                            f"{c[9]:+.2f} {c[10]:+.2f} {c[11]:+.2f}]")
                log.info(
                    TAG,
                    f"[REPORT] {freq.report('loop')} | {pose_line} | {err_line} | "
                    f"cmd={bridge.cmd_count} (+{dc} @{cmd_rate:.0f}/s) js={bridge.js_count} | "
                    f"spin={'OK' if bridge._spin_ok else 'DEAD'} | CMD {cmd_line}",
                )
    except KeyboardInterrupt:
        pass

    timeline.stop()
    sim_app.close()
    log.info(TAG, "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
