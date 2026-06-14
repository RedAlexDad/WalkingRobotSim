/// @file homogeneous_transforms.hpp
/// @brief Построители однородных матриц 4×4 (noexcept).
///
/// Содержит noexcept-обёртки для создания матриц трансформации:
/// - Чистый перенос (translation only)
/// - Перенос + вращение (RPY)
/// - Обратная матрица
///
/// ## Формат
/// Матрица 4×4 в формате Eigen::Matrix4d:
/// ```
/// | R  t |
/// | 0  1 |
/// ```
/// где R = 3×3 матрица вращения, t = 3×1 вектор переноса.
///
/// @warning homog_transform_inverse() вычисляет аналитическую обратную,
///   что дешевле полного обращения. Не вызывайте её для необратимых матриц.
///
/// @see rotation_matrices.hpp, ForwardKinematics

#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/utils/rotation_matrices.hpp"

namespace quadropted {

/// Матрица чистого переноса (без вращения).
///
/// @param dx  Смещение по X [м]
/// @param dy  Смещение по Y [м]
/// @param dz  Смещение по Z [м]
///
/// @return Матрица 4×4: диагональ 1,3,3,1, перенос в (1..3, 3).
[[nodiscard]] Eigen::Matrix4d homog_transxyz(double dx, double dy, double dz) noexcept;

/// Матрица переноса + вращения (X→Y→Z extrinsic).
///
/// @param dx,dy,dz  Перенос [м]
/// @param alpha     Вращение вокруг X [рад] (roll)
/// @param beta      Вращение вокруг Y [рад] (pitch)
/// @param gamma     Вращение вокруг Z [рад] (yaw)
///
/// @return Матрица: T = Trans(dx,dy,dz) * RotX(alpha) * RotY(beta) * RotZ(gamma)
///
/// @note Вращение extrinsic (вокруг глобальных осей X→Y→Z).
/// @see rotxyz()
[[nodiscard]] Eigen::Matrix4d homog_transform(double dx, double dy, double dz, double alpha, double beta,
                                               double gamma) noexcept;

/// Аналитическая обратная однородной матрицы.
///
/// Для T = [R t; 0 1], обратная T⁻¹ = [Rᵀ  -Rᵀ*t; 0 1].
///
/// @param matrix  Однородная матрица 4×4
///
/// @return Обратная матрица.
///
/// @exception Гарантия noexcept. Если matrix = 0, результат неопределён.
/// @note В 2-3 раза быстрее прямого Eigen::inverse().
[[nodiscard]] Eigen::Matrix4d homog_transform_inverse(const Eigen::Matrix4d& matrix) noexcept;

}  // namespace quadropted
