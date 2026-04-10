//! Robot Controller Node — Full Rust implementation with TrotGait
//!
//! Full ROS 2 integration:
//! - TrotGaitController orchestrates stance/swing phases
//! - IK computes joint angles from foot positions
//! - Float64MultiArray publisher for joint_group_controller/commands
//! - Twist subscriber for cmd_vel (future: mode switching)

use rclrs::vendor::example_interfaces::msg::rmw::Float64MultiArray;
use quadropted_core::controllers::trot::gait::TrotGaitController;
use quadropted_core::kinematics::inverse::{compute_local_positions, compute_all_joint_angles};
use nalgebra::SMatrix;
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions};
use rosidl_runtime_rs::Sequence;
use std::sync::{Arc, Mutex};
use std::time::Duration;

struct SharedState {
    ticks: i32,
    foot_locations: SMatrix<f64, 3, 4>,
    trot_gait: TrotGaitController,
    cmd_vel: [f64; 3],
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

        let trot_gait = TrotGaitController::new(0.04, 0.18, 0.02, false, default_stance);

        println!("[Rust] Default stance:");
        for leg in 0..4 {
            let name = ["FR", "FL", "RR", "RL"][leg];
            println!("[Rust]   {}: x={:.4} y={:.4}", name, default_stance[(0, leg)], default_stance[(1, leg)]);
        }

        Self {
            ticks: 0,
            foot_locations: trot_gait.default_stance(),
            trot_gait,
            cmd_vel: [0.05, 0.0, 0.0],  // Walk forward slowly
        }
    }

    fn step(&mut self, robot_height: f64) -> [f64; 12] {
        self.ticks += 1;

        // Always run TrotGait
        self.foot_locations = self.trot_gait.step(
            self.ticks,
            &self.foot_locations,
            &self.cmd_vel,
            robot_height,
        );

        // IK: foot positions → joint angles
        // Clamp angles to safe range
        let local = compute_local_positions(
            &self.foot_locations, 0.3762, 0.0935,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        );
        let mut angles = compute_all_joint_angles(&local, 0.0, 0.0955, 0.213, 0.213);

        // Clamp angles to safe range
        for i in 0..4 {
            angles[i * 3 + 0] = angles[i * 3 + 0].clamp(-0.3, 0.3);
            angles[i * 3 + 1] = angles[i * 3 + 1].clamp(0.5, 1.3);
            angles[i * 3 + 2] = angles[i * 3 + 2].clamp(-2.8, -1.5);
        }

        angles
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🦀 Rust Robot Controller Node starting...");
    println!("   Features: TrotGaitController + IK + Float64MultiArray pub\n");

    let ctx = Context::new([], rclrs::InitOptions::new())?;
    let mut executor = ctx.create_basic_executor();
    let node = executor.create_node("robot_controller_rust")?;
    println!("✅ Node created: robot_controller_rust");

    let state = Arc::new(Mutex::new(SharedState::new()));

    // Publisher for joint commands
    let joint_pub: Publisher<Float64MultiArray> =
        node.create_publisher("joint_group_controller/commands")?;
    println!("✅ Publisher: joint_group_controller/commands");

    // 60Hz control loop
    let ctrl_state = state.clone();
    let ctrl_pub = joint_pub.clone();
    std::thread::spawn(move || loop {
        let mut s = ctrl_state.lock().unwrap();
        let angles = s.step(-0.25);

        if s.ticks % 120 == 0 {
            println!("[Rust DEBUG] Tick #{} ({:.1}s) TROT mode, vx={:.3}",
                s.ticks, s.ticks as f64 / 60.0, s.cmd_vel[0]);
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

    println!("✅ 60Hz control loop with TrotGait + IK");
    println!("🚀 Spinning (Ctrl+C to stop)...\n");

    loop {
        let mut spin_opts = SpinOptions::default();
        spin_opts.timeout = Some(Duration::from_millis(1000));
        let _ = executor.spin(spin_opts);
    }
}
