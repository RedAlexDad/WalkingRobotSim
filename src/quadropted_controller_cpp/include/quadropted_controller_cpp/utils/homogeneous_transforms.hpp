#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/utils/rotation_matrices.hpp"

namespace quadropted {

[[nodiscard]] Eigen::Matrix4d homog_transxyz(double dx, double dy, double dz) noexcept;
[[nodiscard]] Eigen::Matrix4d homog_transform(double dx, double dy, double dz, double alpha, double beta,
                                              double gamma) noexcept;
[[nodiscard]] Eigen::Matrix4d homog_transform_inverse(const Eigen::Matrix4d& matrix) noexcept;

}  // namespace quadropted
