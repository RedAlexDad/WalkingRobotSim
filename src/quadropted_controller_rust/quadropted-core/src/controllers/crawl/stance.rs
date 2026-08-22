//! Crawl Stance Controller
//!
//! Direct translation from C++ `crawl_stance.cpp`.

use crate::math::rotation::rotz;
use nalgebra::{Matrix3, SMatrix, Vector3};

/// Crawl stance controller
pub struct CrawlStanceController {
    phase_length: i32,
    stance_ticks: i32,
    swing_ticks: i32,
    time_step: f64,
    z_error_constant: f64,
    body_shift_y: f64,
}

impl CrawlStanceController {
    pub fn new(phase_length: i32, stance_ticks: i32, swing_ticks: i32, time_step: f64, z_error_constant: f64, body_shift_y: f64) -> Self {
        Self {
            phase_length,
            stance_ticks,
            swing_ticks,
            time_step,
            z_error_constant,
            body_shift_y,
        }
    }

    /// Compute next foot location for a leg in stance
    pub fn next_foot_location(
        &self,
        leg_index: usize,
        state_foot: &SMatrix<f64, 3, 4>,
        cmd_vel: &Vector3<f64>,
        robot_height: f64,
        first_cycle: bool,
        move_sideways: bool,
        move_left: bool,
    ) -> Vector3<f64> {
        let z = state_foot[(2, leg_index)];

        let step_dist_x = cmd_vel.x * (self.phase_length as f64 / self.swing_ticks as f64);
        let shift_factor = if first_cycle { 1 } else { 2 };

        let side_vel = if move_sideways {
            if move_left {
                -(self.body_shift_y * shift_factor as f64) / (self.time_step * self.stance_ticks as f64)
            } else {
                (self.body_shift_y * shift_factor as f64) / (self.time_step * self.stance_ticks as f64)
            }
        } else {
            0.0
        };

        let velocity = Vector3::new(
            -(step_dist_x / 3.0) / (self.time_step * self.stance_ticks as f64),
            side_vel,
            (1.0 / self.z_error_constant) * (robot_height - z),
        );

        let delta_pos = velocity * self.time_step;
        let yaw_delta = -cmd_vel.z * self.time_step;
        let delta_ori = rotz(yaw_delta);

        let foot_location: Vector3<f64> = state_foot.column(leg_index).into();
        delta_ori * foot_location + delta_pos
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_crawl_stance_zero_velocity() {
        let controller = CrawlStanceController::new(200, 27, 173, 0.02, 0.001, 0.02);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        for col in 0..4 {
            foot[(0, col)] = 0.2;
            foot[(2, col)] = -0.25;
        }

        let cmd_vel = Vector3::zeros();
        let result = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, true, false, false);

        // With zero velocity and no sideways, should stay similar
        assert!((result.x - 0.2).abs() < 0.01, "X = {}", result.x);
    }

    #[test]
    fn test_crawl_stance_sideways() {
        let controller = CrawlStanceController::new(200, 27, 173, 0.02, 0.001, 0.02);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        for col in 0..4 {
            foot[(0, col)] = 0.2;
            foot[(2, col)] = -0.25;
        }

        let cmd_vel = Vector3::zeros();
        let result = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, true, true, true);

        // With sideways movement, Y should change
        assert!(result.y.abs() > 1e-10, "Y should change with sideways: {}", result.y);
    }

    #[test]
    fn test_crawl_stance_shift_factor_doubles_sideways_after_first_cycle() {
        // first_cycle=true → shift_factor=1; first_cycle=false → shift_factor=2
        // Боковое смещение должно удвоиться при повторном цикле (как C++ runtime:
        // нода никогда не вызывает step(), поэтому first_cycle всегда true → factor=1)
        let controller = CrawlStanceController::new(200, 27, 173, 0.02, 0.001, 0.02);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        foot[(2, 0)] = -0.25;

        let cmd_vel = Vector3::zeros();
        let r_first = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, true, true, true);
        let r_second = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, false, true, true);

        // Оба отрицательны (движение влево: move_left=true)
        assert!(r_first.y < 0.0, "first cycle move_left should be negative: {}", r_first.y);
        // Второй цикл должен сместить сильнее по модулю (factor=2)
        assert!(
            r_second.y.abs() > r_first.y.abs(),
            "second cycle should shift more: first={} second={}",
            r_first.y, r_second.y
        );
    }

    #[test]
    fn test_crawl_stance_move_left_vs_right() {
        let controller = CrawlStanceController::new(200, 27, 173, 0.02, 0.001, 0.02);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        foot[(2, 0)] = -0.25;

        let cmd_vel = Vector3::zeros();
        let left = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, true, true, true);
        let right = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, true, true, false);

        // move_left → отрицательный y, move_right → положительный y
        assert!(left.y < 0.0, "move_left: {}", left.y);
        assert!(right.y > 0.0, "move_right: {}", right.y);
        // По модулю равны
        assert!((left.y.abs() - right.y.abs()).abs() < 1e-12);
    }

    #[test]
    fn test_crawl_stance_z_tracking() {
        let controller = CrawlStanceController::new(200, 27, 173, 0.02, 0.001, 0.02);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        foot[(2, 0)] = -0.5; // ниже robot_height

        let cmd_vel = Vector3::zeros();
        let result = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, true, false, false);

        // z должен расти к robot_height (-0.25)
        assert!(result.z > -0.5, "z should increase: {}", result.z);
    }

    #[test]
    fn test_crawl_stance_forward_cmd_moves_foot_back() {
        let controller = CrawlStanceController::new(200, 27, 173, 0.02, 0.001, 0.02);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        foot[(0, 0)] = 0.2;
        foot[(2, 0)] = -0.25;

        let cmd_vel = Vector3::new(0.1, 0.0, 0.0);
        let result = controller.next_foot_location(0, &foot, &cmd_vel, -0.25, true, false, false);

        // step_dist_x = 0.1*(200/173)=0.1156; velocity_x=-(0.1156/3)/(0.02*27)=-0.0714
        // delta_x = -0.00143 → нога чуть назад
        assert!(result.x < 0.2, "foot should move back with forward cmd: {}", result.x);
    }
}
