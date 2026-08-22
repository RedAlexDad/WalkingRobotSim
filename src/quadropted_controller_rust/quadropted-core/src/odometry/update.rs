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

    // Stall detection (как в C++ odometry_update.cpp):
    // Если ноги дают ненулевую дельту, НО робот не получил команду движения
    // И IMU показывает, что корпус не вращается — робот, вероятно, застрял
    // (ноги скользят, корпус стоит).
    //
    // FIX: проверка команды — при прямолинейном движении корпус не вращается
    // (angular_velocity ≈ 0), поэтому критерий только по вращению давал ложное
    // застревание через stall_window отсчётов и замораживал odom
    // (SLAM «белый круг по центру»). Теперь stall срабатывает только если
    // команды движения нет.
    let delta_mag = (avg_delta_x * avg_delta_x + avg_delta_y * avg_delta_y).sqrt();
    let legs_moving = delta_mag > 0.0001;
    let has_command = state.linear_velocity_x.abs() > 1e-4 || state.linear_velocity_y.abs() > 1e-4;
    let body_still = !has_command && state.imu_angular_velocity.abs() < state.stall_ang_vel_threshold;

    if legs_moving && body_still {
        state.stall_consecutive_count += 1;
        if state.stall_consecutive_count >= state.stall_window {
            state.is_stalled = true;
        }
    } else {
        state.stall_consecutive_count = 0;
        if state.is_stalled {
            if state.imu_angular_velocity.abs() > state.stall_exit_ang_vel_threshold {
                state.is_stalled = false;
            }
        }
    }

    if state.is_stalled {
        return;
    }

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

    #[test]
    fn test_stall_detection_stops_integration() {
        // C++ odometry_update.cpp: если ноги движутся, но IMU показывает покой —
        // робот застрял; после stall_window отсчётов интеграция останавливается.
        let mut state = OdometryState::new(3);
        state.stall_window = 5;
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        state.foot_states[0].position = Vector3::new(0.21, -0.14, -0.25);
        // imu_angular_velocity = 0 → body_still = true, legs_moving = true

        for _ in 0..6 {
            state.foot_states[0].prev_position = Some(state.foot_states[0].position);
            state.foot_states[0].position.x += 0.01;
            update_odometry(&mut state, 0.02, 0.65);
        }

        assert!(state.is_stalled, "stall should be detected");
        // Позиция не должна накапливаться после срабатывания stall
        let x_after_stall = state.x;
        for _ in 0..5 {
            state.foot_states[0].prev_position = Some(state.foot_states[0].position);
            state.foot_states[0].position.x += 0.01;
            update_odometry(&mut state, 0.02, 0.65);
        }
        assert!(
            (state.x - x_after_stall).abs() < 1e-12,
            "x should freeze after stall: before={} after={}",
            x_after_stall, state.x
        );

        // Выход из stall при достаточной угловой скорости IMU
        state.imu_angular_velocity = 0.2; // > stall_exit_ang_vel_threshold (0.1)
        update_odometry(&mut state, 0.02, 0.65);
        assert!(!state.is_stalled, "stall should be cleared by IMU motion");
    }

    #[test]
    fn test_no_stall_when_imu_rotating() {
        // При вращении IMU stall не срабатывает (body не still)
        let mut state = OdometryState::new(3);
        state.stall_window = 5;
        state.imu_angular_velocity = 0.2;
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        state.foot_states[0].position = Vector3::new(0.21, -0.14, -0.25);

        for _ in 0..6 {
            state.foot_states[0].prev_position = Some(state.foot_states[0].position);
            state.foot_states[0].position.x += 0.01;
            update_odometry(&mut state, 0.02, 0.65);
        }

        assert!(!state.is_stalled, "no stall when IMU is rotating");
    }

    #[test]
    fn test_no_stall_when_command_given() {
        // FIX-регрессия (SLAM «белый круг»): при прямолинейном движении тело не
        // вращается (angular ≈ 0), поэтому старый критерий (только вращение)
        // давал ложное застревание и замораживал odom. Теперь наличие команды
        // движения (linear_velocity) отменяет stall.
        let mut state = OdometryState::new(3);
        state.stall_window = 5;
        state.linear_velocity_x = 0.1; // робот получил команду движения
        state.imu_angular_velocity = 0.0; // тело едет прямо, не вращается
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        state.foot_states[0].position = Vector3::new(0.21, -0.14, -0.25);

        for _ in 0..10 {
            state.foot_states[0].prev_position = Some(state.foot_states[0].position);
            state.foot_states[0].position.x += 0.01;
            update_odometry(&mut state, 0.02, 0.65);
        }

        assert!(!state.is_stalled, "no stall while commanded to move");
        assert!(state.x > 0.0, "odom должен интегрироваться при команде, x = {}", state.x);
    }

    #[test]
    fn test_stall_exit_requires_above_exit_threshold() {
        // Если робот застрял, выход требует |angular| > stall_exit_ang_vel_threshold.
        // Умеренное вращение между порогами (0.05..0.1) не должно разблокировать.
        let mut state = OdometryState::new(3);
        state.stall_window = 3;
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));

        // Накапливаем stall
        for _ in 0..3 {
            state.foot_states[0].prev_position = Some(state.foot_states[0].position);
            state.foot_states[0].position.x += 0.01;
            update_odometry(&mut state, 0.02, 0.65);
        }
        assert!(state.is_stalled);

        // Вращение ниже exit-порога (0.1) → остаёмся в stall
        state.imu_angular_velocity = 0.07;
        state.foot_states[0].prev_position = Some(state.foot_states[0].position);
        state.foot_states[0].position.x += 0.01;
        update_odometry(&mut state, 0.02, 0.65);
        assert!(state.is_stalled, "below exit threshold must keep stall");

        // Вращение выше exit-порога → выходим
        state.imu_angular_velocity = 0.15;
        update_odometry(&mut state, 0.02, 0.65);
        assert!(!state.is_stalled, "above exit threshold must clear stall");
    }

    #[test]
    fn test_stall_ang_vel_threshold_boundary() {
        // Граница stall_ang_vel_threshold: тело вращается ровно с порогом →
        // |angular| < threshold false → body_still=false → no stall.
        let mut state = OdometryState::new(3);
        state.stall_window = 3;
        state.imu_angular_velocity = state.stall_ang_vel_threshold; // ровно порог
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        for _ in 0..3 {
            state.foot_states[0].prev_position = Some(state.foot_states[0].position);
            state.foot_states[0].position.x += 0.01;
            update_odometry(&mut state, 0.02, 0.65);
        }
        assert!(!state.is_stalled, "exactly at threshold body is considered moving");
    }

    #[test]
    fn test_negative_dt_is_noop() {
        // Отрицательный dt — защита от скачков времени назад (jump back in time)
        let mut state = OdometryState::new(3);
        state.linear_velocity_x = 0.1;
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        state.foot_states[0].position = Vector3::new(0.21, -0.14, -0.25);
        update_odometry(&mut state, -0.02, 0.65);
        assert_eq!(state.x, 0.0);
        assert_eq!(state.stall_consecutive_count, 0);
    }

    #[test]
    fn test_contact_without_prev_position_no_delta() {
        // Первый контакт ноги (нет prev_position) — дельту не считаем,
        // но prev_position должен запомниться для следующего тика.
        let mut state = OdometryState::new(3);
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = None;
        state.foot_states[0].position = Vector3::new(0.21, -0.14, -0.25);
        update_odometry(&mut state, 0.02, 0.65);
        assert_eq!(state.x, 0.0, "no prev → no delta");
        assert!(
            state.foot_states[0].prev_position.is_some(),
            "prev_position must be recorded after first contact"
        );
    }

    #[test]
    fn test_multi_foot_delta_averages() {
        // Две ноги в контакте, каждая сдвигается на 0.01 → сумма / (2 * coeff)
        let mut state = OdometryState::new(3);
        for i in 0..2 {
            state.foot_states[i].contact = true;
            state.foot_states[i].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
            state.foot_states[i].position = Vector3::new(0.21, -0.14, -0.25);
        }
        update_odometry(&mut state, 0.02, 0.65);
        // delta_total = 0.01*2, contact_sum = 0.65*2 → avg = 0.01/0.65
        assert!((state.x - 0.01 / 0.65).abs() < 1e-12, "x = {}", state.x);
    }

    #[test]
    fn test_y_axis_inversion() {
        // В C++ delta_y берётся с обратным знаком (delta_y = -(foot_y - prev_y))
        let mut state = OdometryState::new(1);
        state.foot_states[0].contact = true;
        state.foot_states[0].prev_position = Some(Vector3::new(0.20, -0.14, -0.25));
        // Движение ноги в +y (влево в теле) → тело должно сместиться в -y
        state.foot_states[0].position = Vector3::new(0.20, -0.13, -0.25);
        update_odometry(&mut state, 0.02, 0.65);
        let body_dy = -(0.01) / 0.65;
        assert!((state.y - body_dy).abs() < 1e-12, "y = {} expected {}", state.y, body_dy);
    }
}
