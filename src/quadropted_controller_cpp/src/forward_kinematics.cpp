#include "quadropted_controller_cpp/forward_kinematics.hpp"

namespace quadropted {

Eigen::Vector2d LegBasePositions::get(int leg_index, double body_length, double body_width) {
    double hl = body_length * 0.5;
    double hw = body_width * 0.5;
    switch (leg_index) {
        case 0: return { hl,  hw};  // FR
        case 1: return { hl, -hw};  // FL
        case 2: return {-hl,  hw};  // RR
        case 3: return {-hl, -hw};  // RL
        default: return {0, 0};
    }
}

Eigen::Vector3d compute_leg_fk_chain(
    double theta_hip, double theta_thigh, double theta_calf,
    double base_x, double base_y, double l1, double l2, double l3, double l4)
{
    Eigen::Matrix4d T = homog_transform(base_x, base_y, -l1, 0, 0, 0);
    T *= homog_transform(0, 0, 0, 0, 0, theta_hip);
    T *= homog_transform(0, 0, 0, 0, theta_thigh, 0);
    T *= homog_transform(l2, 0, 0, 0, 0, 0);
    T *= homog_transform(0, 0, 0, 0, theta_calf, 0);
    T *= homog_transform(l3, 0, 0, 0, 0, 0);
    T *= homog_transform(l4, 0, 0, 0, 0, 0);

    Eigen::Vector4d p = T * Eigen::Vector4d(0, 0, 0, 1);
    return p.head<3>();
}

ForwardKinematics::ForwardKinematics(double body_length, double body_width,
                      double l1, double l2, double l3, double l4)
    : body_length_(body_length), body_width_(body_width),
      l1_(l1), l2_(l2), l3_(l3), l4_(l4) {}

std::vector<Eigen::Vector3d> ForwardKinematics::forward_kinematics_all_legs(const std::vector<double>& joint_angles) const {
    std::vector<Eigen::Vector3d> positions(4);
    for (int leg = 0; leg < 4; ++leg) {
        int idx = leg * 3;
        auto base = LegBasePositions::get(leg, body_length_, body_width_);
        positions[leg] = compute_leg_fk_chain(
            joint_angles[idx], joint_angles[idx + 1], joint_angles[idx + 2],
            base.x(), base.y(), l1_, l2_, l3_, l4_);
    }
    return positions;
}

} // namespace quadropted
