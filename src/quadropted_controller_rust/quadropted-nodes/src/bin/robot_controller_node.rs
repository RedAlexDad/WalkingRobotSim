//! Robot Controller Node — State Machine (REST/TROT/CRAWL/STAND) + IK.
//!
//! ROS 2 integration:
//! - Subscriptions: robot_mode, robot_velocity, imu
//! - Service: robot_behavior_command (sit/up/walk)
//! - Publishers: joint_group_controller/commands, foot_contact
//!
//! Шаг контроллера, переключение режимов, сервис поведения и контакты ног
//! живут в `quadropted_nodes::controller` и покрыты юнит-тестами; здесь —
//! только связка с rclrs.

use quadropted_nodes::controller::{
    SharedState, CONTROL_PERIOD_MS, ROBOT_ID,
};
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions};
use rosidl_runtime_rs::Sequence;
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

/// Текущее время в секундах — для PID-компенсации и сброса регуляторов.
fn now_secs() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
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
    {
        let s = state.lock().unwrap();
        let stance = s.default_stance();
        println!("[Rust] Default stance:");
        for leg in 0..4 {
            let name = ["FR", "FL", "RR", "RL"][leg];
            println!(
                "[Rust]   {}: x={:.4} y={:.4}",
                name,
                stance[(0, leg)],
                stance[(1, leg)]
            );
        }
    }

    // Publisher for joint commands
    let joint_pub: Publisher<std_msgs_rs::Float64MultiArray> =
        node.create_publisher("joint_group_controller/commands")?;
    println!("✅ Publisher: joint_group_controller/commands");

    // Publisher for foot contacts (для odometry — как C++ publish_foot_contacts)
    let contact_pub: Publisher<quadropted_msgs_rs::RobotFootContact> =
        node.create_publisher("foot_contact")?;
    println!("✅ Publisher: foot_contact");

    // Subscription: robot_mode
    let mode_state = state.clone();
    let _mode_sub = node.create_subscription(
        "robot_mode",
        move |msg: quadropted_msgs_rs::RobotModeCommand| {
            if msg.robot_id != ROBOT_ID {
                return;
            }
            let mode_raw = msg.mode.to_cstr().to_string_lossy();
            let mut s = mode_state.lock().unwrap();
            let previous = s.behavior_state();
            match s.apply_mode_command(msg.robot_id, &mode_raw, now_secs()) {
                Some(new_state) => {
                    println!("[Rust] Mode change: {:?} -> {:?}", previous, new_state);
                }
                None => {
                    println!(
                        "[Rust] Ignored unknown mode: '{}'",
                        mode_raw.trim_matches(char::from(0))
                    );
                }
            }
        },
    )?;
    println!("✅ Subscription: robot_mode");

    // Subscription: robot_velocity
    let vel_state = state.clone();
    let _vel_sub = node.create_subscription(
        "robot_velocity",
        move |msg: quadropted_msgs_rs::RobotVelocity| {
            let mut s = vel_state.lock().unwrap();
            s.apply_velocity(
                msg.robot_id,
                [
                    msg.cmd_vel.linear.x,
                    msg.cmd_vel.linear.y,
                    msg.cmd_vel.linear.z,
                ],
                [
                    msg.cmd_vel.angular.x,
                    msg.cmd_vel.angular.y,
                    msg.cmd_vel.angular.z,
                ],
            );
        },
    )?;
    println!("✅ Subscription: robot_velocity");

    // Subscription: imu
    let imu_state = state.clone();
    let _imu_sub = node.create_subscription("imu", move |msg: sensor_msgs_rs::Imu| {
        let mut s = imu_state.lock().unwrap();
        let q = nalgebra::Quaternion::new(
            msg.orientation.w,
            msg.orientation.x,
            msg.orientation.y,
            msg.orientation.z,
        );
        s.apply_imu_quaternion(&q);
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
            let (success, message) = s.behavior_command(&cmd, now_secs());
            resp.success = success;
            resp.message = message.into();
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
        let Some(out) = s.control_tick(now_secs()) else {
            let finished = s.startup_grace() == 0;
            drop(s);
            if finished {
                println!("[Rust] Startup grace period complete, controller active");
            }
            std::thread::sleep(Duration::from_millis(CONTROL_PERIOD_MS));
            continue;
        };

        if let Some(line) = out.debug_line {
            println!("{line}");
        }

        let mut msg = std_msgs_rs::Float64MultiArray::default();
        let mut seq = Sequence::new(out.angles.len());
        for (i, &val) in out.angles.iter().enumerate() {
            seq[i] = val;
        }
        msg.data = seq;
        ctrl_pub.publish(&msg).ok();

        // Публикация контактов ног (для odometry) — как C++ publish_foot_contacts
        let mut contact_msg = quadropted_msgs_rs::RobotFootContact::default();
        contact_msg.contacts = out.contacts;
        contact_pub.publish(&contact_msg).ok();

        drop(s);
        std::thread::sleep(Duration::from_millis(CONTROL_PERIOD_MS)); // 60Hz
    });

    println!("✅ 60Hz control loop with State Machine");
    println!("🚀 Spinning (Ctrl+C to stop)...\n");

    loop {
        let mut spin_opts = SpinOptions::default();
        spin_opts.timeout = Some(Duration::from_millis(1000));
        let _ = executor.spin(spin_opts);
    }
}
