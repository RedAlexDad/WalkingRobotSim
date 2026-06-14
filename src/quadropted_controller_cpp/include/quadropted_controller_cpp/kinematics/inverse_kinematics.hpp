#pragma once
#include <Eigen/Dense>
#include <array>
#include <cmath>
#include <stdexcept>

#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/utils/fast_math.hpp"

namespace quadropted {

[[nodiscard]] Eigen::Matrix<double, 4, 3> compute_local_positions(const LegsMatrix& leg_positions, double body_length,
                                                                  double body_width, double dx, double dy, double dz,
                                                                  double roll, double pitch, double yaw) noexcept;

[[nodiscard]] std::array<double, 3> compute_joint_angles_for_leg(double x, double y, double z, int leg_index, double l1,
                                                                 double l2, double l3, double l4) noexcept;

namespace detail {

template <typename Derived>
[[nodiscard]] std::array<double, 12> compute_all_joint_angles(const Eigen::MatrixBase<Derived>& positions, double l1,
                                                              double l2, double l3, double l4, double l2_sq,
                                                              double inv_2l3l4, double l3sq_l4sq) noexcept {
    if (positions.rows() != 4 || positions.cols() != 3) {
        throw std::invalid_argument("positions must be 4x3 (4 legs x 3 coordinates)");
    }
    static const double LEG_SIGNS[] = {1.0, -1.0, 1.0, -1.0};

    std::array<double, 12> angles{};

    for (int i = 0; i < 4; ++i) {
        double x = positions(i, 0);
        double y = positions(i, 1);
        double z = positions(i, 2);

        double f_sq = x * x + y * y - l2_sq;
        double F = (f_sq > 0.0) ? std::sqrt(f_sq) : 0.0;
        double G = F - l1;
        double H = std::sqrt(G * G + z * z);

        double theta1 = -fast_atan2(y, x) - fast_atan2(F, l2 * LEG_SIGNS[i]);

        double D = (H * H - l3sq_l4sq) * inv_2l3l4;
        if (D > 1.0)
            D = 1.0;
        else if (D < -1.0)
            D = -1.0;

        double sqrt_1_D2 = std::sqrt(std::max(0.0, 1.0 - D * D));
        double theta4 = -fast_atan2(sqrt_1_D2, D);
        double theta3 = fast_atan2(z, G) - fast_atan2(-l4 * sqrt_1_D2, l3 + l4 * D);

        int idx = i * 3;
        angles[idx] = theta1;
        angles[idx + 1] = theta3;
        angles[idx + 2] = theta4;
    }

    return angles;
}

}  // namespace detail

template <typename Derived>
[[nodiscard]] std::array<double, 12> compute_all_joint_angles(const Eigen::MatrixBase<Derived>& positions, double l1,
                                                              double l2, double l3, double l4) noexcept {
    if (positions.rows() != 4 || positions.cols() != 3) {
        throw std::invalid_argument("positions must be 4x3 (4 legs x 3 coordinates)");
    }
    double l2_sq = l2 * l2;
    double _2l3l4 = 2.0 * l3 * l4;
    double inv_2l3l4 = 1.0 / _2l3l4;
    double l3sq_l4sq = l3 * l3 + l4 * l4;
    return detail::compute_all_joint_angles(positions, l1, l2, l3, l4, l2_sq, inv_2l3l4, l3sq_l4sq);
}

class InverseKinematics {
  public:
    InverseKinematics(double body_length, double body_width, double l1, double l2, double l3, double l4);

    [[nodiscard]] Eigen::Matrix<double, 4, 3> get_local_positions(const LegsMatrix& leg_positions, double dx, double dy,
                                                                  double dz, double roll, double pitch,
                                                                  double yaw) const noexcept;

    [[nodiscard]] std::array<double, 12> inverse_kinematics(const LegsMatrix& leg_positions, double dx, double dy,
                                                            double dz, double roll, double pitch,
                                                            double yaw) const noexcept;

  private:
    ForwardKinematics fk_;
    double body_length_, body_width_, l1_, l2_, l3_, l4_;
    Eigen::Matrix4d inv_T_bl_base_[4]{};
    double l2_sq_ = 0.0, inv_2l3l4_ = 0.0, l3sq_l4sq_ = 0.0;
};

}  // namespace quadropted
