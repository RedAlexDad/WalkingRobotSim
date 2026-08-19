//! Trot Swing Controller
//!
//! Direct translation from C++ `trot_swing.cpp`.

use crate::math::rotation::{rotxyz, rotz};
use nalgebra::{SMatrix, Vector3};

/// Trot swing controller
pub struct TrotSwingController {
    swing_ticks: i32,
    time_step: f64,
    z_leg_lift: f64,
    default_stance: SMatrix<f64, 3, 4>,
    phase_length: i32,
    stance_ticks: i32,
}

impl TrotSwingController {
    pub fn new(
        swing_ticks: i32,
        time_step: f64,
        z_leg_lift: f64,
        default_stance: SMatrix<f64, 3, 4>,
        phase_length: i32,
        stance_ticks: i32,
    ) -> Self {
        Self {
            swing_ticks,
            time_step,
            z_leg_lift,
            default_stance,
            phase_length,
            stance_ticks,
        }
    }

    /// Compute Raibert heuristic touchdown location
    pub fn raibert_touchdown_location(&self, leg_index: usize, cmd_vel: &Vector3<f64>) -> Vector3<f64> {
        // FIX: phase_length * time_step for delta_pos (like Python)
        let total_time = self.phase_length as f64 * self.time_step;
        let delta_pos = Vector3::new(
            cmd_vel.x * total_time,
            cmd_vel.y * total_time,
            0.0,
        );

        // FIX: stance_ticks * time_step for yaw rotation (like Python)
        let theta = self.stance_ticks as f64 * self.time_step * cmd_vel.z;
        let rotation = rotz(theta);

        let default_col: Vector3<f64> = self.default_stance.column(leg_index).into();
        rotation * default_col + delta_pos
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
    ) -> Vector3<f64> {
        assert!(swing_prop >= 0.0 && swing_prop <= 1.0);

        let foot_location: Vector3<f64> = current.column(leg_index).into();
        let swing_h = self.swing_height(swing_prop);
        let touchdown = self.raibert_touchdown_location(leg_index, cmd_vel);

        let time_left = self.time_step * self.swing_ticks as f64 * (1.0 - swing_prop);
        if time_left < 1e-6 {
            return touchdown;
        }

        // velocity * XY_MASK — Z ignored (like Python)
        let velocity = Vector3::new(
            (touchdown.x - foot_location.x) / time_left,
            (touchdown.y - foot_location.y) / time_left,
            0.0,
        );

        let delta_foot = velocity * self.time_step;

        // z_vector = [0, 0, swing_height + robot_height]
        let mut result = foot_location;
        result.z = swing_h + robot_height; // FIX: use passed robot_height
        result += delta_foot;

        result
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
    fn test_swing_height_profile() {
        let controller = TrotSwingController::new(9, 0.02, 0.08, default_stance(), 11, 2);

        // At start: height = 0
        assert!((controller.swing_height(0.0) - 0.0).abs() < 1e-10);
        // At midpoint: height = max
        assert!((controller.swing_height(0.5) - 0.08).abs() < 1e-10);
        // At end: height = 0
        assert!((controller.swing_height(1.0) - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_swing_zero_velocity() {
        let controller = TrotSwingController::new(9, 0.02, 0.08, default_stance(), 11, 2);
        let foot = default_stance();
        let cmd_vel = Vector3::zeros();

        let result = controller.next_foot_location(0.5, 0, &foot, &cmd_vel, -0.25);

        // With zero velocity, should be near default stance with swing height
        let foot_z: f64 = foot[(2, 0)];
        assert!((result.z - (0.08 + (-0.25))).abs() < 0.01, "Z = {}", result.z);
    }

    #[test]
    fn test_raibert_forward_velocity() {
        let stance = default_stance();
        let controller = TrotSwingController::new(9, 0.02, 0.08, stance.clone(), 11, 2);

        let cmd_vel = Vector3::new(0.3, 0.0, 0.0); // Forward velocity
        let touchdown = controller.raibert_touchdown_location(0, &cmd_vel);

        // Touchdown should be ahead of default stance
        let stance_x: f64 = stance[(0, 0)];
        assert!(touchdown.x > stance_x, "Touchdown X = {}, expected > {}", touchdown.x, stance_x);
    }

    #[test]
    fn test_swing_end_returns_touchdown() {
        // swing_prop = 1.0 → time_left ≈ 0 → возвращаем touchdown (ветка time_left < 1e-6)
        let controller = TrotSwingController::new(9, 0.02, 0.08, default_stance(), 11, 2);
        let cmd_vel = Vector3::new(0.3, 0.0, 0.0);
        let result = controller.next_foot_location(1.0, 0, &default_stance(), &cmd_vel, -0.25);
        let td = controller.raibert_touchdown_location(0, &cmd_vel);
        assert!((result.x - td.x).abs() < 1e-12 && (result.y - td.y).abs() < 1e-12);
    }
}
