#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"

#include <array>
#include <cmath>
#include <stdexcept>

#include "quadropted_controller_cpp/utils/fast_math.hpp"
#include "quadropted_controller_cpp/utils/math_utils.hpp"

namespace quadropted {

Eigen::Matrix<double, 4, 3> compute_local_positions(const LegsMatrix& leg_positions, double body_length,
                                                    double body_width, double dx, double dy, double dz, double roll,
                                                    double pitch, double yaw) noexcept {
    // Фиксированная матрица вращения для ног: R = rotxyz(pi/2, -pi/2, 0)
    static const Eigen::Matrix3d R_legs =
        (Eigen::Matrix3d() << 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0).finished();

    // T_blwbl — преобразование корпуса
    Eigen::Matrix4d T_blwbl;
    T_blwbl.block<3, 3>(0, 0) = rotxyz(roll, pitch, yaw);
    T_blwbl(0, 3) = dx;
    T_blwbl(1, 3) = dy;
    T_blwbl(2, 3) = dz;
    T_blwbl(3, 0) = 0;
    T_blwbl(3, 1) = 0;
    T_blwbl(3, 2) = 0;
    T_blwbl(3, 3) = 1;

    double hl = 0.5 * body_length;
    double hw = 0.5 * body_width;

    // Матрицы преобразования для каждой ноги
    auto make_leg_T = [&](double tx, double ty, double tz) {
        Eigen::Matrix4d T = Eigen::Matrix4d::Identity();
        T.block<3, 3>(0, 0) = R_legs;
        T(0, 3) = tx;
        T(1, 3) = ty;
        T(2, 3) = tz;
        return T;
    };

    Eigen::Matrix4d T_leg[4];
    T_leg[0] = T_blwbl * make_leg_T(hl, -hw, 0);   // FR
    T_leg[1] = T_blwbl * make_leg_T(hl, hw, 0);    // FL
    T_leg[2] = T_blwbl * make_leg_T(-hl, -hw, 0);  // RR
    T_leg[3] = T_blwbl * make_leg_T(-hl, hw, 0);   // RL

    // Обратное преобразование для каждой ноги
    Eigen::Matrix<double, 4, 3> result;
    result.setZero();
    for (int i = 0; i < 4; ++i) {
        Eigen::Matrix4d inv_T = homog_transform_inverse(T_leg[i]);
        Eigen::Vector4d leg_pos_h;
        leg_pos_h << leg_positions.col(i), 1.0;
        Eigen::Vector4d pos_local = inv_T * leg_pos_h;
        result.row(i) = pos_local.head<3>();
    }

    return result;
}

std::array<double, 3> compute_joint_angles_for_leg(double x, double y, double z, int leg_index, double l1, double l2,
                                                   double l3, double l4) noexcept {
    static const double LEG_SIGNS[] = {1.0, -1.0, 1.0, -1.0};

    double l2_sq = l2 * l2;
    double f_sq = x * x + y * y - l2_sq;
    double F = (f_sq > 0.0) ? std::sqrt(f_sq) : 0.0;
    double G = F - l1;
    double H = std::sqrt(G * G + z * z);

    double theta1 = -fast_atan2(y, x) - fast_atan2(F, l2 * LEG_SIGNS[leg_index]);

    double _2l3l4 = 2.0 * l3 * l4;
    double l3sq_l4sq = l3 * l3 + l4 * l4;
    double D = (H * H - l3sq_l4sq) / _2l3l4;
    if (D > 1.0)
        D = 1.0;
    else if (D < -1.0)
        D = -1.0;

    double sqrt_1_D2 = std::sqrt(std::max(0.0, 1.0 - D * D));
    double theta4 = -fast_atan2(sqrt_1_D2, D);
    double theta3 = fast_atan2(z, G) - fast_atan2(-l4 * sqrt_1_D2, l3 + l4 * D);

    return {theta1, theta3, theta4};
}

InverseKinematics::InverseKinematics(double body_length, double body_width, double l1, double l2, double l3, double l4)
    : fk_(body_length, body_width, l1, l2, l3, l4),
      body_length_(body_length),
      body_width_(body_width),
      l1_(l1),
      l2_(l2),
      l3_(l3),
      l4_(l4) {
    static const Eigen::Matrix3d R_legs =
        (Eigen::Matrix3d() << 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0).finished();
    double hl = 0.5 * body_length;
    double hw = 0.5 * body_width;
    double leg_origins[4][3] = {{hl, -hw, 0.0}, {hl, hw, 0.0}, {-hl, -hw, 0.0}, {-hl, hw, 0.0}};
    for (int i = 0; i < 4; ++i) {
        Eigen::Matrix4d T = Eigen::Matrix4d::Identity();
        T.block<3, 3>(0, 0) = R_legs;
        T(0, 3) = leg_origins[i][0];
        T(1, 3) = leg_origins[i][1];
        T(2, 3) = leg_origins[i][2];
        inv_T_bl_base_[i] = homog_transform_inverse(T);
    }
    double _2l3l4 = 2.0 * l3 * l4;
    l2_sq_ = l2 * l2;
    inv_2l3l4_ = 1.0 / _2l3l4;
    l3sq_l4sq_ = l3 * l3 + l4 * l4;
}

Eigen::Matrix<double, 4, 3> InverseKinematics::get_local_positions(const LegsMatrix& leg_positions, double dx,
                                                                   double dy, double dz, double roll, double pitch,
                                                                   double yaw) const noexcept {
    if (leg_positions.rows() != 3 || leg_positions.cols() != 4) {
        throw std::invalid_argument("leg_positions must be 3x4 (3 coordinates x 4 legs)");
    }
    Eigen::Matrix4d T_blwbl;
    T_blwbl.block<3, 3>(0, 0) = rotxyz(roll, pitch, yaw);
    T_blwbl(0, 3) = dx;
    T_blwbl(1, 3) = dy;
    T_blwbl(2, 3) = dz;
    T_blwbl(3, 0) = 0;
    T_blwbl(3, 1) = 0;
    T_blwbl(3, 2) = 0;
    T_blwbl(3, 3) = 1;

    Eigen::Matrix4d inv_T_blwbl = homog_transform_inverse(T_blwbl);

    Eigen::Matrix<double, 4, 3> result;
    result.setZero();
    for (int i = 0; i < 4; ++i) {
        Eigen::Matrix4d inv_T = inv_T_bl_base_[i] * inv_T_blwbl;
        Eigen::Vector4d leg_pos_h;
        leg_pos_h << leg_positions.col(i), 1.0;
        Eigen::Vector4d pos_local = inv_T * leg_pos_h;
        result.row(i) = pos_local.head<3>();
    }

    return result;
}

std::array<double, 12> InverseKinematics::inverse_kinematics(const LegsMatrix& leg_positions, double dx, double dy,
                                                             double dz, double roll, double pitch,
                                                             double yaw) const noexcept {
    auto positions = get_local_positions(leg_positions, dx, dy, dz, roll, pitch, yaw);
    return detail::compute_all_joint_angles(positions, l1_, l2_, l3_, l4_, l2_sq_, inv_2l3l4_, l3sq_l4sq_);
}

}  // namespace quadropted
