//! Cross-validation tests: Rust vs real C++ execution
//!
//! Runs the C++ cross-validation harness binary
//! (`quadropted_controller_cpp/test/cpp_xval_harness.cpp`, built by colcon
//! into `build/quadropted_controller_cpp/cpp_xval_harness`) and compares its
//! JSON output with the Rust implementation. This validates mathematical
//! equivalence of every public API against the *actual* C++ code that runs
//! in the simulator (not just re-derived formulas).

use std::path::PathBuf;
use std::process::Command;

// ── Harness discovery ────────────────────────────────────────
// Priority: $CPP_XVAL_HARNESS → colcon build dir (host + container) →
//           colcon install dir
fn harness_path() -> PathBuf {
    if let Ok(p) = std::env::var("CPP_XVAL_HARNESS") {
        return PathBuf::from(p);
    }
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR")); // .../quadropted-core
    let repo_root = manifest
        .parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .expect("cannot walk up to repo root"); // repo root (host) or /root/ws (container)
    let candidates = [
        repo_root.join("build/quadropted_controller_cpp/cpp_xval_harness"),
        repo_root.join("install/quadropted_controller_cpp/lib/quadropted_controller_cpp/cpp_xval_harness"),
    ];
    for c in candidates {
        if c.exists() {
            return c;
        }
    }
    panic!(
        "C++ cross-validation harness not found. Build it first:\n\
         colcon build --packages-select quadropted_controller_cpp\n\
         (or set $CPP_XVAL_HARNESS to the binary path)"
    );
}

/// Run the C++ harness for one test and parse its JSON output.
fn run_harness(test: &str) -> serde_json::Value {
    let out = Command::new(harness_path())
        .arg(test)
        .output()
        .unwrap_or_else(|e| panic!("failed to run C++ harness for {}: {}", test, e));
    assert!(
        out.status.success(),
        "C++ harness '{}' exited with {:?}: {}",
        test,
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
    serde_json::from_slice(&out.stdout).unwrap_or_else(|e| panic!("bad JSON from '{}': {}", test, e))
}

// ── Comparison helpers ───────────────────────────────────────
fn approx(a: f64, b: f64, tol: f64) -> bool {
    (a - b).abs() <= tol
}

fn assert_vec3_eq(name: &str, rust: (f64, f64, f64), cpp: &serde_json::Value, tol: f64) {
    let c = cpp.as_array().expect("vec3 must be array");
    assert!(approx(rust.0, c[0].as_f64().unwrap(), tol) && approx(rust.1, c[1].as_f64().unwrap(), tol)
        && approx(rust.2, c[2].as_f64().unwrap(), tol),
        "{}: Rust=({}, {}, {}) C++=({}, {}, {}) tol={}", name, rust.0, rust.1, rust.2,
        c[0], c[1], c[2], tol);
}

fn assert_mat3_eq(name: &str, rust: &nalgebra::Matrix3<f64>, cpp: &serde_json::Value, tol: f64) {
    for r in 0..3 {
        for c in 0..3 {
            let v = cpp[r][c].as_f64().unwrap();
            assert!(approx(rust[(r, c)], v, tol),
                "{}[{}][{}]: Rust={} C++={} tol={}", name, r, c, rust[(r, c)], v, tol);
        }
    }
}

fn assert_mat4_eq(name: &str, rust: &nalgebra::Matrix4<f64>, cpp: &serde_json::Value, tol: f64) {
    for r in 0..4 {
        for c in 0..4 {
            let v = cpp[r][c].as_f64().unwrap();
            assert!(approx(rust[(r, c)], v, tol),
                "{}[{}][{}]: Rust={} C++={} tol={}", name, r, c, rust[(r, c)], v, tol);
        }
    }
}

fn assert_legs_eq(name: &str, rust: &nalgebra::SMatrix<f64, 3, 4>, cpp: &serde_json::Value, tol: f64) {
    for c in 0..4 {
        let col = &cpp[c];
        for r in 0..3 {
            let v = col[r].as_f64().unwrap();
            assert!(approx(rust[(r, c)], v, tol),
                "{} leg{} [{}]: Rust={} C++={} tol={}", name, c, r, rust[(r, c)], v, tol);
        }
    }
}

/// C++ 4x3 local positions (rows = legs) vs Rust 3x4 (columns = legs).
fn assert_local_eq(name: &str, rust: &nalgebra::SMatrix<f64, 3, 4>, cpp: &serde_json::Value, tol: f64) {
    for leg in 0..4 {
        let row = &cpp[leg];
        for c in 0..3 {
            let v = row[c].as_f64().unwrap();
            assert!(approx(rust[(c, leg)], v, tol),
                "{} leg{} [{}]: Rust={} C++={} tol={}", name, leg, c, rust[(c, leg)], v, tol);
        }
    }
}

// ═══════════════════════════════════════════════════════════
// Math: rotations
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_rotx() {
    use quadropted_core::math::rotation::rotx;
    let data = run_harness("rotx");
    let cases = data["data"].as_array().unwrap();
    let angles = [0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2, 1.1];
    for (i, a) in angles.iter().enumerate() {
        assert_mat3_eq(&format!("rotx({})", a), &rotx(*a), &cases[i], 1e-12);
    }
}

#[test]
fn xval_roty() {
    use quadropted_core::math::rotation::roty;
    let data = run_harness("roty");
    let cases = data["data"].as_array().unwrap();
    let angles = [0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2, 1.1];
    for (i, a) in angles.iter().enumerate() {
        assert_mat3_eq(&format!("roty({})", a), &roty(*a), &cases[i], 1e-12);
    }
}

#[test]
fn xval_rotz() {
    use quadropted_core::math::rotation::rotz;
    let data = run_harness("rotz");
    let cases = data["data"].as_array().unwrap();
    let angles = [0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2, 1.1];
    for (i, a) in angles.iter().enumerate() {
        assert_mat3_eq(&format!("rotz({})", a), &rotz(*a), &cases[i], 1e-12);
    }
}

#[test]
fn xval_rotxyz() {
    use quadropted_core::math::rotation::rotxyz;
    let data = run_harness("rotxyz");
    let cases = data["data"].as_array().unwrap();
    let cases_in = [(0.0, 0.0, 0.0), (0.3, -0.2, 0.5), (1.0, 0.5, -0.7), (-0.4, 0.9, 0.1)];
    for (i, (r, p, y)) in cases_in.iter().enumerate() {
        assert_mat3_eq(&format!("rotxyz({},{},{})", r, p, y), &rotxyz(*r, *p, *y), &cases[i], 1e-12);
    }
}

// ═══════════════════════════════════════════════════════════
// Math: homogeneous transforms
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_homog_transxyz() {
    use quadropted_core::math::transform::homog_transxyz;
    let data = run_harness("homog_transxyz");
    let cases = data["data"].as_array().unwrap();
    let cases_in = [(0.0, 0.0, 0.0), (0.1, 0.2, 0.3), (-0.5, 1.2, 0.05)];
    for (i, c) in cases_in.iter().enumerate() {
        assert_mat4_eq(&format!("homog_transxyz({})", i), &homog_transxyz(c.0, c.1, c.2), &cases[i], 1e-12);
    }
}

#[test]
fn xval_homog_transform() {
    use quadropted_core::math::rotation::rotxyz;
    use quadropted_core::math::transform::homog_transform;
    let data = run_harness("homog_transform");
    let cases = data["data"].as_array().unwrap();
    let cases_in = [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (0.1, 0.2, 0.3, 0.4, 0.5, 0.6), (-0.5, 1.2, 0.05, -0.1, 0.3, 0.7)];
    for (i, c) in cases_in.iter().enumerate() {
        let t = nalgebra::Vector3::new(c.0, c.1, c.2);
        let r = rotxyz(c.3, c.4, c.5);
        assert_mat4_eq(&format!("homog_transform({})", i), &homog_transform(&t, &r), &cases[i], 1e-12);
    }
}

#[test]
fn xval_homog_inverse() {
    use quadropted_core::math::rotation::rotxyz;
    use quadropted_core::math::transform::{homog_transform, homog_transform_inverse};
    let data = run_harness("homog_inverse");
    let cases = data["data"].as_array().unwrap();
    let cases_in = [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (0.1, 0.2, 0.3, 0.4, 0.5, 0.6), (-0.5, 1.2, 0.05, -0.1, 0.3, 0.7)];
    for (i, c) in cases_in.iter().enumerate() {
        let t = nalgebra::Vector3::new(c.0, c.1, c.2);
        let r = rotxyz(c.3, c.4, c.5);
        let m = homog_transform(&t, &r);
        assert_mat4_eq(&format!("homog_inverse({})", i), &homog_transform_inverse(&m), &cases[i], 1e-12);
    }
}

// ═══════════════════════════════════════════════════════════
// Kinematics: FK
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_fk_leg() {
    use quadropted_core::kinematics::forward::{compute_leg_fk_chain, leg_base_positions};
    let data = run_harness("fk_leg");
    let cases = data["data"].as_array().unwrap();
    let (bl, bw, l1, l2, l3, l4) = (0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);
    let angle_cases = [(0.0, 0.0, 0.0), (0.3, -0.6, 0.5), (-0.2, 0.8, -0.4), (0.5, 0.2, -0.9)];
    for (ci, (th, tt, tc)) in angle_cases.iter().enumerate() {
        for leg in 0..4 {
            let base = leg_base_positions(leg, bl, bw);
            let p = compute_leg_fk_chain(*th, *tt, *tc, base.x, base.y, l1, l2, l3, l4);
            assert_vec3_eq(&format!("fk_leg case{} leg{}", ci, leg), (p.x, p.y, p.z), &cases[ci][leg], 1e-9);
        }
    }
}

#[test]
fn xval_fk_all_legs() {
    use quadropted_core::kinematics::forward::forward_kinematics_all_legs;
    let data = run_harness("fk_all_legs");
    let cases = data["data"].as_array().unwrap();
    let (bl, bw, l1, l2, l3, l4) = (0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);
    let joint_cases: [[f64; 12]; 2] = [
        [0.0, 0.3, -0.6, 0.0, 0.3, -0.6, 0.0, 0.3, -0.6, 0.0, 0.3, -0.6],
        [0.1, -0.4, 0.3, -0.2, 0.5, -0.7, 0.4, -0.1, 0.2, -0.3, 0.6, -0.5],
    ];
    for (ci, j) in joint_cases.iter().enumerate() {
        let feet = forward_kinematics_all_legs(j, bl, bw, l1, l2, l3, l4);
        for leg in 0..4 {
            assert_vec3_eq(&format!("fk_all case{} leg{}", ci, leg),
                (feet[leg].x, feet[leg].y, feet[leg].z), &cases[ci][leg], 1e-9);
        }
    }
}

// ═══════════════════════════════════════════════════════════
// Kinematics: IK
// ═══════════════════════════════════════════════════════════
// NOTE: C++ uses fast_atan2 (polynomial approx) while Rust uses std::atan2,
// so IK tolerance is 2e-3 — same as the C++ unit test (test_ik.cpp).
const IK_TOL: f64 = 2e-3;

#[test]
fn xval_ik_leg() {
    use quadropted_core::kinematics::inverse::compute_joint_angles_for_leg;
    let data = run_harness("ik_leg");
    let cases = data["data"].as_array().unwrap();
    let (l1, l2, l3, l4) = (0.0, 0.0955, 0.213, 0.213);
    let targets = [
        (0.2, -0.12, -0.2), (0.2, 0.12, -0.2), (-0.2, -0.12, -0.2), (-0.2, 0.12, -0.2),
        (0.25, -0.15, -0.25), (0.18, 0.10, -0.3), (-0.22, -0.13, -0.28), (-0.19, 0.14, -0.22),
    ];
    for (i, (x, y, z)) in targets.iter().enumerate() {
        let leg = i % 4;
        let a = compute_joint_angles_for_leg(*x, *y, *z, leg, l1, l2, l3, l4);
        assert_vec3_eq(&format!("ik_leg {}", i), (a[0], a[1], a[2]), &cases[i], IK_TOL);
    }
}

#[test]
fn xval_local_positions() {
    use quadropted_core::kinematics::inverse::compute_local_positions;
    use nalgebra::SMatrix;
    let data = run_harness("local_positions");
    let cases = data["data"].as_array().unwrap();
    let (bl, bw) = (0.3762, 0.0935);
    let lp: SMatrix<f64, 3, 4> = SMatrix::from_row_slice(&[
        0.2081, 0.2081, -0.1881, -0.1881, -0.14225, 0.14225, -0.14225, 0.14225, -0.25, -0.25, -0.25, -0.25,
    ]);
    let params = [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (0.01, 0.0, 0.005, 0.0, -0.02, 0.0), (0.0, -0.02, 0.0, 0.03, 0.0, 0.04)];
    for (i, (dx, dy, dz, roll, pitch, yaw)) in params.iter().enumerate() {
        let local = compute_local_positions(&lp, bl, bw, *dx, *dy, *dz, *roll, *pitch, *yaw);
        assert_local_eq(&format!("local_positions {}", i), &local, &cases[i], 1e-9);
    }
}

#[test]
fn xval_ik_all() {
    use quadropted_core::kinematics::inverse::inverse_kinematics;
    use nalgebra::SMatrix;
    let data = run_harness("ik_all");
    let cases = data["data"].as_array().unwrap();
    let (bl, bw, l1, l2, l3, l4) = (0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);
    let lp: SMatrix<f64, 3, 4> = SMatrix::from_row_slice(&[
        0.2081, 0.2081, -0.1881, -0.1881, -0.14225, 0.14225, -0.14225, 0.14225, -0.25, -0.25, -0.25, -0.25,
    ]);
    let params = [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (0.01, 0.0, 0.005, 0.0, -0.02, 0.0), (0.0, -0.02, 0.0, 0.03, 0.0, 0.04)];
    for (i, (dx, dy, dz, roll, pitch, yaw)) in params.iter().enumerate() {
        let a = inverse_kinematics(&lp, bl, bw, l1, l2, l3, l4, *dx, *dy, *dz, *roll, *pitch, *yaw);
        for (k, v) in a.iter().enumerate() {
            let cpp = cases[i][k].as_f64().unwrap();
            assert!(approx(*v, cpp, IK_TOL), "ik_all {}[{}]: Rust={} C++={} tol={}", i, k, v, cpp, IK_TOL);
        }
    }
}

// ═══════════════════════════════════════════════════════════
// Gait: phases + contacts (integer-exact)
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_trot_gait_phases() {
    use quadropted_core::controllers::trot::gait::TrotGaitController;
    let data = run_harness("trot_gait_phases");
    let d = &data["data"];
    let st = node_stance();
    let mut trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
    let ticks = d["ticks"].as_array().unwrap();
    assert_eq!(trot.stance_ticks(), ticks[0].as_i64().unwrap() as i32);
    assert_eq!(trot.swing_ticks(), ticks[1].as_i64().unwrap() as i32);
    assert_eq!(trot.phase_length(), ticks[2].as_i64().unwrap() as i32);

    let phases = d["phases"].as_array().unwrap();
    for (t, p) in phases.iter().enumerate() {
        let rust_p = trot.gait_mut().phase_index(t as i32);
        assert_eq!(rust_p, p.as_u64().unwrap() as usize, "phase_index({})", t);
    }
    let contacts = d["contacts"].as_array().unwrap();
    for (t, c) in contacts.iter().enumerate() {
        let rust_c = trot.contacts(t as i32);
        for leg in 0..4 {
            assert_eq!(rust_c[leg], c[leg].as_i64().unwrap() as i32, "contacts({}) leg {}", t, leg);
        }
    }
}

#[test]
fn xval_crawl_gait_phases() {
    use quadropted_core::controllers::crawl::gait::CrawlGaitController;
    let data = run_harness("crawl_gait_phases");
    let d = &data["data"];
    let crawl = CrawlGaitController::new(0.55, 0.45, 0.02, node_stance());
    let ticks = d["ticks"].as_array().unwrap();
    assert_eq!(crawl.stance_ticks(), ticks[0].as_i64().unwrap() as i32);
    assert_eq!(crawl.swing_ticks(), ticks[1].as_i64().unwrap() as i32);
    assert_eq!(crawl.phase_length(), ticks[2].as_i64().unwrap() as i32);

    let phases = d["phases"].as_array().unwrap();
    for (t, p) in phases.iter().enumerate() {
        assert_eq!(crawl.phase_index(t as i32), p.as_u64().unwrap() as usize, "phase_index({})", t);
    }
    let contacts = d["contacts"].as_array().unwrap();
    for (t, c) in contacts.iter().enumerate() {
        let rust_c = crawl.contacts(t as i32);
        for leg in 0..4 {
            assert_eq!(rust_c[leg], c[leg].as_i64().unwrap() as i32, "contacts({}) leg {}", t, leg);
        }
    }
}

// ═══════════════════════════════════════════════════════════
// Controllers: TROT
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_trot_stance_swing() {
    use quadropted_core::controllers::trot::stance::TrotStanceController;
    use quadropted_core::controllers::trot::swing::TrotSwingController;
    let data = run_harness("trot_stance_swing");
    let d = &data["data"];
    let st = node_stance();
    let stance = TrotStanceController::new(22, 2, 9, 0.02, 0.02);
    let swing = TrotSwingController::new(9, 0.02, 0.14, st, 22, 2);
    let cmd = nalgebra::Vector3::new(0.05, 0.02, 0.1);

    for leg in 0..4 {
        let r = stance.next_foot_location(leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("trot stance leg{}", leg), (r.x, r.y, r.z), &d["stance"][leg], 1e-9);
        let pd = stance.position_delta(leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("trot pos_delta leg{}", leg), (pd.x, pd.y, pd.z), &d["pos_delta"][leg], 1e-9);
        let sw = swing.next_foot_location(0.4, leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("trot swing leg{}", leg), (sw.x, sw.y, sw.z), &d["swing"][leg], 1e-9);
        let td = swing.raibert_touchdown_location(leg, &cmd);
        assert_vec3_eq(&format!("trot td leg{}", leg), (td.x, td.y, td.z), &d["td"][leg], 1e-9);
    }
    for (i, p) in [0.0, 0.25, 0.5, 0.75, 1.0].iter().enumerate() {
        assert!(approx(swing.swing_height(*p), d["h"][i].as_f64().unwrap(), 1e-12),
            "trot swing_height({})", p);
    }
}

#[test]
fn xval_trot_gait_step() {
    use quadropted_core::controllers::trot::gait::TrotGaitController;
    let data = run_harness("trot_gait_step");
    let cases = data["data"].as_array().unwrap();
    let st = node_stance();
    let trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
    let mut cur = st;
    let cmd = [0.05, 0.02, 0.1];
    for t in 1..=44 {
        cur = trot.step(t, &cur, &cmd, -0.25);
        assert_legs_eq(&format!("trot step {}", t), &cur, &cases[(t - 1) as usize], 1e-9);
    }
}

// ═══════════════════════════════════════════════════════════
// Controllers: CRAWL
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_crawl_stance_swing() {
    use quadropted_core::controllers::crawl::stance::CrawlStanceController;
    use quadropted_core::controllers::crawl::swing::CrawlSwingController;
    let data = run_harness("crawl_stance_swing");
    let d = &data["data"];
    let st = node_stance();
    let stance = CrawlStanceController::new(196, 27, 22, 0.02, 0.02, 0.06);
    let swing = CrawlSwingController::new(22, 0.02, 0.14, st, 196, 27, 0.06);
    let cmd = nalgebra::Vector3::new(0.01, 0.005, 0.05);

    for leg in 0..4 {
        let r = stance.next_foot_location(leg, &st, &cmd, -0.25, true, true, leg == 0);
        assert_vec3_eq(&format!("crawl stance leg{}", leg), (r.x, r.y, r.z), &d["stance"][leg], 1e-9);
        let sw = swing.next_foot_location(0.4, leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("crawl swing leg{}", leg), (sw.x, sw.y, sw.z), &d["swing"][leg], 1e-9);
        let td = swing.raibert_touchdown_location(leg, &cmd, false);
        assert_vec3_eq(&format!("crawl td leg{}", leg), (td.x, td.y, td.z), &d["td"][leg], 1e-9);
    }
    for (i, p) in [0.0, 0.25, 0.5, 0.75, 1.0].iter().enumerate() {
        assert!(approx(swing.swing_height(*p), d["h"][i].as_f64().unwrap(), 1e-12),
            "crawl swing_height({})", p);
    }
}

#[test]
fn xval_crawl_runtime_step() {
    // Активный runtime-путь (RobotControllerNode::step_crawl): Rust
    // CrawlGaitController::step() против C++ step_crawl (с командой и без).
    use quadropted_core::controllers::crawl::gait::CrawlGaitController;
    let data = run_harness("crawl_runtime_step");
    let d = &data["data"];
    let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, node_stance());
    let mut cur = node_stance();
    let cmd = [0.01, 0.0, 0.0];
    let with_cmd = d["with_cmd"].as_array().unwrap();
    for (i, cpp) in with_cmd.iter().enumerate() {
        cur = crawl.step(i as i32 + 1, &cur, &cmd, -0.25);
        assert_legs_eq(&format!("crawl step(with cmd) {}", i + 1), &cur, cpp, 1e-9);
    }
    let no_cmd = d["no_cmd"].as_array().unwrap();
    let zero = [0.0, 0.0, 0.0];
    for (i, cpp) in no_cmd.iter().enumerate() {
        cur = crawl.step(1000 + i as i32, &cur, &zero, -0.25);
        assert_legs_eq(&format!("crawl step(no cmd) {}", i + 1), &cur, cpp, 1e-9);
    }
}

// ═══════════════════════════════════════════════════════════
// Controllers: REST / STAND / PID
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_rest_stand() {
    use quadropted_core::controllers::rest::{RestController, RestState};
    use quadropted_core::controllers::stand::{BodyState, StandController};
    let data = run_harness("rest_stand");
    let d = &data["data"];
    let st = node_stance();
    let mut rest = RestController::new(st);
    let stand = StandController::new(st);

    let state = RestState { imu_roll: 0.1, imu_pitch: -0.05 };
    let r1 = rest.step(&state, -0.25);
    assert_legs_eq("rest1", &r1, &d["rest1"], 1e-9);
    let r2 = rest.step(&state, -0.25);
    assert_legs_eq("rest2", &r2, &d["rest2"], 1e-9);

    let mut body = BodyState { body_local_position: [0.0, 0.0, 0.0], body_local_orientation: [0.0, 0.0, 0.0] };
    let s0 = stand.run(&mut body, -0.25, &[0.0, 0.0, 0.0], &[0.0, 0.0, 0.0]);
    assert_legs_eq("stand0", &s0, &d["stand0"], 1e-9);
    let sm = stand.run(&mut body, -0.25, &[0.05, 0.0, 0.0], &[0.0, 0.0, 0.0]);
    assert_legs_eq("stand_move", &sm, &d["stand_move"], 1e-9);
    for i in 0..3 {
        let v = d["body_pos"][i].as_f64().unwrap();
        assert!(approx(body.body_local_position[i], v, 1e-12), "body_pos[{}]: Rust={} C++={}", i, body.body_local_position[i], v);
    }
}

#[test]
fn xval_pid() {
    use quadropted_core::controllers::pid::PIDController;
    let data = run_harness("pid");
    let cases = data["data"].as_array().unwrap();
    let mut pid = PIDController::new(0.15, 0.02, 0.002);
    pid.reset(0.0);
    let mut t = 0.02;
    for (i, cpp) in cases.iter().enumerate() {
        let r = pid.run(0.1, -0.05, t);
        assert!(approx(r[0], cpp[0].as_f64().unwrap(), 1e-12) && approx(r[1], cpp[1].as_f64().unwrap(), 1e-12),
            "pid[{}]: Rust=({},{}) C++=({},{})", i, r[0], r[1], cpp[0], cpp[1]);
        t += 0.02;
    }
}

// ═══════════════════════════════════════════════════════════
// Odometry
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_odometry_update() {
    use quadropted_core::odometry::state::OdometryState;
    use quadropted_core::odometry::update::update_odometry;
    use nalgebra::Vector3;
    let data = run_harness("odometry_update");
    let d = &data["data"];

    // x: foot 0 движется в +x при контакте
    let mut st = OdometryState::new(14);
    st.linear_velocity_x = 0.1;
    st.foot_states[0].contact = true;
    st.foot_states[0].position = Vector3::new(0.20, -0.14, -0.25);
    let xs = d["x"].as_array().unwrap();
    for (i, cpp) in xs.iter().enumerate() {
        st.foot_states[0].position.x += 0.002;
        update_odometry(&mut st, 0.02, 0.65);
        assert!(approx(st.x, cpp.as_f64().unwrap(), 1e-9), "odom x[{}]: Rust={} C++={}", i, st.x, cpp);
    }

    // y: theta = 0.5, foot движется в +y
    let mut st2 = OdometryState::new(14);
    st2.theta = 0.5;
    st2.foot_states[0].contact = true;
    st2.foot_states[0].position = Vector3::new(0.20, -0.14, -0.25);
    let ys = d["y"].as_array().unwrap();
    for (i, cpp) in ys.iter().enumerate() {
        st2.foot_states[0].position.y += 0.002;
        update_odometry(&mut st2, 0.02, 0.65);
        assert!(approx(st2.y, cpp.as_f64().unwrap(), 1e-9), "odom y[{}]: Rust={} C++={}", i, st2.y, cpp);
    }

    assert_eq!(st.is_stalled, d["stall"].as_bool().unwrap(), "stall flag mismatch");
}

// ═══════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════
/// Stance как в активном C++-ноде (RobotControllerNode ctor).
fn node_stance() -> nalgebra::SMatrix<f64, 3, 4> {
    let body = [0.3762, 0.0935];
    let legs = [0.0, 0.0955, 0.213, 0.213];
    let dx_front = body[0] * 0.5 + 0.02;
    let dx_back = body[0] * 0.5 + 0.0;
    let dy = body[1] * 0.5 + legs[1];
    nalgebra::SMatrix::<f64, 3, 4>::from_row_slice(&[
        dx_front, dx_front, -dx_back, -dx_back,
        -dy, dy, -dy, dy,
        0.0, 0.0, 0.0, 0.0,
    ])
}
