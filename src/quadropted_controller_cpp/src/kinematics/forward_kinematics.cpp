#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"

#include <cmath>

#include "quadropted_controller_cpp/utils/math_utils.hpp"

namespace quadropted {

Eigen::Vector3d compute_leg_fk_chain(double theta_hip, double theta_thigh, double theta_calf,
                                     const Eigen::Matrix4d& T_base, const Eigen::Matrix4d& T_thigh_t,
                                     const Eigen::Matrix4d& T_calf_t, const Eigen::Matrix4d& T_foot) {
    Eigen::Matrix4d T_hip = homog_transform(0, 0, 0, 0, 0, theta_hip);
    Eigen::Matrix4d T_thigh = homog_transform(0, 0, 0, 0, theta_thigh, 0);
    Eigen::Matrix4d T_calf = homog_transform(0, 0, 0, 0, theta_calf, 0);

    Eigen::Matrix4d T_total = T_base * T_hip * T_thigh * T_thigh_t * T_calf * T_calf_t * T_foot;

    Eigen::Vector4d foot_hom = T_total * Eigen::Vector4d(0, 0, 0, 1);
    return foot_hom.head<3>();
}

ForwardKinematics::ForwardKinematics(double body_length, double body_width, double l1, double l2, double l3, double l4)
    : l1_(l1),
      l2_(l2),
      l3_(l3),
      l4_(l4),
      T_thigh_t_(homog_transform(l2, 0, 0, 0, 0, 0)),
      T_calf_t_(homog_transform(l3, 0, 0, 0, 0, 0)),
      T_foot_(homog_transform(l4, 0, 0, 0, 0, 0)) {
    double hl = 0.5 * body_length;
    double hw = 0.5 * body_width;
    double origins[4][2] = {{hl, -hw}, {hl, hw}, {-hl, -hw}, {-hl, hw}};
    for (int i = 0; i < 4; ++i) {
        Eigen::Matrix4d& T = T_base_[i];
        T(0, 0) = 1;
        T(0, 1) = 0;
        T(0, 2) = 0;
        T(0, 3) = origins[i][0];
        T(1, 0) = 0;
        T(1, 1) = 1;
        T(1, 2) = 0;
        T(1, 3) = origins[i][1];
        T(2, 0) = 0;
        T(2, 1) = 0;
        T(2, 2) = 1;
        T(2, 3) = -l1;
        T(3, 0) = 0;
        T(3, 1) = 0;
        T(3, 2) = 0;
        T(3, 3) = 1;
    }
}

std::vector<Eigen::Vector3d> ForwardKinematics::forward_kinematics_all_legs(
    const std::vector<double>& joint_angles) const {
    if (joint_angles.size() != 12) {
        throw std::invalid_argument("Expected 12 joint angles.");
    }

    std::vector<Eigen::Vector3d> foot_positions;
    foot_positions.reserve(4);

    for (int leg = 0; leg < 4; ++leg) {
        int idx = leg * 3;
        double theta_hip = joint_angles[idx];
        double theta_thigh = joint_angles[idx + 1];
        double theta_calf = joint_angles[idx + 2];

        foot_positions.push_back(
            compute_leg_fk_chain(theta_hip, theta_thigh, theta_calf, T_base_[leg], T_thigh_t_, T_calf_t_, T_foot_));
    }

    return foot_positions;
}

FootPositions ForwardKinematics::forward_kinematics_all_legs(const JointAngles& joint_angles) const {
    FootPositions foot_positions;

    for (int leg = 0; leg < 4; ++leg) {
        int idx = leg * 3;
        double theta_hip = joint_angles[idx];
        double theta_thigh = joint_angles[idx + 1];
        double theta_calf = joint_angles[idx + 2];

        foot_positions[leg] =
            compute_leg_fk_chain(theta_hip, theta_thigh, theta_calf, T_base_[leg], T_thigh_t_, T_calf_t_, T_foot_);
    }

    return foot_positions;
}

}  // namespace quadropted
