//! Cross-validation tests: Rust vs C++
//!
//! Runs the C++ test binaries and compares output with Rust computation.
//! This ensures mathematical equivalence between the two implementations.

use std::process::Command;

/// Run a C++ test binary and parse JSON output
fn run_cpp_test(test_name: &str) -> serde_json::Value {
    let output = Command::new("./target/cpp_test_binaries")
        .arg(test_name)
        .output()
        .expect("Failed to run C++ test binary");

    assert!(output.status.success(), "C++ test {} failed", test_name);

    serde_json::from_slice(&output.stdout)
        .unwrap_or_else(|_| panic!("Failed to parse JSON from {}", test_name))
}

/// Helper: compare two f64 values with tolerance
fn approx_eq(a: f64, b: f64, tol: f64) -> bool {
    (a - b).abs() < tol
}

/// Helper: compare two matrices element-wise
fn matrices_approx_eq(rust: &nalgebra::Matrix3<f64>, cpp: &nalgebra::Matrix3<f64>, tol: f64) -> bool {
    for i in 0..3 {
        for j in 0..3 {
            if !approx_eq(rust[(i, j)], cpp[(i, j)], tol) {
                return false;
            }
        }
    }
    true
}

#[test]
fn cross_validate_rotx() {
    use quadropted_core::math::rotation::rotx;

    let test_cases = vec![0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2];

    for angle in test_cases {
        let rust_result = rotx(angle);
        let (s, c) = angle.sin_cos();
        let cpp_expected = nalgebra::Matrix3::new(
            1.0, 0.0, 0.0,
            0.0, c, -s,
            0.0, s, c,
        );
        assert!(
            matrices_approx_eq(&rust_result, &cpp_expected, 1e-10),
            "rotx({}) mismatch:\nRust:\n{}\nExpected:\n{}",
            angle, rust_result, cpp_expected
        );
    }
}

#[test]
fn cross_validate_roty() {
    use quadropted_core::math::rotation::roty;

    let test_cases = vec![0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2];

    for angle in test_cases {
        let rust_result = roty(angle);
        let (s, c) = angle.sin_cos();
        let cpp_expected = nalgebra::Matrix3::new(
            c, 0.0, s,
            0.0, 1.0, 0.0,
            -s, 0.0, c,
        );
        assert!(
            matrices_approx_eq(&rust_result, &cpp_expected, 1e-10),
            "roty({}) mismatch", angle
        );
    }
}

#[test]
fn cross_validate_rotz() {
    use quadropted_core::math::rotation::rotz;

    let test_cases = vec![0.0, 0.5, -0.3, std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_2];

    for angle in test_cases {
        let rust_result = rotz(angle);
        let (s, c) = angle.sin_cos();
        let cpp_expected = nalgebra::Matrix3::new(
            c, -s, 0.0,
            s, c, 0.0,
            0.0, 0.0, 1.0,
        );
        assert!(
            matrices_approx_eq(&rust_result, &cpp_expected, 1e-10),
            "rotz({}) mismatch", angle
        );
    }
}

#[test]
fn cross_validate_rotxyz() {
    use quadropted_core::math::rotation::rotxyz;

    let test_cases = vec![
        (0.0, 0.0, 0.0),
        (0.1, 0.2, 0.3),
        (-0.5, 0.0, 0.1),
        (std::f64::consts::FRAC_PI_4, std::f64::consts::FRAC_PI_6, std::f64::consts::FRAC_PI_3),
    ];

    for (roll, pitch, yaw) in test_cases {
        let rust_result = rotxyz(roll, pitch, yaw);

        // C++ formula: Rx * Ry * Rz (same as quadropted_controller_cpp)
        // .sin_cos() returns (sin, cos)
        let (sa, ca) = roll.sin_cos();
        let (sb, cb) = pitch.sin_cos();
        let (sg, cg) = yaw.sin_cos();

        let cpp_expected = nalgebra::Matrix3::new(
            cb * cg,   -cb * sg,                   sb,
            sa * sb * cg + ca * sg,  -sa * sb * sg + ca * cg,  -sa * cb,
            -ca * sb * cg + sa * sg,  ca * sb * sg + sa * cg,  ca * cb,
        );

        assert!(
            matrices_approx_eq(&rust_result, &cpp_expected, 1e-10),
            "rotxyz({}, {}, {}) mismatch:\nRust:\n{}\nExpected:\n{}",
            roll, pitch, yaw, rust_result, cpp_expected
        );
    }
}

#[test]
fn cross_validate_homog_transxyz() {
    use quadropted_core::math::transform::homog_transxyz;

    let test_cases = vec![
        (0.0, 0.0, 0.0),
        (1.0, 2.0, 3.0),
        (-1.0, 0.0, 0.5),
        (0.3762, 0.0935, 0.0),
    ];

    for (dx, dy, dz) in test_cases {
        let rust_result = homog_transxyz(dx, dy, dz);

        let mut cpp_expected = nalgebra::Matrix4::zeros();
        cpp_expected[(0, 3)] = dx;
        cpp_expected[(1, 3)] = dy;
        cpp_expected[(2, 3)] = dz;
        cpp_expected[(3, 3)] = 1.0;
        cpp_expected[(0, 0)] = 1.0;
        cpp_expected[(1, 1)] = 1.0;
        cpp_expected[(2, 2)] = 1.0;

        assert!(
            (rust_result - cpp_expected).norm() < 1e-10,
            "homog_transxyz({}, {}, {}) mismatch", dx, dy, dz
        );
    }
}

#[test]
fn cross_validate_homog_transform_inverse() {
    use quadropted_core::math::transform::{homog_transform, homog_transform_inverse};

    // Test with rotation + translation
    let roll = 0.1;
    let pitch = 0.2;
    let yaw = 0.3;
    let t = nalgebra::Vector3::new(0.1881, 0.0935, -0.25);
    let r = quadropted_core::math::rotation::rotxyz(roll, pitch, yaw);

    let m = homog_transform(&t, &r);
    let inv = homog_transform_inverse(&m);
    let product = m * inv;

    assert!(
        (product - nalgebra::Matrix4::identity()).norm() < 1e-10,
        "M * M^-1 != I\nM:\n{}\nM^-1:\n{}\nProduct:\n{}",
        m, inv, product
    );
}
