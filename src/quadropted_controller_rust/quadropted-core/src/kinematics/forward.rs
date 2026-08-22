//! Forward Kinematics — compute foot positions from joint angles
//!
//! Direct translation from C++ `forward_kinematics.cpp`.
//! Uses homogeneous transform chains: T_base * T_hip * T_thigh * ... * T_foot

use crate::math::rotation::rotxyz;
use nalgebra::{Matrix4, Vector2, Vector3, Vector4};

/// Get base position for a leg (FR, FL, RR, RL)
/// Order matches C++ compute_local_positions: FR=(hl,-hw), FL=(hl,hw), RR=(-hl,-hw), RL=(-hl,hw)
pub fn leg_base_positions(leg_index: usize, body_length: f64, body_width: f64) -> Vector2<f64> {
    let hl = body_length / 2.0;
    let hw = body_width / 2.0;
    match leg_index {
        0 => nalgebra::Vector2::new(hl, -hw),  // FR
        1 => nalgebra::Vector2::new(hl, hw),   // FL
        2 => nalgebra::Vector2::new(-hl, -hw), // RR
        3 => nalgebra::Vector2::new(-hl, hw),  // RL
        _ => panic!("Invalid leg_index. Must be 0 (FR), 1 (FL), 2 (RR), or 3 (RL)."),
    }
}

/// Compute forward kinematics chain for a single leg
/// Returns foot position in world frame
pub fn compute_leg_fk_chain(
    theta_hip: f64,
    theta_thigh: f64,
    theta_calf: f64,
    base_x: f64,
    base_y: f64,
    l1: f64,
    l2: f64,
    l3: f64,
    l4: f64,
) -> Vector3<f64> {
    let build_homog_transform = |dx, dy, dz, alpha, beta, gamma| {
        let mut t = Matrix4::identity();
        t.fixed_view_mut::<3, 3>(0, 0).copy_from(&rotxyz(alpha, beta, gamma));
        t[(0, 3)] = dx;
        t[(1, 3)] = dy;
        t[(2, 3)] = dz;
        t
    };

    let t_base = build_homog_transform(base_x, base_y, -l1, 0.0, 0.0, 0.0);
    let t_hip = build_homog_transform(0.0, 0.0, 0.0, 0.0, 0.0, theta_hip);
    let t_thigh = build_homog_transform(0.0, 0.0, 0.0, 0.0, theta_thigh, 0.0);
    let t_thigh_t = build_homog_transform(l2, 0.0, 0.0, 0.0, 0.0, 0.0);
    let t_calf = build_homog_transform(0.0, 0.0, 0.0, 0.0, theta_calf, 0.0);
    let t_calf_t = build_homog_transform(l3, 0.0, 0.0, 0.0, 0.0, 0.0);
    let t_foot = build_homog_transform(l4, 0.0, 0.0, 0.0, 0.0, 0.0);

    let t_total = t_base * t_hip * t_thigh * t_thigh_t * t_calf * t_calf_t * t_foot;

    let foot_hom = t_total * Vector4::new(0.0, 0.0, 0.0, 1.0);
    Vector3::new(foot_hom.x, foot_hom.y, foot_hom.z)
}

/// Forward kinematics for all 4 legs
pub fn forward_kinematics_all_legs(
    joint_angles: &[f64; 12],
    body_length: f64,
    body_width: f64,
    l1: f64,
    l2: f64,
    l3: f64,
    l4: f64,
) -> [Vector3<f64>; 4] {
    let mut foot_positions = [Vector3::zeros(); 4];

    for leg in 0..4 {
        let idx = leg * 3;
        let theta_hip = joint_angles[idx];
        let theta_thigh = joint_angles[idx + 1];
        let theta_calf = joint_angles[idx + 2];

        let base = leg_base_positions(leg, body_length, body_width);
        foot_positions[leg] = compute_leg_fk_chain(
            theta_hip, theta_thigh, theta_calf, base.x, base.y, l1, l2, l3, l4,
        );
    }

    foot_positions
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_body() -> (f64, f64, f64, f64, f64, f64) {
        // Unitree GO2 dimensions: body=(0.3762, 0.0935), legs=(0.0, 0.0955, 0.213, 0.213)
        (0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213)
    }

    #[test]
    fn test_leg_base_positions() {
        let (bl, bw, _, _, _, _) = default_body();
        // Order: FR=(hl,-hw), FL=(hl,hw), RR=(-hl,-hw), RL=(-hl,hw)
        assert_eq!(leg_base_positions(0, bl, bw), nalgebra::Vector2::new(0.1881, -0.04675));
        assert_eq!(leg_base_positions(1, bl, bw), nalgebra::Vector2::new(0.1881, 0.04675));
        assert_eq!(leg_base_positions(2, bl, bw), nalgebra::Vector2::new(-0.1881, -0.04675));
        assert_eq!(leg_base_positions(3, bl, bw), nalgebra::Vector2::new(-0.1881, 0.04675));
    }

    #[test]
    fn test_fk_zero_joints() {
        let (bl, bw, l1, l2, l3, l4) = default_body();
        let angles = [0.0; 12];
        let result = forward_kinematics_all_legs(&angles, bl, bw, l1, l2, l3, l4);

        // With zero joints, foot should be at:
        // x = base_x + l2 + l3 + l4
        // y = base_y
        // z = -l1
        let expected_x = l2 + l3 + l4; // 0.0955 + 0.213 + 0.213 = 0.5215
        let expected_z = -l1; // 0.0

        for leg in 0..4 {
            let base = leg_base_positions(leg, bl, bw);
            assert!((result[leg].x - (base.x + expected_x)).abs() < 1e-10,
                "Leg {} X: expected {}, got {}", leg, base.x + expected_x, result[leg].x);
            assert!((result[leg].y - base.y).abs() < 1e-10,
                "Leg {} Y: expected {}, got {}", leg, base.y, result[leg].y);
            assert!((result[leg].z - expected_z).abs() < 1e-10,
                "Leg {} Z: expected {}, got {}", leg, expected_z, result[leg].z);
        }
    }

    #[test]
    #[should_panic(expected = "Invalid leg_index")]
    fn test_leg_base_positions_panics_on_invalid() {
        leg_base_positions(4, 0.3762, 0.0935);
    }

    #[test]
    fn test_fk_bent_thigh_changes_z() {
        // Согнутое колено (thigh>0) меняет Z стопы относительно выпрямленной ноги
        let (bl, bw, l1, l2, l3, l4) = default_body();
        let zero = forward_kinematics_all_legs(&[0.0; 12], bl, bw, l1, l2, l3, l4);

        let mut angles = [0.0; 12];
        angles[1] = 0.5; // thigh для ноги 0 (FR)
        let result = forward_kinematics_all_legs(&angles, bl, bw, l1, l2, l3, l4);

        // thigh меняет z (положительный угол здесь опускает стопу вниз)
        assert!(
            (result[0].z - zero[0].z).abs() > 0.01,
            "bent thigh should change foot z: {} vs {}",
            result[0].z, zero[0].z
        );
        assert!(result[0].z.is_finite());
    }

    #[test]
    fn test_fk_symmetric_stance_is_mirrored() {
        let (bl, bw, l1, l2, l3, l4) = default_body();
        let angles = [0.0; 12];
        let result = forward_kinematics_all_legs(&angles, bl, bw, l1, l2, l3, l4);
        // FR и FL зеркальны по Y (база: FR=(+hl,-hw), FL=(+hl,+hw))
        assert!((result[0].y + result[1].y).abs() < 1e-10, "FR y {} vs FL y {}", result[0].y, result[1].y);
        // FR и RR зеркальны по Y тоже? Нет — FR y=-hw, RR y=-hw (обе слева по y).
        // Проверим равенство y у ног одной стороны: FR и RR оба y=-hw
        assert!((result[0].y - result[2].y).abs() < 1e-10, "FR y {} vs RR y {}", result[0].y, result[2].y);
        // X-координаты FR/FL равны (обе спереди)
        assert!((result[0].x - result[1].x).abs() < 1e-10);
    }

    #[test]
    fn test_fk_hip_rotation_swings_foot() {
        let (bl, bw, l1, l2, l3, l4) = default_body();
        let mut angles = [0.0; 12];
        // hip = 0.3 рад для ноги 0 → стопа сдвигается по Y
        angles[0] = 0.3;
        let result = forward_kinematics_all_legs(&angles, bl, bw, l1, l2, l3, l4);
        let zero = forward_kinematics_all_legs(&[0.0; 12], bl, bw, l1, l2, l3, l4);
        assert!(
            (result[0].y - zero[0].y).abs() > 0.01,
            "hip rotation should move foot y: {} vs {}",
            result[0].y, zero[0].y
        );
    }
}
