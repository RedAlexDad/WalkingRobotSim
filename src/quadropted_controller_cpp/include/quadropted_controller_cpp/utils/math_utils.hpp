/// @file math_utils.hpp
/// @brief Вспомогательные функции для вращений и однородных преобразований.
///
/// Содержит те же функции, что rotation_matrices.hpp и homogeneous_transforms.hpp,
/// но без noexcept-гарантий. Создан для обратной совместимости.
///
/// @warning Для нового кода предпочтительнее использовать noexcept-версии.
/// @see rotation_matrices.hpp, homogeneous_transforms.hpp

#pragma once
#include <Eigen/Dense>

namespace quadropted {

/// @overload quadropted::rotx(double)
Eigen::Matrix3d rotx(double alpha);

/// @overload quadropted::roty(double)
Eigen::Matrix3d roty(double beta);

/// @overload quadropted::rotz(double)
Eigen::Matrix3d rotz(double gamma);

/// @overload quadropted::rotxyz(double,double,double)
Eigen::Matrix3d rotxyz(double alpha, double beta, double gamma);

/// @overload quadropted::homog_transxyz(double,double,double)
Eigen::Matrix4d homog_transxyz(double dx, double dy, double dz);

/// @overload quadropted::homog_transform(double,double,double,double,double,double)
Eigen::Matrix4d homog_transform(double dx, double dy, double dz, double alpha, double beta, double gamma);

/// @overload quadropted::homog_transform_inverse(const Eigen::Matrix4d&)
Eigen::Matrix4d homog_transform_inverse(const Eigen::Matrix4d& matrix);

}  // namespace quadropted
