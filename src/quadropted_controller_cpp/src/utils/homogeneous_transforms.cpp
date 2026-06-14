#include "quadropted_controller_cpp/utils/homogeneous_transforms.hpp"

namespace quadropted {

Eigen::Matrix4d homog_transxyz(double dx, double dy, double dz) noexcept {
    Eigen::Matrix4d m = Eigen::Matrix4d::Identity();
    m(0, 3) = dx;
    m(1, 3) = dy;
    m(2, 3) = dz;
    return m;
}

Eigen::Matrix4d homog_transform(double dx, double dy, double dz, double alpha, double beta, double gamma) noexcept {
    Eigen::Matrix4d m;
    m.block<3, 3>(0, 0) = rotxyz(alpha, beta, gamma);
    m(0, 3) = dx;
    m(1, 3) = dy;
    m(2, 3) = dz;
    m(3, 0) = 0;
    m(3, 1) = 0;
    m(3, 2) = 0;
    m(3, 3) = 1;
    return m;
}

Eigen::Matrix4d homog_transform_inverse(const Eigen::Matrix4d& matrix) noexcept {
    Eigen::Matrix4d inv;
    inv.block<3, 3>(0, 0) = matrix.block<3, 3>(0, 0).transpose();
    inv.block<3, 1>(0, 3) = -inv.block<3, 3>(0, 0) * matrix.block<3, 1>(0, 3);
    inv(3, 0) = 0;
    inv(3, 1) = 0;
    inv(3, 2) = 0;
    inv(3, 3) = 1;
    return inv;
}

}  // namespace quadropted
