//! Odometry Update — foot-delta odometry integration
//!
//! Direct translation from C++ `odometry_update.cpp`.
//!
//! The update estimates body displacement from the relative motion of
//! contacting feet between ticks, filtered by a sliding window. When no foot
//! has previous contact data, it falls back to commanded linear velocity.

use super::state::OdometryState;

/// Normalize an angle to [-π, π].
pub fn normalize_angle(angle: f64) -> f64 {
    angle.sin().atan2(angle.cos())
}

/// Advance odometry by `dt` seconds.
///
/// `contact_count_coeff` weights how much each contacting foot contributes
/// (C++ default 0.65).
pub fn update_odometry(state: &mut OdometryState, dt: f64, contact_count_coeff: f64) {
    if dt <= 0.0 {
        return;
    }

    let mut delta_x_total = 0.0;
    let mut delta_y_total = 0.0;
    let mut contact_sum = 0.0;
    let mut actual_contacts = 0;

    for foot in state.foot_states.iter_mut() {
        if foot.contact {
            let foot_rel_x = foot.position.x;
            let foot_rel_y = foot.position.y;

            if let Some(prev) = foot.prev_position {
                let delta_x = foot_rel_x - prev.x;
                let delta_y = foot_rel_y - prev.y;

                delta_x_total += delta_x;
                delta_y_total += -delta_y;
                contact_sum += contact_count_coeff;
                actual_contacts += 1;
            }

            foot.prev_position = Some(foot.position);
        }
    }

    let (avg_delta_x, avg_delta_y) = if contact_sum > 0.0 {
        (delta_x_total / contact_sum, delta_y_total / contact_sum)
    } else {
        (state.linear_velocity_x * dt, state.linear_velocity_y * dt)
    };

    state.append_delta(avg_delta_x, avg_delta_y);
    let (avg_x, avg_y) = state.average_delta();

    let cos_theta = state.theta.cos();
    let sin_theta = state.theta.sin();
    state.x += avg_x * cos_theta - avg_y * sin_theta;
    state.y += avg_x * sin_theta + avg_y * cos_theta;
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::odometry::state::OdometryState;
    use nalgebra::Vector3;

    #[test]
    fn test_normalize_angle() {
        assert!((normalize_angle(0.0) - 0.0).abs() < 1e-12);
        assert!((normalize_angle(std::f64::consts::PI) - std::f64::consts::PI).abs() < 1e-12);
        assert!((normalize_angle(3.0 * std::f64::consts::PI) - std::f64::consts::PI).abs() < 1e-12);
        assert!((normalize_angle(-3.0 * std::f64::consts::PI) + std::f64::consts::PI).abs() < 1e-12);
    }

    #[test]
    fn test_update_odometry_foot_contact() {
        let mut state = OdometryState::new(3);
        // Foot 0 moves +0.01 in x between ticks while in contact
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        state.foot_states[0].position = Vector3::new(0.21, -0.14, -0.25);

        update_odometry(&mut state, 0.02, 0.65);

        // delta_x = 0.01 / 0.65 → filtered by single-sample window = same
        assert!((state.x - 0.01 / 0.65).abs() < 1e-12, "x = {}", state.x);
        assert!((state.y - 0.0).abs() < 1e-12, "y = {}", state.y);
    }

    #[test]
    fn test_update_odometry_no_contact_falls_back_to_velocity() {
        let mut state = OdometryState::new(3);
        state.linear_velocity_x = 0.1;
        state.linear_velocity_y = 0.0;

        update_odometry(&mut state, 0.02, 0.65);

        assert!((state.x - 0.1 * 0.02).abs() < 1e-12, "x = {}", state.x);
    }

    #[test]
    fn test_update_odometry_zero_dt_is_noop() {
        let mut state = OdometryState::new(3);
        state.x = 1.0;
        update_odometry(&mut state, 0.0, 0.65);
        assert_eq!(state.x, 1.0);
    }

    #[test]
    fn test_update_odometry_rotation_integration() {
        // With theta = π/2, a +x body displacement maps to +y world displacement
        let mut state = OdometryState::new(1);
        state.theta = std::f64::consts::FRAC_PI_2;
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        state.foot_states[0].position = Vector3::new(0.21, -0.14, -0.25);

        update_odometry(&mut state, 0.02, 0.65);

        let body_dx = 0.01 / 0.65;
        assert!((state.x - 0.0).abs() < 1e-12, "x = {}", state.x);
        assert!((state.y - body_dx).abs() < 1e-12, "y = {}", state.y);
    }
}
