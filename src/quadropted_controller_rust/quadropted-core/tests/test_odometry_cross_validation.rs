//! Integration test: Odometry cross-validation against the C++ reference
//! implementation (odometry_state.cpp / odometry_update.cpp).
//!
//! Runs the same test route (foot contacts + commanded velocity) through both
//! the Rust `quadropted_core::odometry` implementation and a direct C++
//! translation embedded here, and asserts the pose drift stays < 1e-6 over a
//! simulated 10-second route (500 ticks @ 50 Hz).

use nalgebra::Vector3;
use quadropted_core::odometry::state::OdometryState;
use quadropted_core::odometry::update::{normalize_angle, update_odometry};

const TICKS: usize = 500; // 10 s @ 50 Hz

/// Direct C++ translation of update_odometry (odometry_update.cpp),
/// including the stall detection added in feat/elevation-mapping.
struct CppOdom {
    x: f64,
    y: f64,
    theta: f64,
    linear_velocity_x: f64,
    linear_velocity_y: f64,
    imu_angular_velocity: f64,
    window: usize,
    dx_queue: Vec<f64>,
    dy_queue: Vec<f64>,
    sum_dx: f64,
    sum_dy: f64,
    // Stall detection (C++ odometry.hpp / odometry_update.cpp)
    is_stalled: bool,
    stall_consecutive_count: i32,
    stall_window: i32,
    stall_ang_vel_threshold: f64,
    stall_exit_ang_vel_threshold: f64,
}

impl CppOdom {
    fn new(window: usize) -> Self {
        Self {
            x: 0.0, y: 0.0, theta: 0.0,
            linear_velocity_x: 0.0, linear_velocity_y: 0.0,
            imu_angular_velocity: 0.0,
            window, dx_queue: Vec::new(), dy_queue: Vec::new(),
            sum_dx: 0.0, sum_dy: 0.0,
            is_stalled: false,
            stall_consecutive_count: 0,
            stall_window: 20,
            stall_ang_vel_threshold: 0.05,
            stall_exit_ang_vel_threshold: 0.1,
        }
    }

    fn append_delta(&mut self, dx: f64, dy: f64) {
        if self.dx_queue.len() == self.window {
            self.sum_dx -= self.dx_queue.remove(0);
            self.sum_dy -= self.dy_queue.remove(0);
        }
        self.dx_queue.push(dx);
        self.dy_queue.push(dy);
        self.sum_dx += dx;
        self.sum_dy += dy;
    }

    fn average_delta(&self) -> (f64, f64) {
        let n = self.dx_queue.len();
        if n == 0 {
            return (0.0, 0.0);
        }
        (self.sum_dx / n as f64, self.sum_dy / n as f64)
    }

    /// Stall detection — exact translation of C++ odometry_update.cpp
    fn update_stall(&mut self, avg_dx: f64, avg_dy: f64) {
        let delta_mag = (avg_dx * avg_dx + avg_dy * avg_dy).sqrt();
        let legs_moving = delta_mag > 0.0001;
        let has_command =
            self.linear_velocity_x.abs() > 1e-4 || self.linear_velocity_y.abs() > 1e-4;
        let body_still = !has_command && self.imu_angular_velocity.abs() < self.stall_ang_vel_threshold;

        if legs_moving && body_still {
            self.stall_consecutive_count += 1;
            if self.stall_consecutive_count >= self.stall_window {
                self.is_stalled = true;
            }
        } else {
            self.stall_consecutive_count = 0;
            if self.is_stalled && self.imu_angular_velocity.abs() > self.stall_exit_ang_vel_threshold {
                self.is_stalled = false;
            }
        }
    }
}

/// Simulated route: robot walks forward with periodic foot lifts, slight yaw.
struct Route {
    tick: usize,
}

impl Route {
    fn contacts(&self, tick: usize) -> [bool; 4] {
        // Simple crawl-like schedule: one leg swings at a time
        let phase = (tick / 10) % 4;
        let mut c = [true; 4];
        c[phase] = false;
        c
    }

    /// Foot positions in body frame: default stance + slow drift (contacted
    /// feet stay planted in world frame, i.e. move backward in body frame).
    fn foot_positions(&self, tick: usize, contacts: &[bool; 4]) -> [Vector3<f64>; 4] {
        let base: [Vector3<f64>; 4] = [
            Vector3::new(0.2081, -0.14225, -0.25),
            Vector3::new(0.2081, 0.14225, -0.25),
            Vector3::new(-0.1881, -0.14225, -0.25),
            Vector3::new(-0.1881, 0.14225, -0.25),
        ];
        // Body advances 0.01 m/s; planted feet drift backward in body frame
        let advance = 0.01 * tick as f64 / 50.0;
        let mut out = base;
        for i in 0..4 {
            if contacts[i] {
                out[i].x -= advance;
            } else {
                // swinging foot returns toward default
                out[i].x = base[i].x;
            }
        }
        out
    }
}

#[test]
fn test_odometry_cross_validation_10s_route() {
    let mut rust_state = OdometryState::new(14);
    let mut cpp = CppOdom::new(14);
    let route = Route { tick: 0 };
    let dt = 1.0 / 50.0;
    let coeff = 0.65;

    // C++ reference tracks prev positions internally; feed identical inputs.
    // To keep the reference faithful, we re-run the same sequence.
    let mut cpp_prev: [Option<Vector3<f64>>; 4] = [None, None, None, None];

    // Робот движется (не stalled): угловая скорость IMU выше порога stall,
    // иначе и Rust, и C++ заморозят интеграцию.
    rust_state.imu_angular_velocity = 0.2;
    cpp.imu_angular_velocity = 0.2;

    for tick in 0..TICKS {
        let contacts = route.contacts(tick);
        let feet = route.foot_positions(tick, &contacts);

        // Rust update (prev_position kept for non-contacting feet — same as C++)
        for i in 0..4 {
            rust_state.foot_states[i].contact = contacts[i];
            rust_state.foot_states[i].position = feet[i];
        }
        rust_state.linear_velocity_x = 0.01;
        update_odometry(&mut rust_state, dt, coeff);

        // C++ reference update (faithful translation with own prev tracking)
        let mut dx_total = 0.0;
        let mut dy_total = 0.0;
        let mut contact_sum = 0.0;
        for i in 0..4 {
            if contacts[i] {
                if let Some(p) = cpp_prev[i] {
                    dx_total += feet[i].x - p.x;
                    dy_total += -(feet[i].y - p.y);
                    contact_sum += coeff;
                }
                cpp_prev[i] = Some(feet[i]);
            }
            // non-contacting feet keep their prev value (like C++ odometry_update.cpp)
        }
        let (avg_dx, avg_dy) = if contact_sum > 0.0 {
            (dx_total / contact_sum, dy_total / contact_sum)
        } else {
            (0.01 * dt, 0.0)
        };
        // Stall detection (C++ odometry_update.cpp)
        cpp.update_stall(avg_dx, avg_dy);
        if cpp.is_stalled {
            continue;
        }
        cpp.append_delta(avg_dx, avg_dy);
        let (a, b) = cpp.average_delta();
        let (ct, st) = (cpp.theta.cos(), cpp.theta.sin());
        cpp.x += a * ct - b * st;
        cpp.y += a * st + b * ct;
    }

    let dx = (rust_state.x - cpp.x).abs();
    let dy = (rust_state.y - cpp.y).abs();
    assert!(dx < 1e-9, "x drift: rust={:.12} cpp={:.12} diff={:.3e}", rust_state.x, cpp.x, dx);
    assert!(dy < 1e-9, "y drift: rust={:.12} cpp={:.12} diff={:.3e}", rust_state.y, cpp.y, dy);
}

#[test]
fn test_odometry_velocity_fallback() {
    // No contact data → must fall back to commanded velocity (like C++)
    // IMU показывает вращение (> stall-порога), чтобы stall не заморозил интеграцию.
    let mut state = OdometryState::new(14);
    state.linear_velocity_x = 0.1;
    state.imu_angular_velocity = 0.2;
    for _ in 0..500 {
        update_odometry(&mut state, 0.02, 0.65);
    }
    // 500 ticks * 0.02 = 10 s at 0.1 m/s = 1.0 m
    assert!((state.x - 1.0).abs() < 1e-9, "x = {}", state.x);
}

#[test]
fn test_odometry_theta_from_imu_like_input() {
    let mut state = OdometryState::new(14);
    // Simulate IMU yaw = 90°
    state.theta = normalize_angle(std::f64::consts::FRAC_PI_2);
    assert!((state.theta - std::f64::consts::FRAC_PI_2).abs() < 1e-12);
}

#[test]
fn test_odometry_stall_freezes_position() {
    // Ноги движутся (контакт + дрейф), IMU показывает покой → робот застрял.
    // После stall_window отсчётов интеграция останавливается (как в C++).
    let mut state = OdometryState::new(14);
    state.stall_window = 20;

    for tick in 0..100 {
        let contacts = [true, true, true, true];
        for i in 0..4 {
            state.foot_states[i].contact = contacts[i];
            // Ноги дрейфуют вперёд в body frame (тело едет, ноги «отстают»)
            let drift = 0.0005 * tick as f64;
            state.foot_states[i].position =
                nalgebra::Vector3::new(0.2081 - drift, -0.14225 + i as f64 * 0.28, -0.25);
        }
        update_odometry(&mut state, 0.02, 0.65);
    }

    assert!(state.is_stalled, "stall должен сработать при проскальзывании ног");
    // После stall позиция не растёт: зафиксируем значение и убедимся, что оно стабильно
    let frozen_x = state.x;
    let frozen_y = state.y;
    for tick in 100..120 {
        let drift = 0.0005 * tick as f64;
        for i in 0..4 {
            state.foot_states[i].contact = true;
            state.foot_states[i].position =
                nalgebra::Vector3::new(0.2081 - drift, -0.14225 + i as f64 * 0.28, -0.25);
        }
        update_odometry(&mut state, 0.02, 0.65);
    }
    assert!((state.x - frozen_x).abs() < 1e-12, "x должен быть заморожен: {} vs {}", state.x, frozen_x);
    assert!((state.y - frozen_y).abs() < 1e-12, "y должен быть заморожен: {} vs {}", state.y, frozen_y);
}
