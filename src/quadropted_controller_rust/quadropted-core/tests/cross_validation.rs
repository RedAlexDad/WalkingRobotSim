//! Cross-validation tests: Rust vs golden-данные C++-эталона.
//!
//! Раньше эти тесты запускали C++-харнесс `cpp_xval_harness` и сравнивали
//! его JSON-вывод с Rust на лету. Теперь эталон завендорен в
//! `tests/golden/mod.rs`: те же 21 проверка, те же значения, снятые с того же
//! харнесса с точностью `%.17g` (полный round-trip `f64`). C++-пакет удалён,
//! сборка и сеть для тестов не нужны.
//!
//! Допуски совпадают с прежними — эталон снят без потери точности:
//!
//! | Допуск   | Что сравнивается                                            |
//! |----------|-------------------------------------------------------------|
//! | `1e-12`  | математика (`rot*`, `homog_*`), PID, `swing_height`         |
//! | `1e-9`   | FK/`local_positions`, шаги походки, контроллеры, одометрия   |
//! | `2e-3`   | IK: в C++ `fast_atan2` (полином), в Rust `std::atan2`        |
//! | точно    | целочисленные `phase_index` и `contacts`                    |
//!
//! Допуск `2e-3` для IK — тот же, что в C++ unit-тесте `test_ik.cpp`.

mod golden;

use golden::*;

// ── Comparison helpers ───────────────────────────────────────
fn approx(a: f64, b: f64, tol: f64) -> bool {
    (a - b).abs() <= tol
}

fn assert_vec3_eq(name: &str, rust: (f64, f64, f64), cpp: &[f64; 3], tol: f64) {
    assert!(
        approx(rust.0, cpp[0], tol) && approx(rust.1, cpp[1], tol) && approx(rust.2, cpp[2], tol),
        "{}: Rust=({}, {}, {}) C++=({}, {}, {}) tol={}",
        name,
        rust.0,
        rust.1,
        rust.2,
        cpp[0],
        cpp[1],
        cpp[2],
        tol
    );
}

fn assert_mat3_eq(name: &str, rust: &nalgebra::Matrix3<f64>, cpp: &[[f64; 3]; 3], tol: f64) {
    for r in 0..3 {
        for c in 0..3 {
            let v = cpp[r][c];
            assert!(
                approx(rust[(r, c)], v, tol),
                "{}[{}][{}]: Rust={} C++={} tol={}",
                name,
                r,
                c,
                rust[(r, c)],
                v,
                tol
            );
        }
    }
}

fn assert_mat4_eq(name: &str, rust: &nalgebra::Matrix4<f64>, cpp: &[[f64; 4]; 4], tol: f64) {
    for r in 0..4 {
        for c in 0..4 {
            let v = cpp[r][c];
            assert!(
                approx(rust[(r, c)], v, tol),
                "{}[{}][{}]: Rust={} C++={} tol={}",
                name,
                r,
                c,
                rust[(r, c)],
                v,
                tol
            );
        }
    }
}

fn assert_legs_eq(name: &str, rust: &nalgebra::SMatrix<f64, 3, 4>, cpp: &[[f64; 3]; 4], tol: f64) {
    for c in 0..4 {
        let col = &cpp[c];
        for r in 0..3 {
            let v = col[r];
            assert!(
                approx(rust[(r, c)], v, tol),
                "{} leg{} [{}]: Rust={} C++={} tol={}",
                name,
                c,
                r,
                rust[(r, c)],
                v,
                tol
            );
        }
    }
}

/// C++ 4x3 local positions (rows = legs) vs Rust 3x4 (columns = legs).
fn assert_local_eq(
    name: &str,
    rust: &nalgebra::SMatrix<f64, 3, 4>,
    cpp: &[[f64; 3]; 4],
    tol: f64,
) {
    for leg in 0..4 {
        let row = &cpp[leg];
        for c in 0..3 {
            let v = row[c];
            assert!(
                approx(rust[(c, leg)], v, tol),
                "{} leg{} [{}]: Rust={} C++={} tol={}",
                name,
                leg,
                c,
                rust[(c, leg)],
                v,
                tol
            );
        }
    }
}

// ═══════════════════════════════════════════════════════════
// Math: rotations
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_rotx() {
    use quadropted_core::math::rotation::rotx;
    let angles = [0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2, 1.1];
    for (i, a) in angles.iter().enumerate() {
        assert_mat3_eq(&format!("rotx({})", a), &rotx(*a), &ROTX[i], 1e-12);
    }
}

#[test]
fn xval_roty() {
    use quadropted_core::math::rotation::roty;
    let angles = [0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2, 1.1];
    for (i, a) in angles.iter().enumerate() {
        assert_mat3_eq(&format!("roty({})", a), &roty(*a), &ROTY[i], 1e-12);
    }
}

#[test]
fn xval_rotz() {
    use quadropted_core::math::rotation::rotz;
    let angles = [0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2, 1.1];
    for (i, a) in angles.iter().enumerate() {
        assert_mat3_eq(&format!("rotz({})", a), &rotz(*a), &ROTZ[i], 1e-12);
    }
}

#[test]
fn xval_rotxyz() {
    use quadropted_core::math::rotation::rotxyz;
    let cases_in = [(0.0, 0.0, 0.0), (0.3, -0.2, 0.5), (1.0, 0.5, -0.7), (-0.4, 0.9, 0.1)];
    for (i, (r, p, y)) in cases_in.iter().enumerate() {
        assert_mat3_eq(&format!("rotxyz({},{},{})", r, p, y), &rotxyz(*r, *p, *y), &ROTXYZ[i], 1e-12);
    }
}

// ═══════════════════════════════════════════════════════════
// Math: homogeneous transforms
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_homog_transxyz() {
    use quadropted_core::math::transform::homog_transxyz;
    let cases_in = [(0.0, 0.0, 0.0), (0.1, 0.2, 0.3), (-0.5, 1.2, 0.05)];
    for (i, c) in cases_in.iter().enumerate() {
        assert_mat4_eq(&format!("homog_transxyz({})", i), &homog_transxyz(c.0, c.1, c.2), &HOMOG_TRANSXYZ[i], 1e-12);
    }
}

#[test]
fn xval_homog_transform() {
    use quadropted_core::math::rotation::rotxyz;
    use quadropted_core::math::transform::homog_transform;
    let cases_in = [
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
        (-0.5, 1.2, 0.05, -0.1, 0.3, 0.7),
    ];
    for (i, c) in cases_in.iter().enumerate() {
        let t = nalgebra::Vector3::new(c.0, c.1, c.2);
        let r = rotxyz(c.3, c.4, c.5);
        assert_mat4_eq(&format!("homog_transform({})", i), &homog_transform(&t, &r), &HOMOG_TRANSFORM[i], 1e-12);
    }
}

#[test]
fn xval_homog_inverse() {
    use quadropted_core::math::rotation::rotxyz;
    use quadropted_core::math::transform::{homog_transform, homog_transform_inverse};
    let cases_in = [
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
        (-0.5, 1.2, 0.05, -0.1, 0.3, 0.7),
    ];
    for (i, c) in cases_in.iter().enumerate() {
        let t = nalgebra::Vector3::new(c.0, c.1, c.2);
        let r = rotxyz(c.3, c.4, c.5);
        let m = homog_transform(&t, &r);
        assert_mat4_eq(&format!("homog_inverse({})", i), &homog_transform_inverse(&m), &HOMOG_INVERSE[i], 1e-12);
    }
}

// ═══════════════════════════════════════════════════════════
// Kinematics: FK
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_fk_leg() {
    use quadropted_core::kinematics::forward::{compute_leg_fk_chain, leg_base_positions};
    let (bl, bw, l1, l2, l3, l4) = (0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);
    let angle_cases = [(0.0, 0.0, 0.0), (0.3, -0.6, 0.5), (-0.2, 0.8, -0.4), (0.5, 0.2, -0.9)];
    for (ci, (th, tt, tc)) in angle_cases.iter().enumerate() {
        for leg in 0..4 {
            let base = leg_base_positions(leg, bl, bw);
            let p = compute_leg_fk_chain(*th, *tt, *tc, base.x, base.y, l1, l2, l3, l4);
            assert_vec3_eq(&format!("fk_leg case{} leg{}", ci, leg), (p.x, p.y, p.z), &FK_LEG[ci][leg], 1e-9);
        }
    }
}

#[test]
fn xval_fk_all_legs() {
    use quadropted_core::kinematics::forward::forward_kinematics_all_legs;
    let (bl, bw, l1, l2, l3, l4) = (0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);
    let joint_cases: [[f64; 12]; 2] = [
        [0.0, 0.3, -0.6, 0.0, 0.3, -0.6, 0.0, 0.3, -0.6, 0.0, 0.3, -0.6],
        [0.1, -0.4, 0.3, -0.2, 0.5, -0.7, 0.4, -0.1, 0.2, -0.3, 0.6, -0.5],
    ];
    for (ci, j) in joint_cases.iter().enumerate() {
        let feet = forward_kinematics_all_legs(j, bl, bw, l1, l2, l3, l4);
        for leg in 0..4 {
            assert_vec3_eq(
                &format!("fk_all case{} leg{}", ci, leg),
                (feet[leg].x, feet[leg].y, feet[leg].z),
                &FK_ALL_LEGS[ci][leg],
                1e-9,
            );
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
    let (l1, l2, l3, l4) = (0.0, 0.0955, 0.213, 0.213);
    let targets = [
        (0.2, -0.12, -0.2),
        (0.2, 0.12, -0.2),
        (-0.2, -0.12, -0.2),
        (-0.2, 0.12, -0.2),
        (0.25, -0.15, -0.25),
        (0.18, 0.10, -0.3),
        (-0.22, -0.13, -0.28),
        (-0.19, 0.14, -0.22),
    ];
    for (i, (x, y, z)) in targets.iter().enumerate() {
        let leg = i % 4;
        let a = compute_joint_angles_for_leg(*x, *y, *z, leg, l1, l2, l3, l4);
        assert_vec3_eq(&format!("ik_leg {}", i), (a[0], a[1], a[2]), &IK_LEG[i], IK_TOL);
    }
}

#[test]
fn xval_local_positions() {
    use nalgebra::SMatrix;
    use quadropted_core::kinematics::inverse::compute_local_positions;
    let (bl, bw) = (0.3762, 0.0935);
    let lp: SMatrix<f64, 3, 4> = SMatrix::from_row_slice(&[
        0.2081, 0.2081, -0.1881, -0.1881, -0.14225, 0.14225, -0.14225, 0.14225, -0.25, -0.25, -0.25, -0.25,
    ]);
    let params = [
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (0.01, 0.0, 0.005, 0.0, -0.02, 0.0),
        (0.0, -0.02, 0.0, 0.03, 0.0, 0.04),
    ];
    for (i, (dx, dy, dz, roll, pitch, yaw)) in params.iter().enumerate() {
        let local = compute_local_positions(&lp, bl, bw, *dx, *dy, *dz, *roll, *pitch, *yaw);
        assert_local_eq(&format!("local_positions {}", i), &local, &LOCAL_POSITIONS[i], 1e-9);
    }
}

#[test]
fn xval_ik_all() {
    use nalgebra::SMatrix;
    use quadropted_core::kinematics::inverse::inverse_kinematics;
    let (bl, bw, l1, l2, l3, l4) = (0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);
    let lp: SMatrix<f64, 3, 4> = SMatrix::from_row_slice(&[
        0.2081, 0.2081, -0.1881, -0.1881, -0.14225, 0.14225, -0.14225, 0.14225, -0.25, -0.25, -0.25, -0.25,
    ]);
    let params = [
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (0.01, 0.0, 0.005, 0.0, -0.02, 0.0),
        (0.0, -0.02, 0.0, 0.03, 0.0, 0.04),
    ];
    for (i, (dx, dy, dz, roll, pitch, yaw)) in params.iter().enumerate() {
        let a = inverse_kinematics(&lp, bl, bw, l1, l2, l3, l4, *dx, *dy, *dz, *roll, *pitch, *yaw);
        for (k, v) in a.iter().enumerate() {
            let cpp = IK_ALL[i][k];
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
    let st = node_stance();
    let mut trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
    assert_eq!(trot.stance_ticks(), TROT_GAIT_TICKS[0]);
    assert_eq!(trot.swing_ticks(), TROT_GAIT_TICKS[1]);
    assert_eq!(trot.phase_length(), TROT_GAIT_TICKS[2]);

    for (t, expected) in TROT_GAIT_PHASES.iter().enumerate() {
        let rust_p = trot.gait_mut().phase_index(t as i32);
        assert_eq!(rust_p, *expected, "phase_index({})", t);
    }
    for (t, expected) in TROT_GAIT_CONTACTS.iter().enumerate() {
        let rust_c = trot.contacts(t as i32);
        for leg in 0..4 {
            assert_eq!(rust_c[leg], expected[leg], "contacts({}) leg {}", t, leg);
        }
    }
}

#[test]
fn xval_crawl_gait_phases() {
    use quadropted_core::controllers::crawl::gait::CrawlGaitController;
    let crawl = CrawlGaitController::new(0.55, 0.45, 0.02, node_stance());
    assert_eq!(crawl.stance_ticks(), CRAWL_GAIT_TICKS[0]);
    assert_eq!(crawl.swing_ticks(), CRAWL_GAIT_TICKS[1]);
    assert_eq!(crawl.phase_length(), CRAWL_GAIT_TICKS[2]);

    for (t, expected) in CRAWL_GAIT_PHASES.iter().enumerate() {
        assert_eq!(crawl.phase_index(t as i32), *expected, "phase_index({})", t);
    }
    for (t, expected) in CRAWL_GAIT_CONTACTS.iter().enumerate() {
        let rust_c = crawl.contacts(t as i32);
        for leg in 0..4 {
            assert_eq!(rust_c[leg], expected[leg], "contacts({}) leg {}", t, leg);
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
    let st = node_stance();
    let stance = TrotStanceController::new(22, 2, 9, 0.02, 0.02);
    let swing = TrotSwingController::new(9, 0.02, 0.14, st, 22, 2);
    let cmd = nalgebra::Vector3::new(0.05, 0.02, 0.1);

    for leg in 0..4 {
        let r = stance.next_foot_location(leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("trot stance leg{}", leg), (r.x, r.y, r.z), &TROT_STANCE[leg], 1e-9);
        let pd = stance.position_delta(leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("trot pos_delta leg{}", leg), (pd.x, pd.y, pd.z), &TROT_POS_DELTA[leg], 1e-9);
        let sw = swing.next_foot_location(0.4, leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("trot swing leg{}", leg), (sw.x, sw.y, sw.z), &TROT_SWING[leg], 1e-9);
        let td = swing.raibert_touchdown_location(leg, &cmd);
        assert_vec3_eq(&format!("trot td leg{}", leg), (td.x, td.y, td.z), &TROT_TD[leg], 1e-9);
    }
    for (i, p) in [0.0, 0.25, 0.5, 0.75, 1.0].iter().enumerate() {
        assert!(approx(swing.swing_height(*p), TROT_SWING_H[i], 1e-12), "trot swing_height({})", p);
    }
}

#[test]
fn xval_trot_gait_step() {
    use quadropted_core::controllers::trot::gait::TrotGaitController;
    let st = node_stance();
    let trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
    let mut cur = st;
    let cmd = [0.05, 0.02, 0.1];
    for t in 1..=44 {
        cur = trot.step(t, &cur, &cmd, -0.25);
        assert_legs_eq(&format!("trot step {}", t), &cur, &TROT_STEP[(t - 1) as usize], 1e-9);
    }
}

// ═══════════════════════════════════════════════════════════
// Controllers: CRAWL
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_crawl_stance_swing() {
    use quadropted_core::controllers::crawl::stance::CrawlStanceController;
    use quadropted_core::controllers::crawl::swing::CrawlSwingController;
    let st = node_stance();
    let stance = CrawlStanceController::new(196, 27, 22, 0.02, 0.02, 0.06);
    let swing = CrawlSwingController::new(22, 0.02, 0.14, st, 196, 27, 0.06);
    let cmd = nalgebra::Vector3::new(0.01, 0.005, 0.05);

    for leg in 0..4 {
        let r = stance.next_foot_location(leg, &st, &cmd, -0.25, true, true, leg == 0);
        assert_vec3_eq(&format!("crawl stance leg{}", leg), (r.x, r.y, r.z), &CRAWL_STANCE[leg], 1e-9);
        let sw = swing.next_foot_location(0.4, leg, &st, &cmd, -0.25);
        assert_vec3_eq(&format!("crawl swing leg{}", leg), (sw.x, sw.y, sw.z), &CRAWL_SWING[leg], 1e-9);
        let td = swing.raibert_touchdown_location(leg, &cmd, false);
        assert_vec3_eq(&format!("crawl td leg{}", leg), (td.x, td.y, td.z), &CRAWL_TD[leg], 1e-9);
    }
    for (i, p) in [0.0, 0.25, 0.5, 0.75, 1.0].iter().enumerate() {
        assert!(approx(swing.swing_height(*p), CRAWL_SWING_H[i], 1e-12), "crawl swing_height({})", p);
    }
}

#[test]
fn xval_crawl_runtime_step() {
    // Активный runtime-путь (RobotControllerNode::step_crawl): Rust
    // CrawlGaitController::step() против golden-данных C++ step_crawl
    // (с командой и без).
    use quadropted_core::controllers::crawl::gait::CrawlGaitController;
    let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, node_stance());
    let mut cur = node_stance();
    let cmd = [0.01, 0.0, 0.0];
    for (i, cpp) in CRAWL_RUNTIME_WITH_CMD.iter().enumerate() {
        cur = crawl.step(i as i32 + 1, &cur, &cmd, -0.25);
        assert_legs_eq(&format!("crawl step(with cmd) {}", i + 1), &cur, cpp, 1e-9);
    }
    let zero = [0.0, 0.0, 0.0];
    for (i, cpp) in CRAWL_RUNTIME_NO_CMD.iter().enumerate() {
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
    let st = node_stance();
    let mut rest = RestController::new(st);
    let stand = StandController::new(st);

    let state = RestState { imu_roll: 0.1, imu_pitch: -0.05 };
    let r1 = rest.step(&state, -0.25);
    assert_legs_eq("rest1", &r1, &REST1, 1e-9);
    let r2 = rest.step(&state, -0.25);
    assert_legs_eq("rest2", &r2, &REST2, 1e-9);

    let mut body = BodyState { body_local_position: [0.0, 0.0, 0.0], body_local_orientation: [0.0, 0.0, 0.0] };
    let s0 = stand.run(&mut body, -0.25, &[0.0, 0.0, 0.0], &[0.0, 0.0, 0.0]);
    assert_legs_eq("stand0", &s0, &STAND0, 1e-9);
    let sm = stand.run(&mut body, -0.25, &[0.05, 0.0, 0.0], &[0.0, 0.0, 0.0]);
    assert_legs_eq("stand_move", &sm, &STAND_MOVE, 1e-9);
    for i in 0..3 {
        assert!(
            approx(body.body_local_position[i], BODY_POS[i], 1e-12),
            "body_pos[{}]: Rust={} C++={}",
            i,
            body.body_local_position[i],
            BODY_POS[i]
        );
    }
}

#[test]
fn xval_pid() {
    use quadropted_core::controllers::pid::PIDController;
    let mut pid = PIDController::new(0.15, 0.02, 0.002);
    pid.reset(0.0);
    let mut t = 0.02;
    for (i, cpp) in PID.iter().enumerate() {
        let r = pid.run(0.1, -0.05, t);
        assert!(
            approx(r[0], cpp[0], 1e-12) && approx(r[1], cpp[1], 1e-12),
            "pid[{}]: Rust=({},{}) C++=({},{})",
            i,
            r[0],
            r[1],
            cpp[0],
            cpp[1]
        );
        t += 0.02;
    }
}

// ═══════════════════════════════════════════════════════════
// Odometry
// ═══════════════════════════════════════════════════════════
#[test]
fn xval_odometry_update() {
    use nalgebra::Vector3;
    use quadropted_core::odometry::state::OdometryState;
    use quadropted_core::odometry::update::update_odometry;

    // x: foot 0 движется в +x при контакте
    let mut st = OdometryState::new(14);
    st.linear_velocity_x = 0.1;
    st.foot_states[0].contact = true;
    st.foot_states[0].position = Vector3::new(0.20, -0.14, -0.25);
    for (i, cpp) in ODOM_X.iter().enumerate() {
        st.foot_states[0].position.x += 0.002;
        update_odometry(&mut st, 0.02, 0.65);
        assert!(approx(st.x, *cpp, 1e-9), "odom x[{}]: Rust={} C++={}", i, st.x, cpp);
    }

    // y: theta = 0.5, foot движется в +y
    let mut st2 = OdometryState::new(14);
    st2.theta = 0.5;
    st2.foot_states[0].contact = true;
    st2.foot_states[0].position = Vector3::new(0.20, -0.14, -0.25);
    for (i, cpp) in ODOM_Y.iter().enumerate() {
        st2.foot_states[0].position.y += 0.002;
        update_odometry(&mut st2, 0.02, 0.65);
        assert!(approx(st2.y, *cpp, 1e-9), "odom y[{}]: Rust={} C++={}", i, st2.y, cpp);
    }

    assert_eq!(st.is_stalled, ODOM_STALL, "stall flag mismatch");
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
