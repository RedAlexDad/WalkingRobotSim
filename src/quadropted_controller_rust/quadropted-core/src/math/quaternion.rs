//! Quaternion ↔ Euler conversion utilities.
//!
//! Pure functions extracted from the ROS nodes so they can be unit-tested
//! without an rclrs runtime. Must stay bit-identical with the node code that
//! previously inlined these formulas (odometry_node.rs, robot_controller_node.rs).

use nalgebra::Quaternion;

/// Build a unit quaternion from a yaw angle (rotation about Z).
///
/// Mirrors `quat_from_yaw` used by the odometry node when publishing
/// `odom` pose / TF. Returns a unit quaternion with `w = cos(yaw/2)`.
pub fn quat_from_yaw(yaw: f64) -> Quaternion<f64> {
    let (s, c) = (yaw * 0.5).sin_cos();
    Quaternion::new(c, 0.0, 0.0, s)
}

/// Extract yaw (heading) from a quaternion, in `[-π, π]`.
///
/// Matches the odometry node's inline conversion:
/// ```text
/// siny_cosp = 2*(w*z + x*y)
/// cosy_cosp = 1 - 2*(y² + z²)
/// yaw = atan2(siny_cosp, cosy_cosp)
/// ```
pub fn euler_yaw(q: &Quaternion<f64>) -> f64 {
    let w = q.w;
    let x = q.i;
    let y = q.j;
    let z = q.k;
    let siny_cosp = 2.0 * (w * z + x * y);
    let cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
    siny_cosp.atan2(cosy_cosp)
}

/// Extract roll from a quaternion.
///
/// Matches the controller node's inline conversion:
/// ```text
/// roll = atan2(2*(w*x + y*z), 1 - 2*(x² + y²))
/// ```
pub fn euler_roll(q: &Quaternion<f64>) -> f64 {
    let w = q.w;
    let x = q.i;
    let y = q.j;
    let z = q.k;
    (2.0 * (w * x + y * z)).atan2(1.0 - 2.0 * (x * x + y * y))
}

/// Extract pitch from a quaternion.
///
/// Matches the controller node's inline conversion:
/// ```text
/// pitch = asin(2*(w*y - z*x))
/// ```
pub fn euler_pitch(q: &Quaternion<f64>) -> f64 {
    let w = q.w;
    let x = q.i;
    let y = q.j;
    let z = q.k;
    (2.0 * (w * y - z * x)).asin()
}

/// Normalize an angle to `[-π, π]`.
///
/// Duplicated here (and in `odometry::update`) so IMU heading code does not
/// depend on the odometry module. Kept bit-identical.
pub fn normalize_angle(angle: f64) -> f64 {
    angle.sin().atan2(angle.cos())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn assert_close(a: f64, b: f64, tol: f64) {
        assert!((a - b).abs() < tol, "|{a} - {b}| >= {tol}");
    }

    #[test]
    fn quat_from_yaw_zero_is_identity() {
        let q = quat_from_yaw(0.0);
        assert_close(q.w, 1.0, 1e-12);
        assert_close(q.i, 0.0, 1e-12);
        assert_close(q.j, 0.0, 1e-12);
        assert_close(q.k, 0.0, 1e-12);
    }

    #[test]
    fn quat_from_yaw_pi() {
        let q = quat_from_yaw(std::f64::consts::PI);
        assert_close(q.w, 0.0, 1e-12);
        assert_close(q.k, 1.0, 1e-12);
    }

    #[test]
    fn quat_from_yaw_pi_half_round_trip() {
        let q = quat_from_yaw(std::f64::consts::FRAC_PI_2);
        assert_close(q.k, (std::f64::consts::FRAC_PI_2 / 2.0).sin(), 1e-12);
        assert_close(q.w, (std::f64::consts::FRAC_PI_2 / 2.0).cos(), 1e-12);
    }

    #[test]
    fn euler_yaw_round_trip() {
        for yaw in [-3.0, -1.5, -0.5, 0.0, 0.5, 1.5, 2.0, 3.0] {
            let q = quat_from_yaw(yaw);
            let back = euler_yaw(&q);
            assert_close(normalize_angle(back), normalize_angle(yaw), 1e-12);
        }
    }

    #[test]
    fn euler_roll_pitch_known_rotation() {
        // 30° about X → roll = 30°, pitch = 0°
        let roll = std::f64::consts::FRAC_PI_6;
        let q: Quaternion<f64> = nalgebra::UnitQuaternion::from_axis_angle(&nalgebra::Vector3::x_axis(), roll).into_inner();
        assert_close(euler_roll(&q), roll, 1e-12);
        assert_close(euler_pitch(&q), 0.0, 1e-12);

        // 20° about Y → pitch = 20°, roll = 0°
        let pitch = 20.0f64.to_radians();
        let q: Quaternion<f64> = nalgebra::UnitQuaternion::from_axis_angle(&nalgebra::Vector3::y_axis(), pitch).into_inner();
        assert_close(euler_roll(&q), 0.0, 1e-9);
        assert_close(euler_pitch(&q), pitch, 1e-12);
    }

    #[test]
    fn euler_pitch_pi_half_clamped() {
        // asin domain: pitch 90° is the singularity
        let q: Quaternion<f64> = nalgebra::UnitQuaternion::from_axis_angle(&nalgebra::Vector3::y_axis(), std::f64::consts::FRAC_PI_2).into_inner();
        assert_close(euler_pitch(&q), std::f64::consts::FRAC_PI_2, 1e-12);
    }

    #[test]
    fn euler_components_of_rotxyz() {
        // Build quaternion from combined rotation and check all three eulers
        let roll = 0.2;
        let pitch = -0.1;
        let yaw = 0.5;
        let q_roll: Quaternion<f64> = nalgebra::UnitQuaternion::from_axis_angle(&nalgebra::Vector3::x_axis(), roll).into_inner();
        let q_pitch: Quaternion<f64> = nalgebra::UnitQuaternion::from_axis_angle(&nalgebra::Vector3::y_axis(), pitch).into_inner();
        let q_yaw = quat_from_yaw(yaw);
        // intrinsic order applied to vector: yaw then pitch then roll
        let combined = q_yaw * q_pitch * q_roll;
        assert_close(euler_roll(&combined), roll, 1e-9);
        assert_close(euler_pitch(&combined), pitch, 1e-9);
        assert_close(euler_yaw(&combined), yaw, 1e-9);
    }

    #[test]
    fn normalize_angle_rounds_to_pi_interval() {
        // Нормализация сводит угол к [-π, π]. На границах π ≡ -π численно
        // (atan2(±ε, -1) может вернуть любой из них) — допускаем эквивалентность.
        assert_close(normalize_angle(0.0), 0.0, 1e-12);
        assert!((normalize_angle(std::f64::consts::PI) - std::f64::consts::PI).abs() < 1e-12
            || (normalize_angle(std::f64::consts::PI) + std::f64::consts::PI).abs() < 1e-12);
        assert!((normalize_angle(-std::f64::consts::PI) - std::f64::consts::PI).abs() < 1e-12
            || (normalize_angle(-std::f64::consts::PI) + std::f64::consts::PI).abs() < 1e-12);
        assert!((normalize_angle(3.0 * std::f64::consts::PI) - std::f64::consts::PI).abs() < 1e-12
            || (normalize_angle(3.0 * std::f64::consts::PI) + std::f64::consts::PI).abs() < 1e-12);
        assert!((normalize_angle(-3.0 * std::f64::consts::PI) - std::f64::consts::PI).abs() < 1e-12
            || (normalize_angle(-3.0 * std::f64::consts::PI) + std::f64::consts::PI).abs() < 1e-12);
        // 4.0 рад ≈ 4.0 - 2π = -2.283...
        assert_close(normalize_angle(4.0), -2.283185307179586, 1e-9);
    }
}
