/// @file forward_kinematics.hpp
/// @brief Прямая кинематика: углы суставов → положения лап.
///
/// Преобразует 12 углов сочленений (hip × 4, thigh × 4, calf × 4) в положения
/// лап в системе корпуса. Используется в одометрии для отслеживания лап.
///
/// ## Кинематическая цепочка
/// Для каждой лапы:
/// ```
/// base → hip (l1) → thigh (l2, l3) → calf (l4) → foot
/// ```
/// Каждый сегмент описывается однородной матрицей 4×4. Итоговое положение
/// лапы = произведение матриц: T_base * T_hip * T_thigh * T_calf * T_foot.
///
/// ## Параметры ноги
/// - l1: длина плеча (hip offset)
/// - l2: абдукция бедра (hip abduction offset)
/// - l3: длина бедра (thigh)
/// - l4: длина голени (calf)
///
/// @warning Геометрия (body_length, body_width, l1..l4) должна совпадать
///   с обратной кинематикой, иначе FK и IK будут давать разные результаты.
///
/// @see InverseKinematics, OdometryState

#pragma once
#include <Eigen/Dense>
#include <array>

namespace quadropted {

using JointAngles = std::array<double, 12>;    ///< 12 углов: [hip×4, thigh×4, calf×4]
using FootPositions = std::array<Eigen::Vector3d, 4>;  ///< 4 положения лап (Vector3d)

/// Вычисляет смещение базы лапы относительно центра корпуса.
///
/// @param leg_index   Индекс лапы (0..3)
/// @param body_length Длина корпуса [м]
/// @param body_width  Ширина корпуса [м]
///
/// @return Вектор [x, y] смещения базы лапы.
///
/// @note Нумерация: 0=FR, 1=FL, 2=RR, 3=RL.
struct LegBasePositions {
    static Eigen::Vector2d get(int leg_index, double body_length, double body_width);
};

/// Прямая кинематика одной лапы (через цепочку матриц).
///
/// @param theta_hip   Угол в тазобедренном суставе [рад]
/// @param theta_thigh Угол в коленном суставе [рад]
/// @param theta_calf  Угол в голеностопе [рад]
/// @param T_base      Матрица базы лапы (смещение от центра корпуса)
/// @param T_thigh_t   Матрица трансформации бедра
/// @param T_calf_t    Матрица трансформации голени
/// @param T_foot      Матрица конечной точки (лапы)
///
/// @return Положение лапы (Vector3d) в системе корпуса.
///
/// @exception Нет — noexcept.
[[nodiscard]] Eigen::Vector3d compute_leg_fk_chain(double theta_hip, double theta_thigh, double theta_calf,
                                                   const Eigen::Matrix4d& T_base, const Eigen::Matrix4d& T_thigh_t,
                                                   const Eigen::Matrix4d& T_calf_t,
                                                   const Eigen::Matrix4d& T_foot) noexcept;

/// Прямая кинематика всех 4 лап.
///
/// Кеширует матрицы T_base для каждой лапы (вычисляются в конструкторе).
/// Это ускоряет FK для всех лап в цикле.
class ForwardKinematics {
  public:
    /// @param body_length  Длина корпуса [м] (между передними и задними лапами)
    /// @param body_width   Ширина корпуса [м] (между левыми и правыми лапами)
    /// @param l1           Длина плеча (hip offset) [м]
    /// @param l2           Абдукция бедра (hip abduction) [м]
    /// @param l3           Длина бедра [м]
    /// @param l4           Длина голени [м]
    ForwardKinematics(double body_length, double body_width, double l1, double l2, double l3, double l4);

    /// FK для всех лап из вектора углов.
    ///
    /// @param joint_angles  Вектор из 12 углов [рад] (hip0, hip1, ..., thigh0, ..., calf3)
    /// @return Массив 4×Vector3d положений лап.
    [[nodiscard]] FootPositions forward_kinematics_all_legs(const std::vector<double>& joint_angles) const;

    /// FK для всех лап из std::array углов.
    [[nodiscard]] FootPositions forward_kinematics_all_legs(const JointAngles& joint_angles) const;

  private:
    double l1_, l2_, l3_, l4_;
    Eigen::Matrix4d T_thigh_t_, T_calf_t_, T_foot_;
    Eigen::Matrix4d T_base_[4]{};  ///< Матрицы базы для каждой лапы (кешированные)
};

}  // namespace quadropted
