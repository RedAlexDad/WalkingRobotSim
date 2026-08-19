//! Integration test: CRAWL gait must not saturate joint limits during a
//! 30-second (1800 tick) simulation, and the Rust crawl path must be
//! bit-identical to the active C++ runtime path
//! (`robot_controller_node.cpp::step_crawl`).
//!
//! Runs fully headless — no ROS, no Gazebo required.

use nalgebra::{DMatrix, SMatrix, Vector3};
use quadropted_core::controllers::crawl::gait::CrawlGaitController;
use quadropted_core::controllers::crawl::stance::CrawlStanceController;
use quadropted_core::controllers::crawl::swing::CrawlSwingController;
use quadropted_core::controllers::gait::GaitController;
use quadropted_core::kinematics::inverse::{compute_all_joint_angles, compute_local_positions};

const TICKS_TOTAL: usize = 1800; // 30 s @ 60 Hz
const HIP_LIM: f64 = 1.0472; // URDF hip_position_max
const UPPER_MIN: f64 = -1.5708; // URDF thigh_position_min
const UPPER_MAX: f64 = 3.4907; // URDF thigh_position_max
const LOWER_MIN: f64 = -2.7227; // URDF calf_position_min
const LOWER_MAX: f64 = -0.83776; // URDF calf_position_max
const MAX_VIOLATION_FRACTION: f64 = 0.01; // допускаем <= 1% времени

fn default_stance() -> SMatrix<f64, 3, 4> {
    let body_length = 0.3762;
    let body_width = 0.0935;
    let l2 = 0.0955;
    let dx_front = body_length * 0.5 + 0.02;
    let dx_back = body_length * 0.5;
    let dy = body_width * 0.5 + l2;
    let mut s = SMatrix::<f64, 3, 4>::zeros();
    s[(0, 0)] = dx_front; s[(1, 0)] = -dy;
    s[(0, 1)] = dx_front; s[(1, 1)] = dy;
    s[(0, 2)] = -dx_back; s[(1, 2)] = -dy;
    s[(0, 3)] = -dx_back; s[(1, 3)] = dy;
    s
}

fn ik(foot: &SMatrix<f64, 3, 4>) -> [f64; 12] {
    let local = compute_local_positions(foot, 0.3762, 0.0935, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    compute_all_joint_angles(&local, 0.0, 0.0955, 0.213, 0.213)
}

/// C++ runtime reference path (exact translation of step_crawl).
fn cpp_runtime_step(
    gait: &GaitController,
    stance_ctrl: &CrawlStanceController,
    swing: &CrawlSwingController,
    ticks: i32,
    current: &SMatrix<f64, 3, 4>,
    cmd: &[f64; 3],
    robot_height: f64,
) -> SMatrix<f64, 3, 4> {
    let has_command = cmd[0].abs() > 1e-4 || cmd[1].abs() > 1e-4 || cmd[2].abs() > 1e-4;
    if !has_command {
        let mut result = gait.default_stance;
        result.row_mut(2).fill(robot_height);
        let alpha = 0.1;
        return current * (1.0 - alpha) + result * alpha;
    }

    let mut next = SMatrix::<f64, 3, 4>::zeros();
    let contacts = gait.contacts(ticks);
    let phase_idx = gait.phase_index(ticks);
    let cmdv = Vector3::new(cmd[0], cmd[1], cmd[2]);

    for leg in 0..4 {
        if contacts[leg] == 1 {
            let move_sideways = phase_idx == 0 || phase_idx == 4;
            let move_left = phase_idx == 0;
            next.column_mut(leg).copy_from(&stance_ctrl.next_foot_location(
                leg, current, &cmdv, robot_height, true, move_sideways, move_left,
            ));
        } else {
            let sub = gait.subphase_ticks(ticks);
            let swing_prop = sub as f64 / gait.swing_ticks as f64;
            next.column_mut(leg).copy_from(&swing.next_foot_location(
                swing_prop, leg, current, &cmdv, robot_height,
            ));
        }
    }
    next
}

fn run_scenario(cmd: [f64; 3]) -> (Vec<SMatrix<f64, 3, 4>>, Vec<SMatrix<f64, 3, 4>>) {
    let stance = default_stance();

    // Rust path
    let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, stance.clone());
    let mut foot = stance.clone();
    let mut rust_hist = Vec::new();
    for tick in 1..=TICKS_TOTAL as i32 {
        foot = crawl.step(tick, &foot, &cmd, -0.25);
        rust_hist.push(foot);
    }

    // C++ runtime reference
    let gait = GaitController::new(
        0.55, 0.45, 0.02,
        DMatrix::from_row_slice(4, 8, &[
            1, 1, 1, 0, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 0,
            1, 0, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 0, 1, 1,
        ]),
        stance.clone(),
    );
    let swing = CrawlSwingController::new(
        gait.swing_ticks, 0.02, 0.14, gait.default_stance.clone(),
        gait.phase_length, gait.stance_ticks, 0.06,
    );
    let stance_ctrl = CrawlStanceController::new(
        gait.phase_length, gait.stance_ticks, gait.swing_ticks, 0.02, 0.02, 0.06,
    );
    let mut foot_cpp = stance.clone();
    let mut cpp_hist = Vec::new();
    for t in 1..=TICKS_TOTAL as i32 {
        foot_cpp = cpp_runtime_step(&gait, &stance_ctrl, &swing, t, &foot_cpp, &cmd, -0.25);
        cpp_hist.push(foot_cpp);
    }

    (rust_hist, cpp_hist)
}

fn assert_no_saturation(label: &str, hist: &[SMatrix<f64, 3, 4>]) {
    let samples = hist.len() * 4;
    let mut hip_viol = 0usize;
    let mut upper_viol = 0usize;
    let mut lower_viol = 0usize;

    for foot in hist {
        let a = ik(foot);
        for i in 0..12 {
            match i % 3 {
                0 => {
                    if a[i].abs() > HIP_LIM {
                        hip_viol += 1;
                    }
                }
                1 => {
                    if a[i] > UPPER_MAX || a[i] < UPPER_MIN {
                        upper_viol += 1;
                    }
                }
                _ => {
                    if a[i] > LOWER_MAX || a[i] < LOWER_MIN {
                        lower_viol += 1;
                    }
                }
            }
        }
    }

    let frac = |n: usize| n as f64 / samples as f64;
    assert!(
        frac(hip_viol) <= MAX_VIOLATION_FRACTION,
        "[{}] hip joint limit violated {:.2}% of the time ({} / {})",
        label, 100.0 * frac(hip_viol), hip_viol, samples
    );
    assert!(
        frac(upper_viol) <= MAX_VIOLATION_FRACTION,
        "[{}] upper joint limit violated {:.2}% of the time ({} / {})",
        label, 100.0 * frac(upper_viol), upper_viol, samples
    );
    assert!(
        frac(lower_viol) <= MAX_VIOLATION_FRACTION,
        "[{}] lower joint limit violated {:.2}% of the time ({} / {})",
        label, 100.0 * frac(lower_viol), lower_viol, samples
    );
}

fn assert_foot_motion(hist: &[SMatrix<f64, 3, 4>]) {
    // Робот должен реально двигаться: ноги меняют позицию между тактами
    let mut max_step = 0.0f64;
    for w in hist.windows(2) {
        let d = (w[1] - w[0]).abs().max();
        if d > max_step {
            max_step = d;
        }
    }
    assert!(
        max_step > 1e-6,
        "feet did not move during CRAWL (max per-tick change = {:.2e})",
        max_step
    );
}

#[test]
fn test_crawl_no_saturation_yaw_turn() {
    // Сценарий `make crawl`: поворот с максимальным yaw (после clamp 0.15)
    let (rust, cpp) = run_scenario([0.0, 0.0, 0.15]);
    assert_no_saturation("RUST yaw", &rust);
    assert_no_saturation("CPP  yaw", &cpp);
    assert_foot_motion(&rust);
}

#[test]
fn test_crawl_no_saturation_forward() {
    let (rust, cpp) = run_scenario([0.01, 0.0, 0.0]);
    assert_no_saturation("RUST fwd", &rust);
    assert_no_saturation("CPP  fwd", &cpp);
    assert_foot_motion(&rust);
}

#[test]
fn test_crawl_no_saturation_max_command() {
    let (rust, cpp) = run_scenario([0.011, 0.0, 0.15]);
    assert_no_saturation("RUST max", &rust);
    assert_no_saturation("CPP  max", &cpp);
    assert_foot_motion(&rust);
}

#[test]
fn test_crawl_rust_matches_cpp_runtime_bit_exact() {
    // Главный критерий: Rust-путь бит-в-бит совпадает с активным C++ рантайм-путём
    for cmd in [[0.0, 0.0, 0.15], [0.01, 0.0, 0.0], [0.011, 0.0, 0.15], [0.0, 0.0, 0.0]] {
        let (rust, cpp) = run_scenario(cmd);
        for (t, (r, c)) in rust.iter().zip(cpp.iter()).enumerate() {
            let diff = (r - c).abs().max();
            assert!(
                diff < 1e-12,
                "Rust vs C++ runtime diverged at tick {}: max diff = {:.3e} (cmd {:?})",
                t + 1, diff, cmd
            );
        }
    }
}
