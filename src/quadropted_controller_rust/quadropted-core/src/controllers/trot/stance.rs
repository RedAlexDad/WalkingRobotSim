//! Trot Stance Controller
//!
//! Direct translation from C++ `trot_stance.cpp`.

use crate::math::rotation::rotxyz;
use nalgebra::{Matrix3, SMatrix, Vector3};

/// Trot stance controller
pub struct TrotStanceController {
    phase_length: i32,
    stance_ticks: i32,
    swing_ticks: i32,
    time_step: f64,
    z_error_constant: f64,
}

impl TrotStanceController {
    pub fn new(phase_length: i32, stance_ticks: i32, swing_ticks: i32, time_step: f64, z_error_constant: f64) -> Self {
        Self {
            phase_length,
            stance_ticks,
            swing_ticks,
            time_step,
            z_error_constant,
        }
    }

    /// Compute position delta for a leg in stance
    pub fn position_delta(&self, leg_index: usize, state_foot: &SMatrix<f64, 3, 4>, cmd_vel: &Vector3<f64>, robot_height: f64) -> Vector3<f64> {
        let z = state_foot[(2, leg_index)]; // FIX: use leg_index, not 0

        let step_dist_x = cmd_vel.x * (self.phase_length as f64 / self.swing_ticks as f64);
        let step_dist_y = cmd_vel.y * (self.phase_length as f64 / self.swing_ticks as f64);

        let velocity = Vector3::new(
            -(step_dist_x / 4.0) / (self.time_step * self.stance_ticks as f64),
            -(step_dist_y / 4.0) / (self.time_step * self.stance_ticks as f64),
            (1.0 / self.z_error_constant) * (robot_height - z),
        );

        velocity * self.time_step
    }

    /// Compute next foot location for a leg in stance
    pub fn next_foot_location(&self, leg_index: usize, state_foot: &SMatrix<f64, 3, 4>, cmd_vel: &Vector3<f64>, robot_height: f64) -> Vector3<f64> {
        let foot_location: Vector3<f64> = state_foot.column(leg_index).into();
        let delta_pos = self.position_delta(leg_index, state_foot, cmd_vel, robot_height);

        // rotxyz(roll, pitch, yaw) — cmd_vel = [roll_rate, pitch_rate, yaw_rate]
        let delta_ori = rotxyz(
            -cmd_vel.x * self.time_step,
            -cmd_vel.y * self.time_step,
            -cmd_vel.z * self.time_step,
        );

        delta_ori * foot_location + delta_pos
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stance_zero_velocity() {
        let controller = TrotStanceController::new(11, 2, 9, 0.02, 0.001);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        // Set reasonable foot positions
        for col in 0..4 {
            foot[(0, col)] = 0.2;
            foot[(2, col)] = -0.25;
        }

        let cmd_vel = Vector3::zeros();
        let result = controller.next_foot_location(0, &foot, &cmd_vel, -0.25);

        // With zero velocity and foot at robot_height, should stay similar
        let foot_location: Vector3<f64> = foot.column(0).into();
        assert!((result.z - foot_location.z).abs() < 0.01, "Z = {}", result.z);
    }

    #[test]
    fn test_stance_z_tracking() {
        let controller = TrotStanceController::new(11, 2, 9, 0.02, 0.001);
        let mut foot = SMatrix::<f64, 3, 4>::zeros();
        for col in 0..4 {
            foot[(0, col)] = 0.2;
            foot[(2, col)] = -0.5; // Foot too low
        }

        let cmd_vel = Vector3::zeros();
        let result = controller.next_foot_location(0, &foot, &cmd_vel, -0.25);

        // Z should move toward robot_height (-0.25)
        assert!(result.z > -0.5, "Z should increase: {}", result.z);
    }
}
