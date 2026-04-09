//! 3×3 Rotation matrices
//!
//! Direct translation from C++ `rotation_matrices.hpp` using nalgebra.

use nalgebra::{Matrix3, Vector3};

/// Rotation matrix around X axis
pub fn rotx(angle: f64) -> Matrix3<f64> {
    let (s, c) = angle.sin_cos();
    Matrix3::new(
        1.0, 0.0, 0.0,
        0.0, c, -s,
        0.0, s, c,
    )
}

/// Rotation matrix around Y axis
pub fn roty(angle: f64) -> Matrix3<f64> {
    let (s, c) = angle.sin_cos();
    Matrix3::new(
        c, 0.0, s,
        0.0, 1.0, 0.0,
        -s, 0.0, c,
    )
}

/// Rotation matrix around Z axis
pub fn rotz(angle: f64) -> Matrix3<f64> {
    let (s, c) = angle.sin_cos();
    Matrix3::new(
        c, -s, 0.0,
        s, c, 0.0,
        0.0, 0.0, 1.0,
    )
}

/// Combined rotation: Rx(roll) * Ry(pitch) * Rz(yaw)
/// Equivalent to C++ rotxyz(roll, pitch, yaw)
/// Order: intrinsic rotations — roll first, then pitch, then yaw
pub fn rotxyz(roll: f64, pitch: f64, yaw: f64) -> Matrix3<f64> {
    // .sin_cos() returns (sin, cos)
    let (sa, ca) = roll.sin_cos();    // sa=sin(roll),  ca=cos(roll)
    let (sb, cb) = pitch.sin_cos();   // sb=sin(pitch), cb=cos(pitch)
    let (sg, cg) = yaw.sin_cos();     // sg=sin(yaw),   cg=cos(yaw)

    Matrix3::new(
        cb * cg,   -cb * sg,                   sb,
        sa * sb * cg + ca * sg,  -sa * sb * sg + ca * cg,  -sa * cb,
        -ca * sb * cg + sa * sg,  ca * sb * sg + sa * cg,  ca * cb,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rotx_zero_is_identity() {
        assert_eq!(rotx(0.0), Matrix3::identity());
    }

    #[test]
    fn roty_zero_is_identity() {
        assert_eq!(roty(0.0), Matrix3::identity());
    }

    #[test]
    fn rotz_zero_is_identity() {
        assert_eq!(rotz(0.0), Matrix3::identity());
    }

    #[test]
    fn rotxyz_zero_is_identity() {
        assert_eq!(rotxyz(0.0, 0.0, 0.0), Matrix3::identity());
    }

    #[test]
    fn rotx_pi2() {
        let m = rotx(std::f64::consts::FRAC_PI_2);
        assert!((m[(1, 1)] - 0.0).abs() < 1e-10);
        assert!((m[(1, 2)] + 1.0).abs() < 1e-10);
    }
}
