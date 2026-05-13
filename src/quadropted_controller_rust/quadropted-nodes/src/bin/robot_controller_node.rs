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
use std::fs::OpenOptions;
use std::io::Write;
use std::sync::atomic::{AtomicU64, Ordering};

// #region agent log
static LOG_SEQ: AtomicU64 = AtomicU64::new(0);
const DEBUG_LOG_PATH: &str = "/home/redalexdad/GitHub/WalkingRobotSim/.cursor/debug-f81059.log";
const DEBUG_SESSION_ID: &str = "f81059";

fn dbg_log(run_id: &str, hypothesis_id: &str, location: &str, message: &str, data: &str) {
    let seq = LOG_SEQ.fetch_add(1, Ordering::Relaxed);
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let line = format!(
        "{{\"sessionId\":\"{}\",\"id\":\"{}-{}\",\"timestamp\":{},\"location\":\"{}\",\"message\":\"{}\",\"data\":{},\"runId\":\"{}\",\"hypothesisId\":\"{}\"}}",
        DEBUG_SESSION_ID, DEBUG_SESSION_ID, seq, ts, location, message, data, run_id, hypothesis_id
    );
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(DEBUG_LOG_PATH) {
        let _ = writeln!(f, "{}", line);
    }
}
// #endregion

struct SharedState {
    ticks: i32,
    foot_locations: SMatrix<f64, 3, 4>,
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
                self.trot_gait.step(
                    self.ticks,
                    &self.foot_locations,
                    &gait_cmd,
                    robot_height,
                )
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

        if self.behavior_state == BehaviorState::CRAWL && self.ticks % 60 == 0 {
            let contacts = self.crawl_gait.contacts(self.ticks);
            let phase_idx = self.crawl_gait.phase_index(self.ticks);
            let sub_ticks = self.crawl_gait.subphase_ticks(self.ticks);
            println!(
                "[RUNTIME_CRAWL_RUST] ticks={} phase={} sub={} contacts=[{},{},{},{}] cmd=[{:.4},{:.4},{:.4}] \
fr=({:.4},{:.4},{:.4}) fl=({:.4},{:.4},{:.4}) rr=({:.4},{:.4},{:.4}) rl=({:.4},{:.4},{:.4})",
                self.ticks,
                phase_idx,
                sub_ticks,
                contacts[0], contacts[1], contacts[2], contacts[3],
                self.cmd_linear[0], self.cmd_linear[1], self.cmd_angular[2],
                self.foot_locations[(0, 0)], self.foot_locations[(1, 0)], self.foot_locations[(2, 0)],
                self.foot_locations[(0, 1)], self.foot_locations[(1, 1)], self.foot_locations[(2, 1)],
                self.foot_locations[(0, 2)], self.foot_locations[(1, 2)], self.foot_locations[(2, 2)],
                self.foot_locations[(0, 3)], self.foot_locations[(1, 3)], self.foot_locations[(2, 3)],
            );
        }
        // #region agent log
        if self.ticks <= 20 || self.ticks % 120 == 0 {
            dbg_log(
                "pre-fix",
                "H6_MODE_PIPELINE_NOT_REACHING_NODE",
                "robot_controller_node.rs:step_after_controller",
                "controller output foot locations and msg counters",
                &format!(
                    "{{\"ticks\":{},\"mode\":\"{:?}\",\"mode_msg_count\":{},\"vel_msg_count\":{},\"fr\":[{:.5},{:.5},{:.5}],\"fl\":[{:.5},{:.5},{:.5}],\"rr\":[{:.5},{:.5},{:.5}],\"rl\":[{:.5},{:.5},{:.5}]}}",
                    self.ticks,
                    self.behavior_state,
                    self.mode_msg_count,
                    self.vel_msg_count,
                    self.foot_locations[(0,0)], self.foot_locations[(1,0)], self.foot_locations[(2,0)],
                    self.foot_locations[(0,1)], self.foot_locations[(1,1)], self.foot_locations[(2,1)],
                    self.foot_locations[(0,2)], self.foot_locations[(1,2)], self.foot_locations[(2,2)],
                    self.foot_locations[(0,3)], self.foot_locations[(1,3)], self.foot_locations[(2,3)]
                ),
            );
        }
        // #endregion

        // IK: foot positions → joint angles
        let local = compute_local_positions(
            &self.foot_locations, 0.3762, 0.0935,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        );
        let angles = compute_all_joint_angles(&local, 0.0, 0.0955, 0.213, 0.213);
        // #region agent log
        if self.ticks <= 20 || self.ticks % 120 == 0 {
            dbg_log(
                "pre-fix",
                "H5_IK_INPUT_DRIFT",
                "robot_controller_node.rs:step_after_ik",
                "ik output joint sample",
                &format!(
                    "{{\"ticks\":{},\"joints\":[{:.5},{:.5},{:.5},{:.5},{:.5},{:.5}]}}",
                    self.ticks, angles[0], angles[1], angles[2], angles[3], angles[4], angles[5]
                ),
            );
        }
        // #endregion

        angles
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🦀 Rust Robot Controller Node starting... [TRACE_CRAWL_COMPARE_V2]");
    println!("   Features: State Machine (REST/TROT/CRAWL/STAND) + IK + Subscriptions\n");

    let ctx = Context::new([], rclrs::InitOptions::new())?;
    let mut executor = ctx.create_basic_executor();
    let node = executor.create_node("robot_controller_rust")?;
    println!("✅ Node created: robot_controller_rust");

    let state = Arc::new(Mutex::new(SharedState::new()));

    // Publisher for joint commands
    let joint_pub: Publisher<Float64MultiArray> =
        node.create_publisher("joint_group_controller/commands")?;
    println!("✅ Publisher: joint_group_controller/commands");

    // Subscription: robot_mode
    let mode_state = state.clone();
    let _mode_sub = node.create_subscription("robot_mode", move |msg: quadropted_msgs_rs::RobotModeCommand| {
        if msg.robot_id == 1 {
            let mut s = mode_state.lock().unwrap();
            let mode_raw = msg.mode.to_cstr().to_string_lossy();
            let mode_str = mode_raw.trim().trim_matches(char::from(0));
            if let Some(new_state) = BehaviorState::from_str(mode_str) {
                s.mode_msg_count += 1;
                // #region agent log
                dbg_log(
                    "pre-fix",
                    "H4_STATE_TRANSITION_RESET",
                    "robot_controller_node.rs:mode_sub",
                    "mode transition request",
                    &format!(
                        "{{\"from\":\"{:?}\",\"to\":\"{:?}\",\"ticks_before\":{},\"mode_str\":\"{}\"}}",
                        s.behavior_state, new_state, s.ticks, mode_str
                    ),
                );
                // #endregion
                println!("[Rust] Mode change: {:?} -> {:?}", s.behavior_state, new_state);
                s.behavior_state = new_state;
                s.ticks = 0;

                // Reset controllers on mode change
                if new_state == BehaviorState::CRAWL {
                    s.crawl_gait.reset();
                }
                // #region agent log
                dbg_log(
                    "pre-fix",
                    "H4_STATE_TRANSITION_RESET",
                    "robot_controller_node.rs:mode_sub_after_reset",
                    "mode transition applied",
                    &format!("{{\"to\":\"{:?}\",\"ticks_after\":{}}}", s.behavior_state, s.ticks),
                );
                // #endregion
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
            // #region agent log
            dbg_log(
                "pre-fix",
                "H2_VELOCITY_MAPPING_LOSS",
                "robot_controller_node.rs:vel_sub_raw",
                "raw robot_velocity",
                &format!(
                    "{{\"lin\":[{:.5},{:.5},{:.5}],\"ang\":[{:.5},{:.5},{:.5}],\"mode\":\"{:?}\"}}",
                    msg.cmd_vel.linear.x, msg.cmd_vel.linear.y, msg.cmd_vel.linear.z,
                    msg.cmd_vel.angular.x, msg.cmd_vel.angular.y, msg.cmd_vel.angular.z,
                    s.behavior_state
                ),
            );
            // #endregion
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
            // #region agent log
            dbg_log(
                "pre-fix",
                "H2_VELOCITY_MAPPING_LOSS",
                "robot_controller_node.rs:vel_sub_mapped",
                "mapped cmd_vel used by controller",
                &format!(
                    "{{\"linear\":[{:.5},{:.5},{:.5}],\"angular\":[{:.5},{:.5},{:.5}]}}",
                    s.cmd_linear[0], s.cmd_linear[1], s.cmd_linear[2],
                    s.cmd_angular[0], s.cmd_angular[1], s.cmd_angular[2]
                ),
            );
            // #endregion
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

    // 60Hz control loop
    let ctrl_state = state.clone();
    let ctrl_pub = joint_pub.clone();
    std::thread::spawn(move || loop {
        let mut s = ctrl_state.lock().unwrap();
        let angles = s.step(-0.25);

        if s.ticks % 120 == 0 {
            println!("[Rust DEBUG] Tick #{} ({:.1}s) {:?} mode, vx={:.3}",
                s.ticks, s.ticks as f64 / 60.0, s.behavior_state, s.cmd_linear[0]);
            if s.behavior_state == BehaviorState::CRAWL {
                let contacts = s.crawl_gait.contacts(s.ticks);
                let phase_idx = s.crawl_gait.phase_index(s.ticks);
                let sub_ticks = s.crawl_gait.subphase_ticks(s.ticks);
                println!(
                    "[RUNTIME_CRAWL_RUST] ticks={} phase={} sub={} contacts=[{},{},{},{}] cmd=[{:.4},{:.4},{:.4}] fr=({:.4},{:.4},{:.4}) fl=({:.4},{:.4},{:.4}) rr=({:.4},{:.4},{:.4}) rl=({:.4},{:.4},{:.4})",
                    s.ticks,
                    phase_idx,
                    sub_ticks,
                    contacts[0], contacts[1], contacts[2], contacts[3],
                    s.cmd_linear[0], s.cmd_linear[1], s.cmd_angular[2],
                    s.foot_locations[(0, 0)], s.foot_locations[(1, 0)], s.foot_locations[(2, 0)],
                    s.foot_locations[(0, 1)], s.foot_locations[(1, 1)], s.foot_locations[(2, 1)],
                    s.foot_locations[(0, 2)], s.foot_locations[(1, 2)], s.foot_locations[(2, 2)],
                    s.foot_locations[(0, 3)], s.foot_locations[(1, 3)], s.foot_locations[(2, 3)],
                );
            }
            let joint_names = [
                "rf_hip", "rf_upper", "rf_lower",
                "lf_hip", "lf_upper", "lf_lower",
                "rh_hip", "rh_upper", "rh_lower",
                "lh_hip", "lh_upper", "lh_lower"
            ];
            for i in 0..12 {
                println!("[Rust DEBUG]   {} = {:.6} rad", joint_names[i], angles[i]);
            }
        }

        let mut msg = Float64MultiArray::default();
        let mut seq = Sequence::new(angles.len());
        for (i, &val) in angles.iter().enumerate() { seq[i] = val; }
        msg.data = seq;
        ctrl_pub.publish(&msg).ok();

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
