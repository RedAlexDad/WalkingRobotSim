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
            max_i: 0.2, // C++: static constexpr double max_i_ = 0.2;
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

    #[test]
    fn test_pid_set_desired() {
        let mut pid = PIDController::new(0.75, 2.29, 0.0);
        pid.set_desired(0.2, -0.1);
        pid.reset(0.0);
        pid.run(0.0, 0.0, 0.0); // инициализация last_time
        // error = desired - measured = (0.2, -0.1)
        let result = pid.run(0.0, 0.0, 0.02);
        // P term: kp * 0.2 = 0.15, kp * (-0.1) = -0.075
        assert!((result[0] - 0.15).abs() < 0.01, "P roll: {}", result[0]);
        assert!((result[1] - (-0.075)).abs() < 0.01, "P pitch: {}", result[1]);
    }

    #[test]
    fn test_pid_integral_clamped_to_max_i() {
        // FIX-регрессия: Rust max_i было 1.0, в C++ — 0.2 (static constexpr max_i_ = 0.2).
        // Без clamp'а интегральный член накапливается бесконечно, компенсация
        // уводила корпус в сторону при длительном отклонении.
        let mut pid = PIDController::new(0.75, 2.29, 0.0);
        pid.set_desired(0.0, 0.0);
        pid.reset(0.0);
        pid.run(0.0, 0.0, 0.0); // init last_time

        // Устойчивое отклонение roll = 0.2 (знак: error = desired - roll = -0.2)
        // за много тактов должно насытить интегратор на max_i = 0.2
        let mut t = 0.0;
        let mut last_i_component = 0.0f64;
        for _ in 0..1000 {
            t += 0.02;
            let out = pid.run(0.2, 0.0, t);
            // i_term вносит ki * i_term. i_term сам clamp'ится в [-0.2, 0.2].
            // Проверяем вклад интегратора косвенно: выход без d-члена (kd=0)
            // = kp*error + ki*i_term. При насыщении он не должен превышать
            // kp*0.2 + ki*0.2 = 0.15 + 0.458 = 0.608 по модулю.
            assert!(out[0].abs() < 0.61, "PID out not saturated correctly: {}", out[0]);
            last_i_component = out[0];
        }
        // Интегратор насыщен — выход должен быть стабилен (не расти)
        let out1 = last_i_component;
        let out2 = pid.run(0.2, 0.0, t + 0.02)[0];
        assert!((out2 - out1).abs() < 1e-9, "saturated integral must be constant: {} vs {}", out1, out2);
    }

    #[test]
    fn test_pid_integral_bounded_directly() {
        // Прямая проверка границы интегратора: даже при большом постоянном
        // отклонении выход ограничен (i_term clamp 0.2).
        let mut pid = PIDController::new(0.75, 2.29, 0.0);
        pid.reset(0.0);
        pid.run(0.0, 0.0, 0.0);
        let mut t = 0.0;
        let mut max_abs_out = 0.0f64;
        for _ in 0..500 {
            t += 0.02;
            let out = pid.run(0.5, 0.0, t); // большой roll-отклонение
            max_abs_out = max_abs_out.max(out[0].abs());
        }
        // kp*0.5 + ki*0.2 = 0.375 + 0.458 = 0.833, плюс малый запас
        assert!(max_abs_out < 0.9, "PID output unbounded: {}", max_abs_out);
    }

    #[test]
    fn test_pid_zero_dt_returns_previous() {
        let mut pid = PIDController::new(0.75, 2.29, 0.1);
        pid.reset(0.0);
        pid.run(0.0, 0.0, 0.0);
        let first = pid.run(0.1, 0.0, 0.02);
        // Шаг dt < 1e-6 → возвращаем [0,0] (защита от деления на ~0)
        let zero_dt = pid.run(0.1, 0.0, 0.0200000000001);
        assert_eq!(zero_dt, [0.0, 0.0], "zero dt must return zeros");
        // last_time не должен был обновиться → следующий нормальный шаг считает от 0.02
        let next = pid.run(0.1, 0.0, 0.04);
        assert!(next[0].abs() > 0.0);
        let _ = first;
    }
}
