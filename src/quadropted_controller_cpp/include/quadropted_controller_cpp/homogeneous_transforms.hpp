#pragma once
#include <Eigen/Dense>
#include "quadropted_controller_cpp/rotation_matrices.hpp"

namespace quadropted {

/// Однородная матрица трансляции 4x4
inline Eigen::Matrix4d homog_transxyz(double dx, double dy, double dz) {
    Eigen::Matrix4d m = Eigen::Matrix4d::Identity();
    m(0, 3) = dx; m(1, 3) = dy; m(2, 3) = dz;
    return m;
}

/// Однородная матрица преобразования 4x4 (translation + rotation)
inline Eigen::Matrix4d homog_transform(double dx, double dy, double dz,
                                        double alpha, double beta, double gamma) {
    Eigen::Matrix4d m = Eigen::Matrix4d::Identity();
    m.block<3, 3>(0, 0) = rotxyz(alpha, beta, gamma);
    m(0, 3) = dx; m(1, 3) = dy; m(2, 3) = dz;
    return m;
}

/// Инверсия однородной матрицы — без копирования, поэлементное построение
inline Eigen::Matrix4d homog_transform_inverse(const Eigen::Matrix4d& matrix) {
    Eigen::Matrix4d inv = Eigen::Matrix4d::Identity();
    // R^T
    inv.block<3, 3>(0, 0) = matrix.block<3, 3>(0, 0).transpose();
    // -R^T * d
    inv.block<3, 1>(0, 3) = -inv.block<3, 3>(0, 0) * matrix.block<3, 1>(0, 3);
    return inv;
}

} // namespace quadropted
