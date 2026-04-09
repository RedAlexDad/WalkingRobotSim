//! Stand Controller — body position/orientation control
//!
//! Direct translation from C++ `stand_controller.cpp`.
//! Allows manual adjustment of body pose via velocity commands.
//! On stop (zero velocity), smoothly returns to center.

use nalgebra::{Matrix3, SMatrix};

/// Stand controller state
pub struct StandController {
    default_stance: SMatrix<f64, 3, 4>,
    body_velocity_scale: f64,
    body_angular_scale: f64,
    max_linear_velocity: f64,
    max_angular_velocity: f64,
}

/// Body state that can be modified by the controller
pub struct BodyState {
    pub body_local_position: [f64; 3],
    pub body_local_orientation: [f64; 3],
}

impl StandController {
    pub fn new(default_stance: SMatrix<f64, 3, 4>) -> Self {
        Self {
            default_stance,
            body_velocity_scale: 0.01,
            body_angular_scale: 0.005,
            max_linear_velocity: 0.2,
            max_angular_velocity: 0.5,
        }
    }

    /// Run one control step
    /// Returns foot positions (default stance with robot_height applied)
    pub fn run(&self, state: &mut BodyState, robot_height: f64, velocity: &[f64; 3], yaw_rate: &[f64; 3]) -> SMatrix<f64, 3, 4> {
        let mut temp = self.default_stance;
        for col in 0..4 {
            temp[(2, col)] = robot_height;
        }

        let mut linear_vel = *velocity;
        let mut angular_vel = *yaw_rate;

        // Clamp velocities
        for i in 0..3 {
            linear_vel[i] = linear_vel[i].clamp(-self.max_linear_velocity, self.max_linear_velocity);
            angular_vel[i] = angular_vel[i].clamp(-self.max_angular_velocity, self.max_angular_velocity);
        }

        // Check if there's any command
        let has_command = linear_vel.iter().any(|&v| v.abs() > 1e-4)
            || angular_vel.iter().any(|&v| v.abs() > 1e-4);

        if has_command {
            // Active control — accumulate position/orientation
            for i in 0..3 {
                state.body_local_position[i] += linear_vel[i] * self.body_velocity_scale;
                state.body_local_orientation[i] += angular_vel[i] * self.body_angular_scale;
            }
        } else {
            // Stop — smooth return to center (lerp)
            let alpha = 0.05;
            for i in 0..3 {
                state.body_local_position[i] *= 1.0 - alpha;
                state.body_local_orientation[i] *= 1.0 - alpha;
            }
        }

        temp
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_stance() -> SMatrix<f64, 3, 4> {
        let mut m = SMatrix::<f64, 3, 4>::zeros();
        // Simple stance: legs at corners
        m[(0, 0)] = 0.2; m[(1, 0)] = 0.1;
        m[(0, 1)] = 0.2; m[(1, 1)] = -0.1;
        m[(0, 2)] = -0.2; m[(1, 2)] = 0.1;
        m[(0, 3)] = -0.2; m[(1, 3)] = -0.1;
        m
    }

    #[test]
    fn test_stand_initial_stance() {
        let stance = default_stance();
        let controller = StandController::new(stance.clone());
        let mut body = BodyState {
            body_local_position: [0.0; 3],
            body_local_orientation: [0.0; 3],
        };

        let result = controller.run(&mut body, -0.25, &[0.0; 3], &[0.0; 3]);

        // Z should be set to robot_height
        for col in 0..4 {
            assert!((result[(2, col)] - (-0.25)).abs() < 1e-10);
        }

        // Body position should not change (zero velocity)
        for i in 0..3 {
            assert!(body.body_local_position[i].abs() < 1e-6);
        }
    }

    #[test]
    fn test_stand_velocity_control() {
        let stance = default_stance();
        let controller = StandController::new(stance);
        let mut body = BodyState {
            body_local_position: [0.0; 3],
            body_local_orientation: [0.0; 3],
        };

        // Apply velocity: z up = 0.1
        controller.run(&mut body, -0.25, &[0.0, 0.0, 0.1], &[0.0; 3]);

        // body_local_position[2] should increase by 0.1 * 0.01 = 0.001
        assert!(
            (body.body_local_position[2] - 0.001).abs() < 1e-10,
            "Expected 0.001, got {}",
            body.body_local_position[2]
        );
    }

    #[test]
    fn test_stand_stop_return_to_center() {
        let stance = default_stance();
        let controller = StandController::new(stance);
        let mut body = BodyState {
            body_local_position: [0.0, 0.0, 0.05],  // Some offset
            body_local_orientation: [0.0; 3],
        };

        // Zero velocity → should return to center
        controller.run(&mut body, -0.25, &[0.0; 3], &[0.0; 3]);

        // body_local_position[2] should be reduced by 5%
        let expected = 0.05 * 0.95;
        assert!(
            (body.body_local_position[2] - expected).abs() < 1e-10,
            "Expected {}, got {}",
            expected,
            body.body_local_position[2]
        );
    }

    #[test]
    fn test_stand_velocity_clamping() {
        let stance = default_stance();
        let controller = StandController::new(stance);
        let mut body = BodyState {
            body_local_position: [0.0; 3],
            body_local_orientation: [0.0; 3],
        };

        // Apply velocity exceeding max: 1.0 > 0.2
        controller.run(&mut body, -0.25, &[1.0, 0.0, 0.0], &[0.0; 3]);

        // Should be clamped to 0.2, so position change = 0.2 * 0.01 = 0.002
        assert!(
            (body.body_local_position[0] - 0.002).abs() < 1e-10,
            "Expected 0.002 (clamped), got {}",
            body.body_local_position[0]
        );
    }
}
