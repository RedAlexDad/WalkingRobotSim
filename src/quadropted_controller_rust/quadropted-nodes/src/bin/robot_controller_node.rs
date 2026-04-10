//! Robot Controller Node — Rust implementation
//!
//! Full ROS 2 integration with proper foot position computation matching C++:
//! - ASYMMETRIC default stance (like C++: dx_front=0.2081, dx_back=0.1881, dy=0.14225)
//! - IK computes joint angles from foot positions
//! - Float64MultiArray publisher for joint_group_controller/commands
//! - Twist subscriber for cmd_vel

use rclrs::vendor::example_interfaces::msg::rmw::Float64MultiArray;
use geometry_msgs_rs::Twist;
use quadropted_core::kinematics::inverse::{compute_local_positions, compute_all_joint_angles};
use quadropted_core::state::behavior::BehaviorState;
use nalgebra::SMatrix;
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions, Subscription};
use rosidl_runtime_rs::Sequence;
use std::sync::{Arc, Mutex};
use std::time::Duration;

struct SharedState {
    behavior_state: BehaviorState,
    foot_locations: SMatrix<f64, 3, 4>,
    body_local_position: [f64; 3],
    body_local_orientation: [f64; 3],
    ticks: u64,
}

impl SharedState {
    fn new() -> Self {
        // Default stance — ASYMMETRIC like C++ robot_controller_node.cpp:
        // dx_front = body[0]*0.5 + 0.02 = 0.2081 (2cm forward shift!)
        // dx_back  = body[0]*0.5 + 0.0  = 0.1881
        // dy       = body[1]*0.5 + legs[1] = 0.04675 + 0.0955 = 0.14225 (includes l2 offset!)
        let body_length = 0.3762;
        let body_width = 0.0935;
        let l2 = 0.0955;
        
        let dx_front = body_length * 0.5 + 0.02;  // 0.2081
        let dx_back = body_length * 0.5;           // 0.1881
        let dy = body_width * 0.5 + l2;            // 0.14225
        
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        // C++ order: FR=(dx_front,-dy), FL=(dx_front,dy), RR=(-dx_back,-dy), RL=(-dx_back,dy)
        foot[(0, 0)] = dx_front; foot[(1, 0)] = -dy;  // FR
        foot[(0, 1)] = dx_front; foot[(1, 1)] = dy;   // FL
        foot[(0, 2)] = -dx_back; foot[(1, 2)] = -dy;  // RR
        foot[(0, 3)] = -dx_back; foot[(1, 3)] = dy;   // RL
        
        println!("[Rust] Default stance (asymmetric, like C++):");
        println!("[Rust]   FR: x={:.4} y={:.4}", foot[(0, 0)], foot[(1, 0)]);
        println!("[Rust]   FL: x={:.4} y={:.4}", foot[(0, 1)], foot[(1, 1)]);
        println!("[Rust]   RR: x={:.4} y={:.4}", foot[(0, 2)], foot[(1, 2)]);
        println!("[Rust]   RL: x={:.4} y={:.4}", foot[(0, 3)], foot[(1, 3)]);
        
        // Verify IK returns reasonable angles
        let local = compute_local_positions(
            &foot, body_length, body_width,
            0.0, 0.0, 0.0,  // body_local_position
            0.0, 0.0, 0.0,  // body_local_orientation
        );
        let angles = compute_all_joint_angles(&local, 0.0, l2, 0.213, 0.213);
        println!("[Rust] IK angles for standing pose:");
        for i in 0..12 {
            print!("{:.4} ", angles[i]);
            if (i + 1) % 3 == 0 {
                println!();  // New line after each leg
            }
        }

        Self {
            behavior_state: BehaviorState::Trot,
            foot_locations: foot,
            body_local_position: [0.0; 3],
            body_local_orientation: [0.0; 3],
            ticks: 0,
        }
    }
    
    fn compute_joint_angles(&self) -> [f64; 12] {
        let local = compute_local_positions(
            &self.foot_locations, 0.3762, 0.0935,
            self.body_local_position[0], self.body_local_position[1], self.body_local_position[2],
            self.body_local_orientation[0], self.body_local_orientation[1], self.body_local_orientation[2],
        );
        compute_all_joint_angles(&local, 0.0, 0.0955, 0.213, 0.213)
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🦀 Rust Robot Controller Node starting...");
    println!("   Features: Twist sub + Float64MultiArray pub + 60Hz IK\n");

    let ctx = Context::new([], rclrs::InitOptions::new())?;
    let mut executor = ctx.create_basic_executor();
    let node = executor.create_node("robot_controller_rust")?;
    println!("✅ Node created: robot_controller_rust");

    let state = Arc::new(Mutex::new(SharedState::new()));

    // Twist subscriber via geometry_msgs_rs (custom bindings)
    {
        let state = state.clone();
        let _sub: Subscription<Twist> = node.create_subscription(
            "robot1/cmd_vel",
            move |msg: Twist| {
                let mut s = state.lock().unwrap();
                s.body_local_position[0] += msg.linear.x * 0.01;
                s.body_local_position[1] += msg.linear.y * 0.01;
                s.body_local_orientation[2] += msg.angular.z * 0.005;
            },
        )?;
    }
    println!("✅ Subscriber: robot1/cmd_vel (geometry_msgs/Twist via geometry_msgs_rs)");

    // Publisher for joint commands
    let joint_pub: Publisher<Float64MultiArray> =
        node.create_publisher("joint_group_controller/commands")?;
    println!("✅ Publisher: joint_group_controller/commands");

    // 60Hz control loop
    let ctrl_state = state.clone();
    let ctrl_pub = joint_pub.clone();
    std::thread::spawn(move || loop {
        let mut s = ctrl_state.lock().unwrap();
        s.ticks += 1;
        let angles = s.compute_joint_angles();
        
        // DEBUG: Print joint angles every 2 seconds
        if s.ticks % 120 == 0 {
            println!("[Rust DEBUG] Tick #{} ({:.1}s) mode={:?}",
                s.ticks, s.ticks as f64 / 60.0, s.behavior_state);
            let joint_names = [
                "rf_hip", "rf_upper", "rf_lower",
                "lf_hip", "lf_upper", "lf_lower",
                "rh_hip", "rh_upper", "rh_lower",
                "lh_hip", "lh_upper", "lh_lower"
            ];
            for i in 0..12 {
                println!("[Rust DEBUG]   {} = {:.6} rad", joint_names[i], angles[i]);
            }
            println!("[Rust DEBUG] === END DEBUG ===");
        }
        
        let mut msg = Float64MultiArray::default();
        let mut seq = Sequence::new(angles.len());
        for (i, &val) in angles.iter().enumerate() { seq[i] = val; }
        msg.data = seq;
        ctrl_pub.publish(&msg).ok();
        
        drop(s);
        std::thread::sleep(Duration::from_millis(16)); // 60Hz
    });

    println!("✅ 60Hz control loop with IK");
    println!("🚀 Spinning (Ctrl+C to stop)...\n");

    loop {
        let mut spin_opts = SpinOptions::default();
        spin_opts.timeout = Some(Duration::from_millis(1000));
        let _ = executor.spin(spin_opts);
    }
}
