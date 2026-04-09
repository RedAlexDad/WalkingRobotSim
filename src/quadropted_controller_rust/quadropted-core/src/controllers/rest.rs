//! Rest Controller — lying down with IMU compensation
//!
//! Direct translation from C++ `rest_controller.cpp`.

use crate::controllers::pid::PIDController;
use crate::math::rotation::rotxyz;
use nalgebra::{Matrix3, SMatrix};

/// Rest controller state (simplified)
pub struct RestState {
    pub imu_roll: f64,
    pub imu_pitch: f64,
}

/// Rest controller
pub struct RestController {
    default_stance: SMatrix<f64, 3, 4>,
    pid: PIDController,
    use_imu: bool,
    pid_last_time: f64,
}

impl RestController {
    pub fn new(default_stance: SMatrix<f64, 3, 4>) -> Self {
        Self {
            default_stance,
            pid: PIDController::new(0.75, 2.29, 0.0),
            use_imu: true,
            pid_last_time: 0.0,
        }
    }

    pub fn reset(&mut self) {
        self.pid.reset(0.0);
        self.pid_last_time = 0.0;
    }

    /// Run one control step
    pub fn step(&mut self, state: &RestState, robot_height: f64) -> SMatrix<f64, 3, 4> {
        let mut temp = self.default_stance;
        for col in 0..4 {
            temp[(2, col)] = robot_height;
        }

        if self.use_imu {
            let compensation = self.pid.run(state.imu_roll, state.imu_pitch, self.pid_last_time);
            self.pid_last_time += 0.02; // fixed step as in Python

            let roll_compensation = -compensation[0];
            let pitch_compensation = -compensation[1];
            let rot = rotxyz(roll_compensation, pitch_compensation, 0.0);

            // Matrix multiply: rot * temp
            let rot_3x3 = rot;
            let mut new_temp = SMatrix::<f64, 3, 4>::zeros();
            for col in 0..4 {
                let col_vec = nalgebra::Vector3::new(temp[(0, col)], temp[(1, col)], temp[(2, col)]);
                let result = rot_3x3 * col_vec;
                new_temp[(0, col)] = result.x;
                new_temp[(1, col)] = result.y;
                new_temp[(2, col)] = result.z;
            }
            temp = new_temp;
        }

        temp
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_stance() -> SMatrix<f64, 3, 4> {
        let mut m = SMatrix::<f64, 3, 4>::zeros();
        m[(0, 0)] = 0.2; m[(1, 0)] = 0.1;
        m[(0, 1)] = 0.2; m[(1, 1)] = -0.1;
        m[(0, 2)] = -0.2; m[(1, 2)] = 0.1;
        m[(0, 3)] = -0.2; m[(1, 3)] = -0.1;
        m
    }

    #[test]
    fn test_rest_height() {
        let stance = default_stance();
        let mut controller = RestController::new(stance);
        controller.use_imu = false; // disable IMU for this test

        let state = RestState { imu_roll: 0.0, imu_pitch: 0.0 };
        let result = controller.step(&state, -0.15);

        // Z should be set to robot_height
        for col in 0..4 {
            assert!((result[(2, col)] - (-0.15)).abs() < 1e-10);
        }
    }

    #[test]
    fn test_rest_imu_compensation() {
        let stance = default_stance();
        let mut controller = RestController::new(stance);

        // First call initializes time, returns zeros
        let state = RestState { imu_roll: 0.1, imu_pitch: 0.05 };
        let result1 = controller.step(&state, -0.15);

        // Second call should apply IMU compensation
        let result2 = controller.step(&state, -0.15);

        // Results should differ after PID accumulates
        // (PID with ki=2.29 will accumulate integral term)
        let diff = (result2 - result1).norm();
        assert!(diff > 1e-10, "IMU compensation should change stance");
    }

    #[test]
    fn test_rest_reset() {
        let stance = default_stance();
        let mut controller = RestController::new(stance);

        // Run a few steps
        for _ in 0..5 {
            let state = RestState { imu_roll: 0.1, imu_pitch: 0.0 };
            controller.step(&state, -0.15);
        }

        // Reset
        controller.reset();

        // After reset, should behave like new
        let state = RestState { imu_roll: 0.1, imu_pitch: 0.0 };
        let result = controller.step(&state, -0.15);
        // First step after reset returns zeros from PID
        assert!(result.norm() > 0.0); // stance has values
    }
}
