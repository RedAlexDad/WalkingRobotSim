#pragma once
#include <Eigen/Dense>

namespace quadropted {

[[nodiscard]] Eigen::Matrix3d rotx(double alpha) noexcept;
[[nodiscard]] Eigen::Matrix3d roty(double beta) noexcept;
[[nodiscard]] Eigen::Matrix3d rotz(double gamma) noexcept;
[[nodiscard]] Eigen::Matrix3d rotxyz(double alpha, double beta, double gamma) noexcept;

}  // namespace quadropted
