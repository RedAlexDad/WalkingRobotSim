//! Inverse Kinematics — compute joint angles from foot positions
//!
//! Direct translation from C++ `inverse_kinematics.cpp`.
//! Pipeline: leg_positions → compute_local_positions → compute_all_joint_angles

use crate::math::rotation::rotxyz;
use crate::math::transform::homog_transform_inverse;
use nalgebra::{Matrix3, Matrix4, SMatrix, Vector3, Vector4};

/// Fixed rotation matrix for legs: R = rotxyz(pi/2, -pi/2, 0)
fn r_legs() -> Matrix3<f64> {
    Matrix3::new(0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
}

/// Compute local positions for all 4 legs
/// Returns 3x4 matrix: each column is (x, y, z) for one leg
pub fn compute_local_positions(
    leg_positions: &SMatrix<f64, 3, 4>, // 3x4: columns are legs
    body_length: f64,
    body_width: f64,
    dx: f64,
    dy: f64,
    dz: f64,
    roll: f64,
    pitch: f64,
    yaw: f64,
) -> SMatrix<f64, 3, 4> {
    let r_legs = r_legs();

    // T_blwbl — body transformation
    let mut t_blwbl = Matrix4::identity();
    t_blwbl.fixed_view_mut::<3, 3>(0, 0).copy_from(&rotxyz(roll, pitch, yaw));
    t_blwbl[(0, 3)] = dx;
    t_blwbl[(1, 3)] = dy;
    t_blwbl[(2, 3)] = dz;

    let hl = 0.5 * body_length;
    let hw = 0.5 * body_width;

    let make_leg_t = |tx, ty, tz| {
        let mut t = Matrix4::identity();
        t.fixed_view_mut::<3, 3>(0, 0).copy_from(&r_legs);
        t[(0, 3)] = tx;
        t[(1, 3)] = ty;
        t[(2, 3)] = tz;
        t
    };

    // FR, FL, RR, RL — same order as C++ compute_local_positions
    let t_leg = [
        t_blwbl * make_leg_t(hl, -hw, 0.0),   // FR: (hl, -hw)
        t_blwbl * make_leg_t(hl, hw, 0.0),    // FL: (hl, hw)
        t_blwbl * make_leg_t(-hl, -hw, 0.0),  // RR: (-hl, -hw)
        t_blwbl * make_leg_t(-hl, hw, 0.0),   // RL: (-hl, hw)
    ];

    // Inverse transformation for each leg
    let mut result = SMatrix::<f64, 3, 4>::zeros();
    for i in 0..4 {
        let inv_t = homog_transform_inverse(&t_leg[i]);
        let leg_pos_h = Vector4::new(
            leg_positions[(0, i)],
            leg_positions[(1, i)],
            leg_positions[(2, i)],
            1.0,
        );
        let pos_local = inv_t * leg_pos_h;
        result[(0, i)] = pos_local.x;
        result[(1, i)] = pos_local.y;
        result[(2, i)] = pos_local.z;
    }

    result
}

/// Compute joint angles for a single leg
/// Returns [theta1 (hip), theta3 (thigh), theta4 (calf)]
pub fn compute_joint_angles_for_leg(x: f64, y: f64, z: f64, leg_index: usize, l1: f64, l2: f64, l3: f64, l4: f64) -> [f64; 3] {
    const LEG_SIGNS: [f64; 4] = [1.0, -1.0, 1.0, -1.0];

    let l2_sq = l2 * l2;
    let f_sq = x * x + y * y - l2_sq;
    let f = if f_sq > 0.0 { f_sq.sqrt() } else { 0.0 };
    let g = f - l1;
    let h = (g * g + z * z).sqrt();

    let theta1 = -y.atan2(x) - f.atan2(l2 * LEG_SIGNS[leg_index]);

    let d = (h * h - l3 * l3 - l4 * l4) / (2.0 * l3 * l4);
    let d = d.clamp(-1.0, 1.0);

    let theta4 = -(1.0 - d * d).sqrt().atan2(d);
    let theta3 = z.atan2(g) - (l4 * theta4.sin()).atan2(l3 + l4 * theta4.cos());

    [theta1, theta3, theta4]
}

/// Compute joint angles for all 4 legs
/// Input: 3x4 matrix (columns are legs)
/// Returns: 12-element array [hip0, thigh0, calf0, hip1, thigh1, calf1, ...]
pub fn compute_all_joint_angles(
    positions: &SMatrix<f64, 3, 4>, // 3x4
    l1: f64,
    l2: f64,
    l3: f64,
    l4: f64,
) -> [f64; 12] {
    let mut angles = [0.0; 12];

    for i in 0..4 {
        let x = positions[(0, i)];
        let y = positions[(1, i)];
        let z = positions[(2, i)];

        let [theta1, theta3, theta4] = compute_joint_angles_for_leg(x, y, z, i, l1, l2, l3, l4);

        let idx = i * 3;
        angles[idx] = theta1;
        angles[idx + 1] = theta3;
        angles[idx + 2] = theta4;
    }

    angles
}

/// Full inverse kinematics pipeline:
/// leg_positions (3x4) → local_positions → joint_angles (12)
pub fn inverse_kinematics(
    leg_positions: &SMatrix<f64, 3, 4>,
    body_length: f64,
    body_width: f64,
    l1: f64,
    l2: f64,
    l3: f64,
    l4: f64,
    dx: f64,
    dy: f64,
    dz: f64,
    roll: f64,
    pitch: f64,
    yaw: f64,
) -> [f64; 12] {
    let local = compute_local_positions(leg_positions, body_length, body_width, dx, dy, dz, roll, pitch, yaw);
    compute_all_joint_angles(&local, l1, l2, l3, l4)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_params() -> (f64, f64, f64, f64, f64, f64) {
        (0.0, 0.0955, 0.213, 0.213, 0.3762, 0.0935)
    }

    #[test]
    fn test_compute_joint_angles_clamping() {
        let (l1, l2, l3, l4, _, _) = default_params();

        // Test that D value is properly clamped
        // When H is very large, D could exceed [-1, 1]
        let angles = compute_joint_angles_for_leg(1.0, 0.0, -1.0, 0, l1, l2, l3, l4);

        // Should not panic, theta4 should be in valid range
        assert!(angles[2].abs() <= std::f64::consts::PI, "theta4 out of range: {}", angles[2]);
    }

    #[test]
    fn test_compute_joint_angles_f_zero() {
        let (l1, l2, l3, l4, _, _) = default_params();

        // When x*x + y*y = l2*l2, F = 0
        let x = 0.0;
        let y = l2;
        let z = -0.1;

        let angles = compute_joint_angles_for_leg(x, y, z, 0, l1, l2, l3, l4);

        // Should handle F=0 gracefully
        assert!(angles[0].is_finite());
        assert!(angles[1].is_finite());
        assert!(angles[2].is_finite());
    }
}
