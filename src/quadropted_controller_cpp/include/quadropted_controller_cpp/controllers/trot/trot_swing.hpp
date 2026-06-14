/// @file trot_swing.hpp
/// @brief Расчёт положений лап в фазе переноса (swing) для рыси.
///
/// Когда лапа переносится (фаза swing), она движется от точки отрыва
/// до точки приземления, рассчитанной по эвристике Райберта.
///
/// ## Траектория Райберта
/// Точка приземления (touchdown) вычисляется исходя из текущей скорости:
///   touchdown = default_stance + cmd_vel * T/2
/// где T — время полного цикла. Это обеспечивает устойчивость походки.
///
/// ## Высота переноса
/// Траектория по Z — синусоидальная: от 0 в момент отрыва до z_leg_lift
/// в середине фазы и обратно до 0 перед касанием.
///
/// @note z_leg_lift определяет клиренс лапы. Слишком малое значение →
///   лапа задевает препятствия. Слишком большое → избыточное движение.
///
/// @warning Raibert touchdown даёт корректную точку только на ровной поверхности.
///   Для пересечённой местности требуется адаптация.
///
/// @see TrotGaitController, TrotStanceController

#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

/// Вычисляет следующее положение лапы в фазе переноса рыси.
class TrotSwingController {
  public:
    /// @param swing_ticks     Длина фазы переноса [тики]
    /// @param time_step       Шаг симуляции [с]
    /// @param z_leg_lift      Высота подъёма лапы [м]
    /// @param default_stance  Положения лап в покое (3×4)
    /// @param phase_length    Общая длина цикла [тики]
    /// @param stance_ticks    Длина фазы опоры [тики]
    TrotSwingController(int swing_ticks, double time_step, double z_leg_lift, Eigen::MatrixXd default_stance,
                        int phase_length, int stance_ticks);

    /// Точка приземления по эвристике Райберта.
    ///
    /// @param leg_index  Индекс лапы (0..3)
    /// @param cmd_vel    Целевая скорость [vx, vy, vz]
    ///
    /// @return Положение лапы в системе корпуса в момент касания.
    ///
    /// @note Формула: touchdown = default + velocity * half_cycle_time.
    /// @see swing_height()
    Eigen::Vector3d raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel) const;

    /// Высота лапы над опорой в зависимости от прогресса фазы.
    ///
    /// @param swing_prop  Прогресс фазы переноса [0..1].
    ///                    0 = отрыв, 1 = касание.
    ///
    /// @return Высота подъёма [м]. 0 в начале и конце, z_leg_lift в середине.
    double swing_height(double swing_prop) const;

    /// Следующее положение лапы в системе корпуса.
    ///
    /// @param swing_prop   Прогресс фазы переноса [0..1]
    /// @param leg_index    Индекс лапы (0..3)
    /// @param current      Текущие положения лап (3×4)
    /// @param cmd_vel      Целевая скорость [vx, vy, vz]
    /// @param robot_height Целевая высота корпуса [м]
    ///
    /// @return Новое положение лапы (3×1).
    Eigen::Vector3d next_foot_location(double swing_prop, int leg_index, const LegsMatrix& current,
                                       const Eigen::Vector3d& cmd_vel, double robot_height) const;

    int swing_ticks() const { return swing_ticks_; }

  private:
    int swing_ticks_;
    double time_step_, z_leg_lift_;
    LegsMatrix default_stance_;
    int phase_length_;   // для Raibert delta_pos (T/2)
    int stance_ticks_;   // для Raibert yaw rotation
    double total_time_;
    double stance_yaw_time_;
    double swing_total_time_;
    double two_z_lift_;  // 2 * z_leg_lift (кешированное)
};

}  // namespace quadropted
