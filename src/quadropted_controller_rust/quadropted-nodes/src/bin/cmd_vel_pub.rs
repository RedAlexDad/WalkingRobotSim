//! CmdVelPub — узел-мост между Nav2/teleop и контроллером.
//!
//! Подписывается на `geometry_msgs/msg/Twist` (`cmd_vel`) и публикует
//! `quadropted_msgs/msg/RobotVelocity` (`robot_velocity`). Вся конвертация
//! (кривая 0.035/0.012, насыщение, ограничение angular.z) живёт в
//! `quadropted_nodes::cmd_vel` и покрыта юнит-тестами; здесь — только связка
//! с rclrs.
//!
//! QoS сохранён как в C++: rclcpp default = KeepLast(10), reliable, volatile.
//! Это же значение является default в rclrs, поэтому QoS явно не задаётся.

use geometry_msgs_rs::Twist;
use quadropted_msgs_rs::RobotVelocity;
use quadropted_nodes::cmd_vel::{convert_twist, has_velocity, MotionTracker, ROBOT_ID};
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions};
use std::sync::{Arc, Mutex};
use std::time::Duration;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🦀 Rust CmdVelPub node starting...");

    // Аргументы процесса (--ros-args -r __ns:=/robot1) — иначе namespace
    // и remapping из launch не применятся (rclrs 0.7).
    let ctx = Context::new(std::env::args(), rclrs::InitOptions::new())?;
    let mut executor = ctx.create_basic_executor();
    let node = executor.create_node("cmd_vel_pub")?;
    // ROS-часы (sim-time из /clock) — как this->now() в C++.
    let clock = node.get_clock();

    // C++: declare_parameter("verbose", false). В rclrs CLI-override читается
    // только при объявлении параметра: use_undeclared_parameters().get()
    // возвращает None, поэтому override_map до объявления недоступен.
    // Дескриптор держим до конца main: MandatoryParameter::drop снимает
    // параметр с регистрации, и он пропал бы из параметр-сервисов.
    let verbose_param = node
        .declare_parameter::<bool>("verbose")
        .default(false)
        .mandatory()?;
    let verbose = verbose_param.get();

    let robot_vel_pub: Publisher<RobotVelocity> = node.create_publisher("robot_velocity")?;
    println!("✅ Publisher: robot_velocity");

    let tracker = Arc::new(Mutex::new(MotionTracker::new(verbose)));
    let _cmd_vel_sub = node.create_subscription("cmd_vel", move |msg: Twist| {
        let (sec, nanosec) = clock.now().to_sec_nanosec().unwrap_or((0, 0));
        let now_secs = sec as f64 + nanosec as f64 * 1e-9;
        tracker
            .lock()
            .unwrap()
            .update(has_velocity(&msg), now_secs);

        let mut out = RobotVelocity::default();
        out.robot_id = ROBOT_ID;
        out.cmd_vel = convert_twist(&msg);
        if let Err(err) = robot_vel_pub.publish(&out) {
            eprintln!("[cmd_vel_pub] publish failed: {err}");
        }
    })?;
    println!("✅ Subscription: cmd_vel");
    println!("🚀 Spinning (Ctrl+C to stop)...\n");

    loop {
        let mut spin_opts = SpinOptions::default();
        spin_opts.timeout = Some(Duration::from_millis(1000));
        let _ = executor.spin(spin_opts);
    }
}
