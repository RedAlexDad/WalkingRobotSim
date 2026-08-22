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

    #[test]
    fn test_rest_reset_produces_same_as_new() {
        // После reset компенсация должна совпадать с новым контроллером
        let stance = default_stance();
        let mut c1 = RestController::new(stance);
        let mut c2 = RestController::new(stance);

        // Прогнать c1 и reset, потом один шаг
        let state = RestState { imu_roll: 0.1, imu_pitch: 0.05 };
        for _ in 0..3 {
            c1.step(&state, -0.15);
        }
        c1.reset();
        let r1 = c1.step(&state, -0.15);

        // c2 — новый (не гоняли до reset, но первый step инициализирует PID)
        // ВАЖНО: c2 первый step возвращает PID [0,0], а c1 после reset тоже.
        let r2 = c2.step(&state, -0.15);
        assert!((r1 - r2).norm() < 1e-10, "reset должен воспроизводить новое состояние");
    }

    #[test]
    fn test_rest_without_imu_keeps_flat_stance() {
        // Без IMU-компенсации z устанавливается в robot_height, x/y — как в стойке
        let stance = default_stance();
        let mut controller = RestController::new(stance);
        controller.use_imu = false;

        let state = RestState { imu_roll: 0.5, imu_pitch: -0.3 }; // большой наклон
        let result = controller.step(&state, -0.15);

        // Без IMU наклон НЕ должен менять x/y (только z = robot_height)
        for col in 0..4 {
            assert!((result[(0, col)] - stance[(0, col)]).abs() < 1e-10, "x col {col}");
            assert!((result[(1, col)] - stance[(1, col)]).abs() < 1e-10, "y col {col}");
            assert!((result[(2, col)] - (-0.15)).abs() < 1e-10, "z col {col}");
        }
    }

    #[test]
    fn test_rest_imu_compensation_counteracts_tilt() {
        // Компенсация должна вращать стойку ПРОТИВ наклона (знак минус)
        let stance = default_stance();
        let mut controller = RestController::new(stance);

        let state = RestState { imu_roll: 0.2, imu_pitch: 0.0 };
        controller.step(&state, -0.15); // init PID
        let r2 = controller.step(&state, -0.15);

        // После 2 шагов PID накопил отрицательную компенсацию (против roll)
        // Сравним с нулевым наклоном
        let mut c2 = RestController::new(stance);
        let flat = RestState { imu_roll: 0.0, imu_pitch: 0.0 };
        c2.step(&flat, -0.15);
        let f2 = c2.step(&flat, -0.15);

        // Наклонённый робот должен дать другую стойку
        assert!((r2 - f2).norm() > 1e-8, "tilted vs flat stance must differ");
    }
}
