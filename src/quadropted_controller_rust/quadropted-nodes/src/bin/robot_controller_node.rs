//! Robot Controller Node — Full Rust implementation with State Machine
//!
//! Full ROS 2 integration:
//! - Behavior State Machine: REST/TROT/CRAWL/STAND
//! - Subscriptions: robot_mode, robot_velocity, imu
//! - TrotGaitController + CrawlGaitController
//! - IK computes joint angles from foot positions
//! - Float64MultiArray publisher for joint_group_controller/commands

use std_msgs_rs::Float64MultiArray;
use quadropted_core::controllers::trot::gait::TrotGaitController;
use quadropted_core::controllers::crawl::gait::CrawlGaitController;
use quadropted_core::controllers::rest::{RestController, RestState};
use quadropted_core::controllers::stand::{StandController, BodyState};
use quadropted_core::state::behavior::BehaviorState;
use quadropted_core::kinematics::inverse::{compute_local_positions, compute_all_joint_angles};
use nalgebra::SMatrix;
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions};
use rosidl_runtime_rs::Sequence;
use std::sync::{Arc, Mutex};
use std::time::Duration;

struct SharedState {
    ticks: i32,
    foot_locations: SMatrix<f64, 3, 4>,
    default_stance: SMatrix<f64, 3, 4>,
    behavior_state: BehaviorState,
    trot_gait: TrotGaitController,
    crawl_gait: CrawlGaitController,
    rest_ctrl: RestController,
    rest_state: RestState,
    stand_ctrl: StandController,
    body_state: BodyState,
    cmd_linear: [f64; 3],
    cmd_angular: [f64; 3],
    imu_roll: f64,
    imu_pitch: f64,
    mode_msg_count: u64,
    vel_msg_count: u64,
    startup_grace: i32,
}

impl SharedState {
    fn new() -> Self {
        let body_length = 0.3762;
        let body_width = 0.0935;
        let l2 = 0.0955;
        let dx_front = body_length * 0.5 + 0.02;
        let dx_back = body_length * 0.5;
        let dy = body_width * 0.5 + l2;

        let mut default_stance = SMatrix::<f64, 3, 4>::zeros();
        default_stance[(0, 0)] = dx_front; default_stance[(1, 0)] = -dy;
        default_stance[(0, 1)] = dx_front; default_stance[(1, 1)] = dy;
        default_stance[(0, 2)] = -dx_back; default_stance[(1, 2)] = -dy;
        default_stance[(0, 3)] = -dx_back; default_stance[(1, 3)] = dy;

        let trot_gait = TrotGaitController::new(0.04, 0.18, 0.02, false, default_stance.clone());
        let crawl_gait = CrawlGaitController::new(0.55, 0.45, 0.02, default_stance.clone());
        let rest_ctrl = RestController::new(default_stance.clone());
        let stand_ctrl = StandController::new(default_stance.clone());

        println!("[Rust] Default stance:");
        for leg in 0..4 {
            let name = ["FR", "FL", "RR", "RL"][leg];
            println!("[Rust]   {}: x={:.4} y={:.4}", name, default_stance[(0, leg)], default_stance[(1, leg)]);
        }

        Self {
            ticks: 0,
            foot_locations: default_stance.clone(),
            default_stance,
            behavior_state: BehaviorState::REST,
            trot_gait,
            crawl_gait,
            rest_ctrl,
            rest_state: RestState { imu_roll: 0.0, imu_pitch: 0.0 },
            stand_ctrl,
            body_state: BodyState {
                body_local_position: [0.0, 0.0, 0.0],
                body_local_orientation: [0.0, 0.0, 0.0],
            },
            cmd_linear: [0.0, 0.0, 0.0],
            cmd_angular: [0.0, 0.0, 0.0],
            imu_roll: 0.0,
            imu_pitch: 0.0,
            mode_msg_count: 0,
            vel_msg_count: 0,
            startup_grace: 120, // 2 сек @ 60 Гц (как C++ startup_grace_)
        }
    }

    fn step(&mut self, robot_height: f64) -> [f64; 12] {
        self.ticks += 1;

        // State machine: select controller based on behavior_state
        self.foot_locations = match self.behavior_state {
            BehaviorState::REST => {
                self.rest_ctrl.step(&self.rest_state, robot_height)
            }
            BehaviorState::TROT => {
                let gait_cmd = [self.cmd_linear[0], self.cmd_linear[1], self.cmd_angular[2]];
                // C++ step_trot: при нулевой скорости — плавное возвращение к default_stance
                let has_command =
                    gait_cmd[0].abs() > 1e-4 || gait_cmd[1].abs() > 1e-4 || gait_cmd[2].abs() > 1e-4;
                if !has_command {
                    let mut result = self.default_stance;
                    result.row_mut(2).fill(robot_height);
                    let alpha = 0.1;
                    self.foot_locations * (1.0 - alpha) + result * alpha
                } else {
                    let mut new_foot = self.trot_gait.step(
                        self.ticks,
                        &self.foot_locations,
                        &gait_cmd,
                        robot_height,
                    );
                    // IMU compensation (как в C++ step_trot)
                    if self.trot_gait.use_imu() {
                        let now_sec = std::time::SystemTime::now()
                            .duration_since(std::time::UNIX_EPOCH)
                            .map(|d| d.as_secs_f64())
                            .unwrap_or(0.0);
                        let comp = self.trot_gait.pid_controller().run(self.imu_roll, self.imu_pitch, now_sec);
                        let rot = quadropted_core::math::rotation::rotxyz(-comp[0], -comp[1], 0.0);
                        new_foot = rot * new_foot;
                    }
                    new_foot
                }
            }
            BehaviorState::CRAWL => {
                // Clamp velocity for crawl mode
                let mut crawl_vel = [self.cmd_linear[0], self.cmd_linear[1], self.cmd_angular[2]];
                crawl_vel[0] = crawl_vel[0].clamp(-0.011, 0.011);
                crawl_vel[1] = crawl_vel[1].clamp(-0.0055, 0.0055);
                crawl_vel[2] = crawl_vel[2].clamp(-0.15, 0.15);

                self.crawl_gait.step(self.ticks, &self.foot_locations, &crawl_vel, robot_height)
            }
            BehaviorState::STAND => {
                self.stand_ctrl.run(
                    &mut self.body_state,
                    robot_height,
                    &self.cmd_linear,
                    &self.cmd_angular,
                )
            }
        };

        // IK: foot positions → joint angles
        // C++ передаёт body_local_position/orientation (высота тела из change_controller)
        let bp = &self.body_state.body_local_position;
        let bo = &self.body_state.body_local_orientation;
        let local = compute_local_positions(
            &self.foot_locations, 0.3762, 0.0935,
            bp[0], bp[1], bp[2], bo[0], bo[1], bo[2],
        );
        let angles = compute_all_joint_angles(&local, 0.0, 0.0955, 0.213, 0.213);

        angles
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🦀 Rust Robot Controller Node starting...");
    println!("   Features: State Machine (REST/TROT/CRAWL/STAND) + IK + Subscriptions\n");

    // Парсим аргументы процесса (--ros-args -r __ns:=/robot1 от launch), иначе
    // namespace и remappings из launch-файла не применяются (rclrs 0.7).
    let ctx = Context::new(std::env::args(), rclrs::InitOptions::new())?;
    let mut executor = ctx.create_basic_executor();
    let node = executor.create_node("robot_controller_rust")?;
    println!("✅ Node created: robot_controller_rust");

    let state = Arc::new(Mutex::new(SharedState::new()));

    // Publisher for joint commands
    let joint_pub: Publisher<Float64MultiArray> =
        node.create_publisher("joint_group_controller/commands")?;
    println!("✅ Publisher: joint_group_controller/commands");

    // Publisher for foot contacts (для odometry — как C++ publish_foot_contacts)
    let contact_pub: Publisher<quadropted_msgs_rs::RobotFootContact> =
        node.create_publisher("foot_contact")?;
    println!("✅ Publisher: foot_contact");

    // Subscription: robot_mode
    let mode_state = state.clone();
    let _mode_sub = node.create_subscription("robot_mode", move |msg: quadropted_msgs_rs::RobotModeCommand| {
        if msg.robot_id == 1 {
            let mut s = mode_state.lock().unwrap();
            let mode_raw = msg.mode.to_cstr().to_string_lossy();
            let mode_str = mode_raw.trim().trim_matches(char::from(0));
            if let Some(new_state) = BehaviorState::from_str(mode_str) {
                s.mode_msg_count += 1;
                println!("[Rust] Mode change: {:?} -> {:?}", s.behavior_state, new_state);
                s.behavior_state = new_state;
                s.ticks = 0;

                // Reset controllers on mode change (как в C++ change_controller)
                match new_state {
                    BehaviorState::CRAWL => {
                        s.crawl_gait.reset();
                        s.body_state.body_local_position[2] = 0.0;
                    }
                    BehaviorState::TROT => {
                        // C++: trot_gait_->pid_controller().reset(this->now().seconds())
                        s.trot_gait.pid_controller().reset(
                            std::time::SystemTime::now()
                                .duration_since(std::time::UNIX_EPOCH)
                                .map(|d| d.as_secs_f64())
                                .unwrap_or(0.0),
                        );
                        s.body_state.body_local_position[2] = 0.0;
                    }
                    BehaviorState::REST => {
                        // C++: body_local_position[2] = -0.15 (лечь на землю)
                        s.body_state.body_local_position[2] = -0.15;
                    }
                    BehaviorState::STAND => {
                        // C++: body_local_position[2] = 0.005
                        s.body_state.body_local_position[2] = 0.005;
                    }
                }
            } else {
                println!("[Rust] Ignored unknown mode: '{}'", mode_str);
            }
        }
    })?;
    println!("✅ Subscription: robot_mode");

    // Subscription: robot_velocity
    let vel_state = state.clone();
    let _vel_sub = node.create_subscription("robot_velocity", move |msg: quadropted_msgs_rs::RobotVelocity| {
        if msg.robot_id == 1 {
            let mut s = vel_state.lock().unwrap();
            s.vel_msg_count += 1;
            s.cmd_linear = [
                msg.cmd_vel.linear.x,
                msg.cmd_vel.linear.y,
                msg.cmd_vel.linear.z,
            ];
            s.cmd_angular = [
                msg.cmd_vel.angular.x,
                msg.cmd_vel.angular.y,
                msg.cmd_vel.angular.z,
            ];
        }
    })?;
    println!("✅ Subscription: robot_velocity");

    // Subscription: imu
    let imu_state = state.clone();
    let _imu_sub = node.create_subscription("imu", move |msg: sensor_msgs_rs::Imu| {
        let mut s = imu_state.lock().unwrap();
        // Convert quaternion to euler angles
        let w = msg.orientation.w;
        let x = msg.orientation.x;
        let y = msg.orientation.y;
        let z = msg.orientation.z;
        s.imu_roll = (2.0 * (w * x + y * z)).atan2(1.0 - 2.0 * (x * x + y * y));
        s.imu_pitch = (2.0 * (w * y - z * x)).asin();
    })?;
    println!("✅ Subscription: imu");

    // Service: robot_behavior_command (sit/up/walk) — как C++ behavior_srv_
    let srv_state = state.clone();
    let _behavior_srv = node.create_service::<quadropted_msgs_rs::RobotBehaviorCommand, _>(
        "robot_behavior_command",
        move |req: quadropted_msgs_rs::RobotBehaviorCommand_Request| {
            let mut resp = quadropted_msgs_rs::RobotBehaviorCommand_Response::default();
            let cmd = req.command.to_cstr().to_string_lossy().to_lowercase();
            println!("[Rust] Received behavior command: {}", cmd);

            let mut s = srv_state.lock().unwrap();
            match cmd.as_str() {
                "sit" => {
                    s.behavior_state = BehaviorState::STAND;
                    s.ticks = 0;
                    s.body_state.body_local_position[2] = -0.15;
                    resp.success = true;
                    resp.message = "Robot sat down.".into();
                }
                "up" => {
                    s.behavior_state = BehaviorState::REST;
                    s.ticks = 0;
                    s.body_state.body_local_position[2] = 0.0;
                    resp.success = true;
                    resp.message = "Robot stood up.".into();
                }
                "walk" => {
                    s.behavior_state = BehaviorState::REST;
                    s.ticks = 0;
                    s.body_state.body_local_position[2] = 0.0;
                    // C++: rest_event + trot_event → REST затем TROT
                    s.behavior_state = BehaviorState::TROT;
                    s.ticks = 0;
                    s.trot_gait.pid_controller().reset(
                        std::time::SystemTime::now()
                            .duration_since(std::time::UNIX_EPOCH)
                            .map(|d| d.as_secs_f64())
                            .unwrap_or(0.0),
                    );
                    resp.success = true;
                    resp.message = "Robot started walking.".into();
                }
                other => {
                    resp.success = false;
                    resp.message = format!("Unknown command: {}", other).into();
                }
            }
            resp
        },
    )?;
    println!("✅ Service: robot_behavior_command");

    // 60Hz control loop
    let ctrl_state = state.clone();
    let ctrl_pub = joint_pub.clone();
    std::thread::spawn(move || loop {
        let mut s = ctrl_state.lock().unwrap();

        // Startup grace period: ждём пока робот приземлится (как C++ startup_grace_)
        if s.startup_grace > 0 {
            s.startup_grace -= 1;
            if s.startup_grace == 0 {
                println!("[Rust] Startup grace period complete, controller active");
            }
            drop(s);
            std::thread::sleep(Duration::from_millis(16));
            continue;
        }

        let angles = s.step(-0.25);

        if s.ticks % 120 == 0 {
            println!("[Rust DEBUG] Tick #{} ({:.1}s) {:?} mode, vx={:.3}",
                s.ticks, s.ticks as f64 / 60.0, s.behavior_state, s.cmd_linear[0]);
        }

        let mut msg = Float64MultiArray::default();
        let mut seq = Sequence::new(angles.len());
        for (i, &val) in angles.iter().enumerate() { seq[i] = val; }
        msg.data = seq;
        ctrl_pub.publish(&msg).ok();

        // Публикация контактов ног (для odometry) — как C++ publish_foot_contacts
        let contact_msg = {
            let mut cm = quadropted_msgs_rs::RobotFootContact::default();
            match s.behavior_state {
                BehaviorState::REST | BehaviorState::STAND => {
                    cm.contacts = [true, true, true, true];
                }
                BehaviorState::TROT => {
                    let c = s.trot_gait.contacts(s.ticks);
                    cm.contacts = [c[0] != 0, c[1] != 0, c[2] != 0, c[3] != 0];
                }
                BehaviorState::CRAWL => {
                    let c = s.crawl_gait.contacts(s.ticks);
                    cm.contacts = [c[0] != 0, c[1] != 0, c[2] != 0, c[3] != 0];
                }
            }
            cm
        };
        contact_pub.publish(&contact_msg).ok();

        drop(s);
        std::thread::sleep(Duration::from_millis(16)); // 60Hz
    });

    println!("✅ 60Hz control loop with State Machine");
    println!("🚀 Spinning (Ctrl+C to stop)...\n");

    loop {
        let mut spin_opts = SpinOptions::default();
        spin_opts.timeout = Some(Duration::from_millis(1000));
        let _ = executor.spin(spin_opts);
    }
}
