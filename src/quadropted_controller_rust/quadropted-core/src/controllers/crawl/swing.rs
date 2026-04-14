//! Crawl Swing Controller
//!
//! Direct translation from C++ `crawl_swing.cpp`.

use crate::math::rotation::rotz;
use nalgebra::{SMatrix, Vector3};

/// Crawl swing controller
pub struct CrawlSwingController {
    swing_ticks: i32,
    time_step: f64,
    z_leg_lift: f64,
    default_stance: SMatrix<f64, 3, 4>,
    phase_length: i32,
    stance_ticks: i32,
    body_shift_y: f64,
}

impl CrawlSwingController {
    pub fn new(
        swing_ticks: i32,
        time_step: f64,
        z_leg_lift: f64,
        default_stance: SMatrix<f64, 3, 4>,
        phase_length: i32,
        stance_ticks: i32,
        body_shift_y: f64,
    ) -> Self {
        Self {
            swing_ticks,
            time_step,
            z_leg_lift,
            default_stance,
            phase_length,
            stance_ticks,
            body_shift_y,
        }
    }

    /// Compute Raibert heuristic touchdown location with shift correction
    pub fn raibert_touchdown_location(&self, leg_index: usize, cmd_vel: &Vector3<f64>, shifted_left: bool) -> Vector3<f64> {
        // phase_length * time_step for delta_pos (like Python)
        let total_time = self.phase_length as f64 * self.time_step;
        let delta_pos = Vector3::new(
            cmd_vel.x * total_time,
            cmd_vel.y * total_time,
            0.0,
        );

        // stance_ticks * time_step for yaw rotation (like Python)
        let theta = self.stance_ticks as f64 * self.time_step * cmd_vel.z;
        let rotation = rotz(theta);

        // shift_correction[1] = -body_shift_y if shifted_left else body_shift_y
        let shift_correction = Vector3::new(
            0.0,
            if shifted_left { -self.body_shift_y } else { self.body_shift_y },
            0.0,
        );

        let default_col: Vector3<f64> = self.default_stance.column(leg_index).into();
        rotation * default_col + delta_pos + shift_correction
    }

    /// Compute swing height at given proportion
    pub fn swing_height(&self, swing_prop: f64) -> f64 {
        if swing_prop < 0.5 {
            (swing_prop / 0.5) * self.z_leg_lift
        } else {
            self.z_leg_lift * (1.0 - (swing_prop - 0.5) / 0.5)
        }
    }

    /// Compute next foot location for a leg in swing
    pub fn next_foot_location(
        &self,
        swing_prop: f64,
        leg_index: usize,
        current: &SMatrix<f64, 3, 4>,
        cmd_vel: &Vector3<f64>,
        robot_height: f64,
        first_cycle: bool,
        phase_index: usize,
    ) -> Vector3<f64> {
        assert!(swing_prop >= 0.0 && swing_prop <= 1.0);

        let foot_location: Vector3<f64> = current.column(leg_index).into();
        let swing_h = self.swing_height(swing_prop);

        // shifted_left determined by phase_index (phases 4-7 are shifted left)
        let shifted_left = phase_index >= 4;
        let touchdown = self.raibert_touchdown_location(leg_index, cmd_vel, shifted_left);

        let time_left = self.time_step * self.swing_ticks as f64 * (1.0 - swing_prop);
        if time_left < 1e-6 {
            return touchdown;
        }

        // velocity * [1, 1, 0] — XY mask
        let mut velocity = (touchdown - foot_location) / time_left;
        velocity.z = 0.0;

        let delta_foot = velocity * self.time_step;

        // Keep swing arc around commanded robot height.
        // Without this offset, foot z drifts near zero and IK saturates joints.
        let z_vector = Vector3::new(0.0, 0.0, swing_h + robot_height);

        // foot_location * [1,1,0] + z_vector + delta_foot
        Vector3::new(foot_location.x, foot_location.y, 0.0) + z_vector + delta_foot
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_stance() -> SMatrix<f64, 3, 4> {
        let mut m = SMatrix::<f64, 3, 4>::zeros();
        m[(0, 0)] = 0.2; m[(1, 0)] = 0.1; m[(2, 0)] = -0.25;
        m[(0, 1)] = 0.2; m[(1, 1)] = -0.1; m[(2, 1)] = -0.25;
        m[(0, 2)] = -0.2; m[(1, 2)] = 0.1; m[(2, 2)] = -0.25;
        m[(0, 3)] = -0.2; m[(1, 3)] = -0.1; m[(2, 3)] = -0.25;
        m
    }

    #[test]
    fn test_crawl_swing_height_profile() {
        let controller = CrawlSwingController::new(173, 0.02, 0.08, default_stance(), 200, 27, 0.02);

        assert!((controller.swing_height(0.0) - 0.0).abs() < 1e-10);
        assert!((controller.swing_height(0.5) - 0.08).abs() < 1e-10);
        assert!((controller.swing_height(1.0) - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_crawl_swing_zero_velocity() {
        let controller = CrawlSwingController::new(173, 0.02, 0.08, default_stance(), 200, 27, 0.02);
        let foot = default_stance();
        let cmd_vel = Vector3::zeros();

        let result = controller.next_foot_location(0.5, 0, &foot, &cmd_vel, -0.25, true, 0);

        // With zero velocity, Z should be robot_height + swing_height
        let expected_z = -0.17;
        assert!((result.z - expected_z).abs() < 0.01, "Z = {}, expected {}", result.z, expected_z);
    }

    #[test]
    fn test_crawl_swing_shift_correction() {
        let stance = default_stance();
        let controller = CrawlSwingController::new(173, 0.02, 0.08, stance.clone(), 200, 27, 0.02);

        let cmd_vel = Vector3::zeros();
        let result_left = controller.raibert_touchdown_location(0, &cmd_vel, true);
        let result_right = controller.raibert_touchdown_location(0, &cmd_vel, false);

        // Y should differ by 2 * body_shift_y
        let diff = (result_left.y - result_right.y).abs();
        assert!((diff - 0.04).abs() < 1e-10, "Y diff = {}, expected 0.04", diff);
    }
}
