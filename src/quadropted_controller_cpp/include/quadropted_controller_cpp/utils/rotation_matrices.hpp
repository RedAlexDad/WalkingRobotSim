/// @file rotation_matrices.hpp
/// @brief Построители матриц вращения 3×3 (axis-angle, noexcept).
///
/// ## Порядок вращения
/// Для extrinsic RPY (X→Y→Z): R = Rz(gamma) * Ry(beta) * Rx(alpha).
///
/// ```
/// rotx(α): |1   0      0   |    roty(β): | cosβ  0  sinβ|
///          |0  cosα  -sinα |             | 0     1   0  |
///          |0  sinα   cosα |             |-sinβ  0  cosβ|
///
/// rotz(γ): |cosγ -sinγ  0|
///          |sinγ  cosγ  0|
///          |0     0     1|
/// ```
///
/// @warning Углы в радианах. Все функции noexcept.
/// @see homogeneous_transforms.hpp, ForwardKinematics

#pragma once
#include <Eigen/Dense>

namespace quadropted {

/// Матрица вращения вокруг оси X (roll).
///
/// @param alpha  Угол поворота [рад].
/// @return Матрица 3×3.
[[nodiscard]] Eigen::Matrix3d rotx(double alpha) noexcept;

/// Матрица вращения вокруг оси Y (pitch).
///
/// @param beta  Угол поворота [рад].
/// @return Матрица 3×3.
[[nodiscard]] Eigen::Matrix3d roty(double beta) noexcept;

/// Матрица вращения вокруг оси Z (yaw).
///
/// @param gamma  Угол поворота [рад].
/// @return Матрица 3×3.
[[nodiscard]] Eigen::Matrix3d rotz(double gamma) noexcept;

/// Композитное вращение RPY (extrinsic X→Y→Z).
///
/// @param alpha  Roll [рад] (вокруг X)
/// @param beta   Pitch [рад] (вокруг Y)
/// @param gamma  Yaw [рад] (вокруг Z)
///
/// @return R = Rz(gamma) * Ry(beta) * Rx(alpha).
///
/// @note Порядок extrinsic X→Y→Z даёт Rz*Ry*Rx как произведение матриц.
/// @see homogeneous_transforms.hpp
[[nodiscard]] Eigen::Matrix3d rotxyz(double alpha, double beta, double gamma) noexcept;

}  // namespace quadropted
