//! Odometry State — sliding-window foot-delta filter
//!
//! Direct translation from C++ `odometry_state.cpp`.

use nalgebra::Vector3;

/// Per-leg foot state used by the odometry update.
#[derive(Clone, Copy, Debug, Default)]
pub struct FootState {
    /// Current foot position in body frame (from forward kinematics).
    pub position: Vector3<f64>,
    /// Previous foot position (None until first contact observation).
    pub prev_position: Option<Vector3<f64>>,
    /// Whether the foot is currently in contact with the ground.
    pub contact: bool,
}

/// Odometry state: pose, velocity, sliding-window filter and per-leg foot data.
pub struct OdometryState {
    pub x: f64,
    pub y: f64,
    pub theta: f64,
    pub linear_velocity_x: f64,
    pub linear_velocity_y: f64,
    pub imu_angular_velocity: f64,
    pub imu_linear_acceleration_x: f64,
    pub imu_linear_acceleration_y: f64,
    pub imu_linear_acceleration_z: f64,

    pub filter_window_size: usize,
    delta_x_queue: Vec<f64>,
    delta_y_queue: Vec<f64>,
    sum_delta_x: f64,
    sum_delta_y: f64,

    pub foot_states: [FootState; 4],
    /// Last 12 joint positions (hip/upper/lower × FR/FL/RR/RL).
    pub joint_positions: [f64; 12],

    /// Gazebo clock (sec, nanosec) — informational.
    pub gazebo_clock_sec: i32,
    pub gazebo_clock_nanosec: i32,
    pub encoder_pos: i32,

    /// Stall detection state (как в C++ odometry.hpp).
    pub is_stalled: bool,
    pub stall_consecutive_count: i32,
    /// Stall detection thresholds (как в C++).
    pub stall_window: i32,
    pub stall_ang_vel_threshold: f64,
    pub stall_exit_ang_vel_threshold: f64,
}

impl OdometryState {
    /// Create state with the given sliding-window size (C++ default: 14).
    pub fn new(filter_window_size: usize) -> Self {
        Self {
            x: 0.0,
            y: 0.0,
            theta: 0.0,
            linear_velocity_x: 0.0,
            linear_velocity_y: 0.0,
            imu_angular_velocity: 0.0,
            imu_linear_acceleration_x: 0.0,
            imu_linear_acceleration_y: 0.0,
            imu_linear_acceleration_z: 0.0,
            filter_window_size,
            delta_x_queue: Vec::new(),
            delta_y_queue: Vec::new(),
            sum_delta_x: 0.0,
            sum_delta_y: 0.0,
            foot_states: [FootState::default(); 4],
            joint_positions: [0.0; 12],
            gazebo_clock_sec: 0,
            gazebo_clock_nanosec: 0,
            encoder_pos: 0,
            is_stalled: false,
            stall_consecutive_count: 0,
            stall_window: 20,
            stall_ang_vel_threshold: 0.05,
            stall_exit_ang_vel_threshold: 0.1,
        }
    }

    /// Append a (dx, dy) sample to the sliding window, dropping the oldest
    /// sample when the window is full.
    pub fn append_delta(&mut self, dx: f64, dy: f64) {
        if self.delta_x_queue.len() == self.filter_window_size {
            self.sum_delta_x -= self.delta_x_queue.remove(0);
            self.sum_delta_y -= self.delta_y_queue.remove(0);
        }
        self.delta_x_queue.push(dx);
        self.delta_y_queue.push(dy);
        self.sum_delta_x += dx;
        self.sum_delta_y += dy;
    }

    /// Average of the sliding window; (0, 0) when empty.
    pub fn average_delta(&self) -> (f64, f64) {
        let n = self.delta_x_queue.len();
        if n == 0 {
            return (0.0, 0.0);
        }
        (self.sum_delta_x / n as f64, self.sum_delta_y / n as f64)
    }

    /// Reset all state to zero / defaults.
    pub fn reset(&mut self) {
        self.x = 0.0;
        self.y = 0.0;
        self.theta = 0.0;
        self.linear_velocity_x = 0.0;
        self.linear_velocity_y = 0.0;
        self.imu_angular_velocity = 0.0;
        self.imu_linear_acceleration_x = 0.0;
        self.imu_linear_acceleration_y = 0.0;
        self.imu_linear_acceleration_z = 0.0;
        self.delta_x_queue.clear();
        self.delta_y_queue.clear();
        self.sum_delta_x = 0.0;
        self.sum_delta_y = 0.0;
        self.foot_states = [FootState::default(); 4];
        self.joint_positions = [0.0; 12];
        self.gazebo_clock_sec = 0;
        self.gazebo_clock_nanosec = 0;
        self.encoder_pos = 0;
        // Как в C++ odometry_state.cpp: сброс stall-состояния
        self.is_stalled = false;
        self.stall_consecutive_count = 0;
    }
}

impl Default for OdometryState {
    fn default() -> Self {
        Self::new(14)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_append_and_average() {
        let mut state = OdometryState::new(3);
        assert_eq!(state.average_delta(), (0.0, 0.0));

        state.append_delta(1.0, 2.0);
        state.append_delta(3.0, 4.0);
        assert_eq!(state.average_delta(), (2.0, 3.0));

        state.append_delta(5.0, 6.0);
        assert_eq!(state.average_delta(), (3.0, 4.0));

        // Window full → oldest dropped
        state.append_delta(9.0, 10.0);
        assert_eq!(state.average_delta(), ((3.0 + 5.0 + 9.0) / 3.0, (4.0 + 6.0 + 10.0) / 3.0));
        assert_eq!(state.delta_x_queue.len(), 3);
    }

    #[test]
    fn test_reset() {
        let mut state = OdometryState::new(14);
        state.x = 1.0;
        state.y = 2.0;
        state.theta = 0.5;
        state.append_delta(1.0, 1.0);
        state.foot_states[0].contact = true;

        state.reset();
        assert_eq!(state.x, 0.0);
        assert_eq!(state.theta, 0.0);
        assert_eq!(state.average_delta(), (0.0, 0.0));
        assert!(!state.foot_states[0].contact);
        assert!(state.delta_x_queue.is_empty());
    }
}
