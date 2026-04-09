//! PID Controller for IMU compensation (roll/pitch)
//!
//! Direct translation from C++ `pid_controller.cpp`.

/// PID controller for roll and pitch compensation
pub struct PIDController {
    kp: f64,
    ki: f64,
    kd: f64,
    max_i: f64,
    last_time: f64,
    i_term: [f64; 2],
    d_term: [f64; 2],
    last_error: [f64; 2],
    desired_roll_pitch: [f64; 2],
}

impl PIDController {
    pub fn new(kp: f64, ki: f64, kd: f64) -> Self {
        Self {
            kp,
            ki,
            kd,
            max_i: 1.0,
            last_time: -1.0,
            i_term: [0.0; 2],
            d_term: [0.0; 2],
            last_error: [0.0; 2],
            desired_roll_pitch: [0.0; 2],
        }
    }

    pub fn run(&mut self, roll: f64, pitch: f64, current_time: f64) -> [f64; 2] {
        let error = [
            self.desired_roll_pitch[0] - roll,
            self.desired_roll_pitch[1] - pitch,
        ];

        if self.last_time < 0.0 {
            self.last_time = current_time;
            return [0.0, 0.0];
        }

        let step = current_time - self.last_time;
        if step < 1e-6 {
            return [0.0, 0.0];
        }

        for i in 0..2 {
            self.i_term[i] += error[i] * step;
            self.i_term[i] = self.i_term[i].clamp(-self.max_i, self.max_i);
            self.d_term[i] = (error[i] - self.last_error[i]) / step;
        }

        self.last_time = current_time;
        self.last_error = error;

        let mut result = [0.0; 2];
        for i in 0..2 {
            result[i] = self.kp * error[i] + self.ki * self.i_term[i] + self.kd * self.d_term[i];
        }

        result
    }

    pub fn reset(&mut self, current_time: f64) {
        self.last_time = current_time;
        self.i_term = [0.0; 2];
        self.d_term = [0.0; 2];
        self.last_error = [0.0; 2];
    }

    pub fn set_desired(&mut self, roll: f64, pitch: f64) {
        self.desired_roll_pitch = [roll, pitch];
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pid_initial_output() {
        let mut pid = PIDController::new(0.75, 2.29, 0.0);
        // First call should return zeros
        let result = pid.run(0.0, 0.0, 0.0);
        assert_eq!(result, [0.0, 0.0]);
    }

    #[test]
    fn test_pid_error_response() {
        let mut pid = PIDController::new(0.75, 2.29, 0.0);
        // Initialize time
        pid.run(0.0, 0.0, 0.0);

        // Apply error: actual roll = 0.1, desired = 0.0
        let result = pid.run(0.1, 0.0, 0.02); // 50Hz

        // P term: kp * error = 0.75 * (-0.1) = -0.075
        assert!(
            (result[0] - (-0.075)).abs() < 0.01,
            "PID output: {}, expected ~-0.075",
            result[0]
        );
        assert!((result[1]).abs() < 1e-10, "No pitch error");
    }

    #[test]
    fn test_pid_reset() {
        let mut pid = PIDController::new(0.75, 2.29, 0.0);
        pid.run(0.1, 0.1, 0.0);
        pid.run(0.1, 0.1, 0.02);

        pid.reset(0.0);
        // After reset, i_term should be zero
        let result = pid.run(0.0, 0.0, 0.02);
        // P term only: 0.75 * 0.0 = 0
        assert!((result[0]).abs() < 1e-10);
        assert!((result[1]).abs() < 1e-10);
    }
}
