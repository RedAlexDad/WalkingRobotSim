//! CmdVelPub — Rust-порт `cmd_vel_pub.cpp` из удалённого C++-контроллера.
//!
//! Узел-мост между Nav2/teleop и контроллером: подписывается на
//! `geometry_msgs/msg/Twist` (`cmd_vel`) и публикует
//! `quadropted_msgs/msg/RobotVelocity` (`robot_velocity`), применяя ту же
//! нелинейную кривую, что и C++: масштаб 0.035 по x, 0.012 по y и
//! экспоненциальное насыщение `k * (1 - exp(-100 * |v * k|))`.
//!
//! QoS сохранён как в C++: rclcpp default = KeepLast(10), reliable, volatile.
//! Это же значение является default в rclrs, поэтому QoS явно не задаётся.

use geometry_msgs_rs::Twist;
use quadropted_msgs_rs::RobotVelocity;
use rclrs::{Context, CreateBasicExecutor, Publisher, SpinOptions};
use std::sync::{Arc, Mutex};
use std::time::Duration;

/// Масштаб линейной скорости по x (C++ `multiply_and_limit`).
const LINEAR_X_SCALE: f64 = 0.035;
/// Масштаб линейной скорости по y (C++ `multiply_and_limit_y`).
const LINEAR_Y_SCALE: f64 = 0.012;
/// Скорость экспоненциального насыщения (C++ `exp(-100.0 * |adjusted|)`).
const SATURATION_RATE: f64 = 100.0;
/// Порог «команда движения не нулевая» для verbose-логики (C++ `1e-6`).
const VELOCITY_EPS: f64 = 1e-6;
/// `robot_id` в исходящем сообщении (C++ `out->robot_id = 1`).
const ROBOT_ID: u16 = 1;

/// Ограничение скорости диапазоном [-1, 1] (C++ `limit`).
fn limit(value: f64) -> f64 {
    if value > 1.0 {
        1.0
    } else if value < -1.0 {
        -1.0
    } else {
        value
    }
}

/// Масштабирование с экспоненциальным насыщением (C++ `multiply_and_limit`).
fn multiply_and_limit(value: f64, scale: f64) -> f64 {
    let adjusted = value * scale;
    let scaled = scale * (1.0 - (-SATURATION_RATE * adjusted.abs()).exp());
    limit(if value >= 0.0 { scaled } else { -scaled })
}

fn multiply_and_limit_x(value: f64) -> f64 {
    multiply_and_limit(value, LINEAR_X_SCALE)
}

fn multiply_and_limit_y(value: f64) -> f64 {
    multiply_and_limit(value, LINEAR_Y_SCALE)
}

/// Есть ли в Twist ненулевая компонента (C++ `has_velocity`).
fn has_velocity(msg: &Twist) -> bool {
    msg.linear.x.abs() > VELOCITY_EPS
        || msg.linear.y.abs() > VELOCITY_EPS
        || msg.linear.z.abs() > VELOCITY_EPS
        || msg.angular.x.abs() > VELOCITY_EPS
        || msg.angular.y.abs() > VELOCITY_EPS
        || msg.angular.z.abs() > VELOCITY_EPS
}

/// Twist → Twist: x/y масштабируются кривой, z и angular.x/y проходят как есть,
/// angular.z ограничивается (C++ `twist_callback`).
fn convert_twist(msg: &Twist) -> Twist {
    let mut out = Twist::default();
    out.linear.x = multiply_and_limit_x(msg.linear.x);
    out.linear.y = multiply_and_limit_y(msg.linear.y);
    out.linear.z = msg.linear.z;
    out.angular.x = msg.angular.x;
    out.angular.y = msg.angular.y;
    out.angular.z = limit(msg.angular.z);
    out
}

/// Учёт интервала движения для verbose-лога (C++ `motion_start_time_`).
struct MotionTracker {
    verbose: bool,
    motion_start_time: f64,
}

impl MotionTracker {
    fn new(verbose: bool) -> Self {
        Self {
            verbose,
            motion_start_time: 0.0,
        }
    }

    fn update(&mut self, has_velocity: bool, now_secs: f64) {
        if has_velocity && self.motion_start_time == 0.0 {
            self.motion_start_time = now_secs;
            if self.verbose {
                println!("[cmd_vel_pub] Motion started at: {:.3}", self.motion_start_time);
            }
        }
        if !has_velocity && self.motion_start_time > 0.0 {
            let elapsed = now_secs - self.motion_start_time;
            if self.verbose {
                println!("[cmd_vel_pub] Motion stopped, elapsed: {:.3} sec", elapsed);
            }
            self.motion_start_time = 0.0;
        }
    }
}

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

#[cfg(test)]
mod tests {
    use super::*;

    /// Эталон снят независимым прогоном C++-формулы `cmd_vel_pub.cpp:53-63`
    /// (g++ -O2, glibc libm, `printf("%.17g")`), а не пересчётом из Rust.
    /// Любое расхождение кривой (коэффициент, знак, скорость насыщения)
    /// ломает тест: допуск 1e-12 намного меньше шага изменения коэффициента.
    const GOLDEN_LINEAR_X: &[(f64, f64)] = &[
        (0.0, 0.0),
        (0.001, 0.00012228587488547938),
        (0.01, 0.001203810430985174),
        (0.05, 0.0056190042730777431),
        (0.1, 0.010335916859845031),
        (0.5, 0.028917911979234427),
        (1.0, 0.033943091580218854),
        (-0.05, -0.0056190042730777431),
        (-0.5, -0.028917911979234427),
        (-1.0, -0.033943091580218854),
        (10.0, 0.034999999999999983),
        (-10.0, -0.034999999999999983),
        (1.0e6, 0.035000000000000003),
    ];

    const GOLDEN_LINEAR_Y: &[(f64, f64)] = &[
        (0.0, 0.0),
        (0.01, 0.00014313944565683378),
        (0.1, 0.0013569547593941104),
        (0.5, 0.0054142603668716838),
        (-0.5, -0.0054142603668716838),
        (10.0, 0.011999926269451761),
        (-10.0, -0.011999926269451761),
        (1.0e6, 0.012),
    ];

    fn assert_golden(golden: &[(f64, f64)], f: impl Fn(f64) -> f64, axis: &str) {
        for &(input, expected) in golden {
            let got = f(input);
            assert!(
                (got - expected).abs() <= 1e-12,
                "{axis}: v={input} → {got}, эталон C++ {expected}"
            );
        }
    }

    #[test]
    fn golden_linear_x_matches_cpp_formula() {
        assert_golden(GOLDEN_LINEAR_X, multiply_and_limit_x, "linear.x");
    }

    #[test]
    fn golden_linear_y_matches_cpp_formula() {
        assert_golden(GOLDEN_LINEAR_Y, multiply_and_limit_y, "linear.y");
    }

    #[test]
    fn curve_saturates_at_scale() {
        assert!((multiply_and_limit_x(10.0) - LINEAR_X_SCALE).abs() < 1e-6);
        assert!((multiply_and_limit_x(-10.0) + LINEAR_X_SCALE).abs() < 1e-6);
        assert!((multiply_and_limit_y(10.0) - LINEAR_Y_SCALE).abs() < 1e-6);
    }

    #[test]
    fn limit_clamps_to_unit_range() {
        assert_eq!(limit(2.5), 1.0);
        assert_eq!(limit(-2.5), -1.0);
        assert_eq!(limit(1.0), 1.0);
        assert_eq!(limit(-1.0), -1.0);
        assert_eq!(limit(0.5), 0.5);
        assert_eq!(limit(0.0), 0.0);
    }

    #[test]
    fn convert_twist_passes_through_z_and_angular_xy() {
        let mut msg = Twist::default();
        msg.linear.x = 1.0;
        msg.linear.y = 0.5;
        msg.linear.z = 0.123;
        msg.angular.x = 0.1;
        msg.angular.y = 0.2;
        msg.angular.z = 3.0;

        let out = convert_twist(&msg);

        assert!((out.linear.x - multiply_and_limit_x(1.0)).abs() <= 1e-15);
        assert!((out.linear.y - multiply_and_limit_y(0.5)).abs() <= 1e-15);
        assert_eq!(out.linear.z, 0.123);
        assert_eq!(out.angular.x, 0.1);
        assert_eq!(out.angular.y, 0.2);
        assert_eq!(out.angular.z, 1.0, "angular.z ограничивается limit()");
    }

    #[test]
    fn velocity_detection_threshold() {
        let mut msg = Twist::default();
        assert!(!has_velocity(&msg));

        msg.linear.x = 1e-7;
        assert!(!has_velocity(&msg), "порог C++ — строго больше 1e-6");

        msg.linear.x = 1e-5;
        assert!(has_velocity(&msg));
    }

    #[test]
    fn motion_tracker_starts_and_stops() {
        let mut tracker = MotionTracker::new(false);
        tracker.update(true, 10.0);
        assert_eq!(tracker.motion_start_time, 10.0);

        tracker.update(true, 11.0);
        assert_eq!(tracker.motion_start_time, 10.0, "старт не перезаписывается");

        tracker.update(false, 12.5);
        assert_eq!(tracker.motion_start_time, 0.0, "остановка сбрасывает старт");
    }
}
