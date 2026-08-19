//! Odometry Node — Rust implementation of `quadropted_controller_cpp`'s
//! `odometry_node.cpp`.
//!
//! Publishes `/robot1/odom` (nav_msgs/Odometry) at 50 Hz and optionally TF
//! (odom → base_link) via tf2_msgs/TFMessage, driven by:
//!   - `joint_group_controller/commands` (Float64MultiArray, 12 joints)
//!   - `foot_contact` (quadropted_msgs/RobotFootContact)
//!   - `imu` (sensor_msgs/Imu) — yaw heading + angular velocity
//!   - `robot_velocity` (quadropted_msgs/RobotVelocity) — fallback velocity

use geometry_msgs_rs::{Quaternion, TransformStamped};
use nav_msgs_rs::Odometry;
use quadropted_core::kinematics::forward::{compute_leg_fk_chain, leg_base_positions};
use quadropted_core::odometry::state::OdometryState;
use quadropted_core::odometry::update::{normalize_angle, update_odometry};
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions};
use rosidl_runtime_rs::Sequence;
use std::sync::{Arc, Mutex};
use std::time::Duration;

const BODY_LENGTH: f64 = 0.3762;
const BODY_WIDTH: f64 = 0.0935;
const L1: f64 = 0.0;
const L2: f64 = 0.0955;
const L3: f64 = 0.213;
const L4: f64 = 0.213;

struct OdomShared {
    state: OdometryState,
    last_update: std::time::Instant,
}

impl OdomShared {
    fn new(window: usize) -> Self {
        Self {
            state: OdometryState::new(window),
            last_update: std::time::Instant::now(),
        }
    }
}

fn quat_from_yaw(yaw: f64) -> Quaternion {
    let half = yaw / 2.0;
    Quaternion {
        x: 0.0,
        y: 0.0,
        z: half.sin(),
        w: half.cos(),
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🦀 Rust Odometry Node starting...");

    let ctx = Context::new([], rclrs::InitOptions::new())?;
    let mut executor = ctx.create_basic_executor();
    let node = executor.create_node("dog_odometry")?;

    // Parameters (with C++-compatible defaults)
    let publish_rate = 50u64;
    let has_imu_heading = true;
    let enable_odom_tf = false;
    let filter_window = 14usize;
    let base_frame_id = "base_link".to_string();
    let odom_frame_id = "odom".to_string();

    let shared = Arc::new(Mutex::new(OdomShared::new(filter_window)));

    // Publishers
    let odom_pub: Publisher<Odometry> = node.create_publisher("odom")?;
    let tf_pub: Publisher<tf2_msgs_rs::TFMessage> = node.create_publisher("tf")?;
    println!("✅ Publisher: odom (nav_msgs/Odometry), tf (tf2_msgs/TFMessage)");

    // Subscription: joint commands (12 angles) — like C++ odometry_node
    let joint_state = shared.clone();
    let _joint_sub = node.create_subscription(
        "joint_group_controller/commands",
        move |msg: std_msgs_rs::Float64MultiArray| {
            let mut s = joint_state.lock().unwrap();
            if msg.data.len() != 12 {
                eprintln!("[odom] Unexpected number of joint angles: {} (expected 12)", msg.data.len());
                return;
            }
            for (i, v) in msg.data.iter().enumerate() {
                s.state.joint_positions[i] = *v;
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
            for i in 0..4 {
                s.state.foot_states[i].contact = msg.contacts[i];
            }
        },
    )?;
    println!("✅ Subscription: foot_contact");

    // Subscription: IMU — yaw heading + angular velocity
    if has_imu_heading {
        let imu_state = shared.clone();
        let _imu_sub = node.create_subscription(
            "imu",
            move |msg: sensor_msgs_rs::Imu| {
                let mut s = imu_state.lock().unwrap();
                let (qx, qy, qz, qw) = (msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w);
                // Euler yaw from quaternion (matches C++ odometry_node.cpp)
                let siny_cosp = 2.0 * (qw * qz + qx * qy);
                let cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz);
                let yaw = siny_cosp.atan2(cosy_cosp);
                s.state.theta = normalize_angle(yaw);
                s.state.imu_angular_velocity = -msg.angular_velocity.z;
                // Линейные ускорения (как в C++ dog_odom_callbacks.cpp)
                s.state.imu_linear_acceleration_x = msg.linear_acceleration.x;
                s.state.imu_linear_acceleration_y = msg.linear_acceleration.y;
                s.state.imu_linear_acceleration_z = msg.linear_acceleration.z;
            },
        )?;
        println!("✅ Subscription: imu");
    }

    // Subscription: commanded velocity (fallback when no contact data)
    let vel_state = shared.clone();
    let _vel_sub = node.create_subscription(
        "robot_velocity",
        move |msg: quadropted_msgs_rs::RobotVelocity| {
            if msg.robot_id == 1 {
                let mut s = vel_state.lock().unwrap();
                s.state.linear_velocity_x = msg.cmd_vel.linear.x;
                s.state.linear_velocity_y = msg.cmd_vel.linear.y;
            }
        },
    )?;
    println!("✅ Subscription: robot_velocity");

    // 50 Hz odometry loop
    let timer_node = node.clone();
    let _timer = timer_node.create_timer_repeating(
        Duration::from_micros(1_000_000 / publish_rate),
        move || {
            let mut s = shared.lock().unwrap();

            // Forward kinematics: joints → foot positions
            for i in 0..4 {
                let joints = [
                    s.state.joint_positions[i * 3],
                    s.state.joint_positions[i * 3 + 1],
                    s.state.joint_positions[i * 3 + 2],
                ];
                let base = leg_base_positions(i, BODY_LENGTH, BODY_WIDTH);
                let foot = compute_leg_fk_chain(
                    joints[0], joints[1], joints[2], base.x, base.y, L1, L2, L3, L4,
                );
                s.state.foot_states[i].position = foot;
            }

            // dt from wall clock (odom node is not sim-time driven here)
            let now = std::time::Instant::now();
            let dt = now.duration_since(s.last_update).as_secs_f64();
            s.last_update = now;

            update_odometry(&mut s.state, dt, 0.65);

            // Build Odometry message
            let mut odom = Odometry::default();
            odom.header.frame_id = odom_frame_id.clone().into();
            odom.child_frame_id = base_frame_id.clone().into();
            // header.stamp — leave default (wall time unavailable via rclrs Time without clock)

            odom.pose.pose.position.x = s.state.x;
            odom.pose.pose.position.y = s.state.y;
            odom.pose.pose.position.z = 0.0;
            odom.pose.pose.orientation = quat_from_yaw(s.state.theta);

            odom.twist.twist.linear.x = s.state.linear_velocity_x;
            odom.twist.twist.linear.y = s.state.linear_velocity_y;
            odom.twist.twist.angular.z = s.state.imu_angular_velocity;

            odom_pub.publish(&odom).ok();

            // TF broadcast (odom → base_link) — via tf2_msgs/TFMessage like the
            // ROS 2 convention (robot_state_publisher style), since raw tf2_ros
            // bindings are not available in rclrs 0.7.
            if enable_odom_tf {
                let mut tf_msg = tf2_msgs_rs::TFMessage::default();
                let mut seq = Sequence::new(1);
                let mut ts = TransformStamped::default();
                ts.header.frame_id = odom_frame_id.clone().into();
                ts.child_frame_id = base_frame_id.clone().into();
                ts.transform.translation.x = s.state.x;
                ts.transform.translation.y = s.state.y;
                ts.transform.translation.z = 0.0;
                ts.transform.rotation = quat_from_yaw(s.state.theta);
                seq[0] = ts;
                tf_msg.transforms = seq;
                tf_pub.publish(&tf_msg).ok();
            }
        },
    )?;

    println!("✅ 50 Hz odometry loop");
    println!("🚀 Spinning (Ctrl+C to stop)...\n");

    loop {
        let mut spin_opts = SpinOptions::default();
        spin_opts.timeout = Some(Duration::from_millis(1000));
        let _ = executor.spin(spin_opts);
    }
}
