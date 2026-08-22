//! 4×4 Homogeneous transformation matrices
//!
//! Direct translation from C++ `homogeneous_transforms.hpp`.

use nalgebra::{Matrix3, Matrix4, Vector3, Vector4};

/// Homogeneous transformation with translation only
pub fn homog_transxyz(dx: f64, dy: f64, dz: f64) -> Matrix4<f64> {
    Matrix4::new(
        1.0, 0.0, 0.0, dx,
        0.0, 1.0, 0.0, dy,
        0.0, 0.0, 1.0, dz,
        0.0, 0.0, 0.0, 1.0,
    )
}

/// Homogeneous transformation: rotation + translation
pub fn homog_transform(translation: &Vector3<f64>, rotation: &Matrix3<f64>) -> Matrix4<f64> {
    let mut m = Matrix4::zeros();
    m.fixed_view_mut::<3, 3>(0, 0).copy_from(rotation);
    m.fixed_view_mut::<3, 1>(0, 3).copy_from(translation);
    m[(3, 3)] = 1.0;
    m
}

/// Inverse of a homogeneous transformation matrix
/// For SE(3) matrices: [R t; 0 1]^-1 = [R^T -R^T*t; 0 1]
pub fn homog_transform_inverse(m: &Matrix4<f64>) -> Matrix4<f64> {
    let r = m.fixed_view::<3, 3>(0, 0);
    let t = m.fixed_view::<3, 1>(0, 3);
    let r_inv = r.transpose();
    let t_inv = -r_inv * t;

    let mut inv = Matrix4::zeros();
    inv.fixed_view_mut::<3, 3>(0, 0).copy_from(&r_inv);
    inv.fixed_view_mut::<3, 1>(0, 3).copy_from(&t_inv);
    inv[(3, 3)] = 1.0;
    inv
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_homog_transxyz() {
        let m = homog_transxyz(1.0, 2.0, 3.0);
        assert_eq!(m[(0, 3)], 1.0);
        assert_eq!(m[(1, 3)], 2.0);
        assert_eq!(m[(2, 3)], 3.0);
        assert_eq!(m[(3, 3)], 1.0);
    }

    #[test]
    fn test_homog_transform_identity() {
        let t = Vector3::zeros();
        let r = Matrix3::identity();
        let m = homog_transform(&t, &r);
        assert_eq!(m, Matrix4::identity());
    }

    #[test]
    fn test_homog_transform_inverse() {
        let t = Vector3::new(1.0, 2.0, 3.0);
        let r = Matrix3::identity();
        let m = homog_transform(&t, &r);
        let inv = homog_transform_inverse(&m);
        let product = m * inv;
        assert!((product - Matrix4::identity()).norm() < 1e-10);
    }

    #[test]
    fn test_homog_transform_inverse_with_rotation() {
        // SE(3)-инверсия с не-identity поворотом: M * M^-1 = I
        use crate::math::rotation::rotxyz;
        let t = Vector3::new(0.5, -0.2, 0.1);
        let r = rotxyz(0.3, -0.2, 0.7);
        let m = homog_transform(&t, &r);
        let inv = homog_transform_inverse(&m);
        let product = m * inv;
        assert!((product - Matrix4::identity()).norm() < 1e-10);
    }

    #[test]
    fn test_homog_transform_inverse_translates_back() {
        // Применение inv к точке должно вернуть её в исходную систему координат
        use crate::math::rotation::rotxyz;
        let t = Vector3::new(1.0, 2.0, 3.0);
        let r = rotxyz(0.1, 0.2, 0.3);
        let m = homog_transform(&t, &r);
        let inv = homog_transform_inverse(&m);

        // Точка в исходном пространстве
        let p = Vector4::new(0.1, 0.2, 0.3, 1.0);
        let transformed = m * p;
        let roundtrip = inv * transformed;
        assert!((roundtrip - p).norm() < 1e-10, "roundtrip must restore point");
    }

    #[test]
    fn test_homog_transxyz_roundtrip() {
        let m = homog_transxyz(1.0, -2.0, 0.5);
        let inv = homog_transform_inverse(&m);
        let p = Vector4::new(1.0, 1.0, 1.0, 1.0);
        let back = inv * (m * p);
        assert!((back - p).norm() < 1e-12);
    }
}
