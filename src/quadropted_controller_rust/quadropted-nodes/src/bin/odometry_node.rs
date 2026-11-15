//! Odometry Node — Rust-порт `odometry_node.cpp` из удалённого C++-контроллера.
//!
//! Publishes `/robot1/odom` (nav_msgs/Odometry) at 50 Hz and optionally TF
//! (odom → base_link) via tf2_msgs/TFMessage, driven by:
//!   - `joint_group_controller/commands` (Float64MultiArray, 12 joints)
//!   - `foot_contact` (quadropted_msgs/RobotFootContact)
//!   - `imu` (sensor_msgs/Imu) — yaw heading + angular velocity
//!   - `robot_velocity` (quadropted_msgs/RobotVelocity) — fallback velocity
//!
//! FK, интегрирование, stall-детект и сборка сообщений живут в
//! `quadropted_nodes::odometry` и покрыты юнит-тестами; здесь — только
//! связка с rclrs.

use quadropted_nodes::odometry::OdomShared;
use quadropted_nodes::params::OdometryParamHandles;
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions};
use std::sync::{Arc, Mutex};
use std::time::Duration;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🦀 Rust Odometry Node starting...");

    // Парсим аргументы процесса (--ros-args -r __ns:=/robot1 от launch), иначе
    // namespace и remappings из launch-файла не применяются (rclrs 0.7).
    let ctx = Context::new(std::env::args(), rclrs::InitOptions::new())?;
    let mut executor = ctx.create_basic_executor();
    let node = executor.create_node("dog_odometry")?;
    // ROS-часы (sim-time из /clock) — нужны для корректного header.stamp,
    // иначе EKF/TF видят нулевой timestamp и «прыжки назад во времени».
    let clock = node.get_clock();

    // Parameters (C++-совместимые). В rclrs override (`-p name:=value`,
    // параметры launch-файла) применяется только при declare_parameter,
    // поэтому каждый параметр объявляется явно, а дескрипторы (структура
    // `param_handles`) живут до конца main: drop снял бы параметры
    // с регистрации и спрятал их из параметр-сервисов.
    let param_handles = OdometryParamHandles::declare(&node)?;
    let params = param_handles.to_params();
    let has_imu_heading = param_handles.has_imu_heading();
    let enable_odom_tf = param_handles.enable_odom_tf();
    let timer_period = params.timer_period();
    println!(
        "✅ Parameters: publish_rate={} Hz, frames={} -> {}, imu_heading={}, odom_tf={}",
        params.publish_rate,
        params.odom_frame_id,
        params.base_frame_id,
        has_imu_heading,
        enable_odom_tf
    );

    let shared = Arc::new(Mutex::new(OdomShared::new(&params)));

    // Publishers
    let odom_pub: Publisher<nav_msgs_rs::Odometry> = node.create_publisher("odom")?;
    let tf_pub: Publisher<tf2_msgs_rs::TFMessage> = node.create_publisher("tf")?;
    // Stall status (как C++ stall_pub_)
    let stall_pub: Publisher<std_msgs_rs::Bool> = node.create_publisher("stall_status")?;
    // Foot markers для RViz (как C++ marker_pub_)
    let marker_pub: Publisher<visualization_msgs_rs::MarkerArray> =
        node.create_publisher("foot_markers")?;
    println!("✅ Publisher: odom, tf, stall_status, foot_markers");

    // Subscription: joint commands (12 angles) — like C++ odometry_node
    let joint_state = shared.clone();
    let _joint_sub = node.create_subscription(
        "joint_group_controller/commands",
        move |msg: std_msgs_rs::Float64MultiArray| {
            let mut s = joint_state.lock().unwrap();
            if !s.apply_joint_command(&msg.data) {
                eprintln!(
                    "[odom] Unexpected number of joint angles: {} (expected 12)",
                    msg.data.len()
                );
            }
        },
    )?;
    println!("✅ Subscription: joint_group_controller/commands");

    // Subscription: foot contacts
    let contact_state = shared.clone();
    let _contact_sub = node.create_subscription(
        "foot_contact",
        move |msg: quadropted_msgs_rs::RobotFootContact| {
            let mut s = contact_state.lock().unwrap();
            s.apply_foot_contact(&msg.contacts);
        },
    )?;
    println!("✅ Subscription: foot_contact");

    // Subscription: IMU — yaw heading + angular velocity
    // ВАЖНО: _imu_sub должен жить на уровне main (как остальные подписки).
    // Если объявить его ВНУТРИ if-блока — он дропнется при выходе из блока,
    // и rclrs уничтожит подписку сразу после создания (graph её не увидит).
    let _imu_sub;
    if has_imu_heading {
        let imu_state = shared.clone();
        _imu_sub = node.create_subscription(
            "imu",
            move |msg: sensor_msgs_rs::Imu| {
                let mut s = imu_state.lock().unwrap();
                let q = nalgebra::Quaternion::new(
                    msg.orientation.w,
                    msg.orientation.x,
                    msg.orientation.y,
                    msg.orientation.z,
                );
                s.apply_imu(
                    &q,
                    msg.angular_velocity.z,
                    [
                        msg.linear_acceleration.x,
                        msg.linear_acceleration.y,
                        msg.linear_acceleration.z,
                    ],
                );
            },
        )?;
        println!("✅ Subscription: imu");
    } else {
        _imu_sub = node.create_subscription("imu", |_msg: sensor_msgs_rs::Imu| {})?;
    }

    // Subscription: commanded velocity (fallback when no contact data)
    let vel_state = shared.clone();
    let _vel_sub = node.create_subscription(
        "robot_velocity",
        move |msg: quadropted_msgs_rs::RobotVelocity| {
            let mut s = vel_state.lock().unwrap();
            s.apply_robot_velocity(
                msg.robot_id,
                [msg.cmd_vel.linear.x, msg.cmd_vel.linear.y],
            );
        },
    )?;
    println!("✅ Subscription: robot_velocity");

    // 50 Hz odometry loop
    let timer_node = node.clone();
    let _timer = timer_node.create_timer_repeating(timer_period, move || {
        let mut s = shared.lock().unwrap();

        // dt из ROS-времени (sim-time), FK, интегрирование и stall-детект
        let now_time = clock.now();
        let (sec, nanosec) = now_time.to_sec_nanosec().unwrap_or((0, 0));
        let now_secs = sec as f64 + nanosec as f64 * 1e-9;
        s.tick(now_secs);

        odom_pub.publish(&s.build_odom(sec, nanosec)).ok();

        // Stall status (как C++ publish_stall_status)
        let mut stall_msg = std_msgs_rs::Bool::default();
        stall_msg.data = s.stall_status();
        stall_pub.publish(&stall_msg).ok();

        // Foot markers для RViz (как C++ publish_markers)
        marker_pub.publish(&s.build_foot_markers(sec, nanosec)).ok();

        // TF broadcast (odom → base_link) — via tf2_msgs/TFMessage like the
        // ROS 2 convention (robot_state_publisher style), since raw tf2_ros
        // bindings are not available in rclrs 0.7.
        if enable_odom_tf {
            tf_pub.publish(&s.build_tf(sec, nanosec)).ok();
        }
    })?;

    println!("✅ 50 Hz odometry loop");
    println!("🚀 Spinning (Ctrl+C to stop)...\n");

    loop {
        let mut spin_opts = SpinOptions::default();
        spin_opts.timeout = Some(Duration::from_millis(1000));
        let _ = executor.spin(spin_opts);
    }
}
