//! CmdVelPub — конвертация `geometry_msgs/Twist` → `quadropted_msgs/RobotVelocity`.
//!
//! Логика перенесена из `cmd_vel_pub.cpp` удалённого C++-контроллера: масштаб
//! 0.035 по x, 0.012 по y и экспоненциальное насыщение
//! `k * (1 - exp(-100 * |v * k|))`. Модуль не требует ROS-контекста, поэтому
//! проверяется юнит-тестами; в бинарнике `cmd_vel_pub` остаётся только связка
//! с rclrs.

use geometry_msgs_rs::Twist;

/// Масштаб линейной скорости по x (C++ `multiply_and_limit`).
pub const LINEAR_X_SCALE: f64 = 0.035;
/// Масштаб линейной скорости по y (C++ `multiply_and_limit_y`).
pub const LINEAR_Y_SCALE: f64 = 0.012;
/// Скорость экспоненциального насыщения (C++ `exp(-100.0 * |adjusted|)`).
pub const SATURATION_RATE: f64 = 100.0;
/// Порог «команда движения не нулевая» для verbose-логики (C++ `1e-6`).
pub const VELOCITY_EPS: f64 = 1e-6;
/// `robot_id` в исходящем сообщении (C++ `out->robot_id = 1`).
pub const ROBOT_ID: u16 = 1;

/// Ограничение скорости диапазоном [-1, 1] (C++ `limit`).
pub fn limit(value: f64) -> f64 {
    if value > 1.0 {
        1.0
    } else if value < -1.0 {
        -1.0
    } else {
        value
    }
}

/// Масштабирование с экспоненциальным насыщением (C++ `multiply_and_limit`).
pub fn multiply_and_limit(value: f64, scale: f64) -> f64 {
    let adjusted = value * scale;
    let scaled = scale * (1.0 - (-SATURATION_RATE * adjusted.abs()).exp());
    limit(if value >= 0.0 { scaled } else { -scaled })
}

/// Масштабирование линейной скорости по x.
pub fn multiply_and_limit_x(value: f64) -> f64 {
    multiply_and_limit(value, LINEAR_X_SCALE)
}

/// Масштабирование линейной скорости по y.
pub fn multiply_and_limit_y(value: f64) -> f64 {
    multiply_and_limit(value, LINEAR_Y_SCALE)
}

/// Есть ли в Twist ненулевая компонента (C++ `has_velocity`).
pub fn has_velocity(msg: &Twist) -> bool {
    msg.linear.x.abs() > VELOCITY_EPS
        || msg.linear.y.abs() > VELOCITY_EPS
        || msg.linear.z.abs() > VELOCITY_EPS
        || msg.angular.x.abs() > VELOCITY_EPS
        || msg.angular.y.abs() > VELOCITY_EPS
        || msg.angular.z.abs() > VELOCITY_EPS
}

/// Twist → Twist: x/y масштабируются кривой, z и angular.x/y проходят как есть,
/// angular.z ограничивается (C++ `twist_callback`).
pub fn convert_twist(msg: &Twist) -> Twist {
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
pub struct MotionTracker {
    verbose: bool,
    motion_start_time: f64,
}

impl MotionTracker {
    /// Создать трекер; `verbose` включает логи старта/остановки.
    pub fn new(verbose: bool) -> Self {
        Self {
            verbose,
            motion_start_time: 0.0,
        }
    }

    /// Текущее время старта движения (0.0 — робот стоит).
    pub fn motion_start_time(&self) -> f64 {
        self.motion_start_time
    }

    /// Обновить состояние по факту наличия скорости в текущем сообщении.
    pub fn update(&mut self, has_velocity: bool, now_secs: f64) {
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
    fn velocity_detection_covers_every_component() {
        for set in 0..6 {
            let mut msg = Twist::default();
            match set {
                0 => msg.linear.x = 0.5,
                1 => msg.linear.y = 0.5,
                2 => msg.linear.z = 0.5,
                3 => msg.angular.x = 0.5,
                4 => msg.angular.y = 0.5,
                _ => msg.angular.z = 0.5,
            }
            assert!(has_velocity(&msg), "компонента {set} должна детектироваться");
        }
    }

    #[test]
    fn motion_tracker_starts_and_stops() {
        let mut tracker = MotionTracker::new(false);
        tracker.update(true, 10.0);
        assert_eq!(tracker.motion_start_time(), 10.0);

        tracker.update(true, 11.0);
        assert_eq!(tracker.motion_start_time(), 10.0, "старт не перезаписывается");

        tracker.update(false, 12.5);
        assert_eq!(tracker.motion_start_time(), 0.0, "остановка сбрасывает старт");
    }

    #[test]
    fn motion_tracker_verbose_logs_do_not_change_state() {
        let mut tracker = MotionTracker::new(true);
        tracker.update(true, 1.0);
        assert_eq!(tracker.motion_start_time(), 1.0);
        tracker.update(false, 2.0);
        assert_eq!(tracker.motion_start_time(), 0.0);
    }

    #[test]
    fn tracker_ignores_stop_without_start() {
        let mut tracker = MotionTracker::new(false);
        tracker.update(false, 5.0);
        assert_eq!(tracker.motion_start_time(), 0.0);
    }

    #[test]
    fn multiply_and_limit_is_odd_and_monotonic() {
        for v in [0.01_f64, 0.1, 0.5, 2.0, 5.0] {
            assert!((multiply_and_limit_x(v) + multiply_and_limit_x(-v)).abs() < 1e-15);
            assert!(multiply_and_limit_x(v) > multiply_and_limit_x(v * 0.5));
        }
    }

    #[test]
    fn convert_twist_of_zero_stays_zero() {
        let out = convert_twist(&Twist::default());
        assert_eq!(out.linear.x, 0.0);
        assert_eq!(out.linear.y, 0.0);
        assert_eq!(out.linear.z, 0.0);
        assert_eq!(out.angular.z, 0.0);
    }
}
