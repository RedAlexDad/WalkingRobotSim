/// @file inverse_kinematics.hpp
/// @brief Обратная кинематика: положения лап → углы суставов.
///
/// Решает IK для 3-степенной ноги (hip, thigh, calf) аналитически.
/// Вход: положения лап в системе корпуса (3×4).
/// Выход: 12 углов сочленений [рад].
///
/// ## Математика
/// Решение основано на геометрии:
/// ```
/// hip  = atan2(y, x) — поворот в плоскости XZ
/// thigh, calf — решение треугольника (l3, l4, H) через закон косинусов
/// ```
/// Где H = расстояние от hip joint до стопы.
///
/// ## Вырожденные случаи
/// - Если H > l3 + l4 (нога полностью выпрямлена) → clamp D = 1.0
/// - Если H < |l3 - l4| → clamp D = -1.0
/// - Квадратный корень отрицательного числа в sqrt_1_D2 = 0 (защита max())
///
/// @warning IK использует fast_atan2() для производительности. Максимальная
///   погрешность ~0.003 рад, что пренебрежимо для управления.
///
/// @see ForwardKinematics, fast_atan2

#pragma once
#include <Eigen/Dense>
#include <array>
#include <cmath>
#include <stdexcept>

#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/utils/fast_math.hpp"

namespace quadropted {

/// Преобразует мировые положения лап в локальные (относительно корпуса).
///
/// @param leg_positions Положения лап в мировой системе (3×4)
/// @param body_length   Длина корпуса [м]
/// @param body_width    Ширина корпуса [м]
/// @param dx,dy,dz      Смещение корпуса [м]
/// @param roll,pitch,yaw Углы корпуса [рад]
///
/// @return Матрица 4×3 локальных положений (4 лапы × [x, y, z]).
[[nodiscard]] Eigen::Matrix<double, 4, 3> compute_local_positions(const LegsMatrix& leg_positions, double body_length,
                                                                   double body_width, double dx, double dy, double dz,
                                                                   double roll, double pitch, double yaw) noexcept;

/// Решает IK для ОДНОЙ лапы: (x, y, z) → [hip, thigh, calf].
///
/// @param x,y,z      Положение лапы в системе корпуса [м]
/// @param leg_index  Индекс лапы (0..3) — влияет на знак hip угла
/// @param l1,l2,l3,l4 Геометрические параметры ноги [м]
///
/// @return Массив [theta_hip, theta_thigh, theta_calf] [рад].
///
/// @note Использует fast_atan2() — см. fast_math.hpp.
[[nodiscard]] std::array<double, 3> compute_joint_angles_for_leg(double x, double y, double z, int leg_index, double l1,
                                                                  double l2, double l3, double l4) noexcept;

namespace detail {

/// @brief Внутренний шаблонный IK для всех 4 лап.
///
/// @tparam Derived  Тип Eigen-матрицы (4×3)
/// @param positions Локальные положения лап (4×3)
/// @param l1       Длина плеча (hip offset) [м]
/// @param l2       Абдукция бедра [м]
/// @param l3       Длина бедра [м]
/// @param l4       Длина голени [м]
/// @param l2_sq     l2² (кешированное)
/// @param inv_2l3l4 1/(2*l3*l4) (кешированное)
/// @param l3sq_l4sq l3²+l4² (кешированное)
///
/// @return Массив 12 углов [рад]
///
/// @throw std::invalid_argument если positions.rows() != 4 || cols() != 3
///
/// @warning Параметры l2_sq, inv_2l3l4, l3sq_l4sq ДОЛЖНЫ быть предвычислены
///   для производительности. Не вызывайте эту функцию с сырыми l1..l4.
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

/// Удобная обёртка: вычисляет l2_sq, inv_2l3l4, l3sq_l4sq и вызывает detail.
///
/// @param positions  Локальные положения лап (4×3)
/// @param l1  Длина плеча (hip offset) [м]
/// @param l2  Абдукция бедра [м]
/// @param l3  Длина бедра [м]
/// @param l4  Длина голени [м]
/// @return Массив 12 углов [рад]
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

/// Высокоуровневый IK-решатель: положения лап → 12 углов.
///
/// Кеширует предвычисленные матрицы T_base_inv для каждой лапы,
/// что ускоряет повторные вызовы в цикле управления.
class InverseKinematics {
  public:
    /// @param body_length  Длина корпуса [м]
    /// @param body_width   Ширина корпуса [м]
    /// @param l1           Длина плеча (hip offset) [м]
    /// @param l2           Абдукция бедра [м]
    /// @param l3           Длина бедра [м]
    /// @param l4           Длина голени [м]
    InverseKinematics(double body_length, double body_width, double l1, double l2, double l3, double l4);

    /// Преобразует положения лап из мировой системы в локальную.
    ///
    /// @param leg_positions  Положения лап в мировой системе (3×4)
    /// @param dx,dy,dz       Смещение корпуса [м]
    /// @param roll,pitch,yaw Углы корпуса [рад]
    ///
    /// @return Матрица 4×3 локальных положений.
    [[nodiscard]] Eigen::Matrix<double, 4, 3> get_local_positions(const LegsMatrix& leg_positions, double dx, double dy,
                                                                   double dz, double roll, double pitch,
                                                                   double yaw) const noexcept;

    /// Полный IK: положения лап → 12 углов [hip×4, thigh×4, calf×4].
    ///
    /// @param leg_positions  Положения лап в мировой системе (3×4)
    /// @param dx,dy,dz       Смещение корпуса [м]
    /// @param roll,pitch,yaw Углы корпуса [рад]
    ///
    /// @return Массив 12 углов [рад].
    [[nodiscard]] std::array<double, 12> inverse_kinematics(const LegsMatrix& leg_positions, double dx, double dy,
                                                             double dz, double roll, double pitch,
                                                             double yaw) const noexcept;

  private:
    ForwardKinematics fk_;                    ///< FK для валидации (не используется напрямую)
    double body_length_, body_width_, l1_, l2_, l3_, l4_;
    Eigen::Matrix4d inv_T_bl_base_[4]{};      ///< Кешированные обратные матрицы базы
    double l2_sq_ = 0.0, inv_2l3l4_ = 0.0, l3sq_l4sq_ = 0.0;  ///< Предвычисленные константы
};

}  // namespace quadropted
