#include "quadropted_controller_cpp/inverse_kinematics.hpp"

namespace quadropted {

Eigen::MatrixXd compute_local_positions(
    const Eigen::MatrixXd& leg_positions,  // (3, 4)
    double body_length, double body_width,
    double dx, double dy, double dz,
    double roll, double pitch, double yaw)
{
    Eigen::Matrix4d T_blwbl = homog_transform(dx, dy, dz, roll, pitch, yaw);
    double hl = body_length * 0.5, hw = body_width * 0.5;

    std::array<Eigen::Vector3d, 4> offsets = {
        Eigen::Vector3d{ hl, -hw, 0},
        Eigen::Vector3d{ hl,  hw, 0},
        Eigen::Vector3d{-hl, -hw, 0},
        Eigen::Vector3d{-hl,  hw, 0}
    };

    Eigen::Matrix4d leg_h = Eigen::Matrix4d::Zero();
    leg_h.topLeftCorner(3, 4) = leg_positions;
    leg_h.row(3).setOnes();

    Eigen::MatrixXd result(4, 3);
    for (int i = 0; i < 4; ++i) {
        Eigen::Matrix4d T_leg = homog_transform(offsets[i].x(), offsets[i].y(), offsets[i].z(),
                                                  M_PI_2, -M_PI_2, 0);
        Eigen::Matrix4d T_blw = T_blwbl * T_leg;
        Eigen::Matrix4d T_inv = homog_transform_inverse(T_blw);
        Eigen::Vector4d p = T_inv * leg_h.col(i);
        result.row(i) = p.head<3>();
    }
    return result.transpose();
}

std::array<double, 3> compute_joint_angles_for_leg(
    double x, double y, double z, int leg_index,
    double l1, double l2, double l3, double l4)
{
    static constexpr double LEG_SIGNS[] = {1.0, -1.0, 1.0, -1.0};

    double f_sq = x * x + y * y - l2 * l2;
    double F = std::sqrt(std::max(f_sq, 0.0));
    double G = F - l1;
    double H = std::sqrt(G * G + z * z);

    double theta1 = -std::atan2(y, x) - std::atan2(F, l2 * LEG_SIGNS[leg_index]);

    double D = (H * H - l3 * l3 - l4 * l4) / (2.0 * l3 * l4);
    D = std::max(-1.0, std::min(1.0, D));

    double theta4 = -std::atan2(std::sqrt(1.0 - D * D), D);
    double theta3 = std::atan2(z, G) - std::atan2(l4 * std::sin(theta4), l3 + l4 * std::cos(theta4));

    return {theta1, theta3, theta4};
}

std::vector<double> compute_all_joint_angles(
    const Eigen::MatrixXd& positions, double l1, double l2, double l3, double l4)
{
    std::vector<double> angles;
    angles.reserve(12);
    for (int i = 0; i < 4; ++i) {
        auto [t1, t3, t4] = compute_joint_angles_for_leg(
            positions(0, i), positions(1, i), positions(2, i),
            i, l1, l2, l3, l4);
        angles.push_back(t1);
        angles.push_back(t3);
        angles.push_back(t4);
    }
    return angles;
}

InverseKinematics::InverseKinematics(double body_length, double body_width,
                      double l1, double l2, double l3, double l4)
    : fk_(body_length, body_width, l1, l2, l3, l4),
      body_length_(body_length), body_width_(body_width),
      l1_(l1), l2_(l2), l3_(l3), l4_(l4) {}

Eigen::MatrixXd InverseKinematics::get_local_positions(const Eigen::MatrixXd& leg_positions,
                                         double dx, double dy, double dz,
                                         double roll, double pitch, double yaw) const {
    return compute_local_positions(leg_positions, body_length_, body_width_,
                                   dx, dy, dz, roll, pitch, yaw);
}

std::vector<double> InverseKinematics::inverse_kinematics(const Eigen::MatrixXd& leg_positions,
                                            double dx, double dy, double dz,
                                            double roll, double pitch, double yaw) const {
    auto local = get_local_positions(leg_positions, dx, dy, dz, roll, pitch, yaw);
    return compute_all_joint_angles(local, l1_, l2_, l3_, l4_);
}

} // namespace quadropted
