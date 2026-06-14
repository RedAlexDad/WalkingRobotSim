/// @file trot_stance.hpp
/// @brief Расчёт положений лап в фазе опоры (stance) для рыси.
///
/// Когда лапа стоит на земле (фаза stance), её положение в мировой системе
/// фиксировано. Корпус движется относительно лапы. Этот контроллер
/// рассчитывает, где должна оказаться лапа в системе корпуса на текущем тике,
/// исходя из скорости движения.
///
/// ## Логика
/// Из текущего положения лапы в системе корпуса вычитается перемещение
/// корпуса за текущий тик (cmd_vel * dt). Это даёт новое относительное
/// положение лапы.
///
/// @note Коррекция по высоте (z_error_constant) предотвращает «проваливание»
///   лапы сквозь опору при неровностях.
///
/// @warning Положение лапы в stance НЕ ДОЛЖНО меняться в мировой системе.
///   Если лапа «проскальзывает» — проблема в расчёте position_delta().
///
/// @see TrotGaitController, TrotSwingController

#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

/// Вычисляет следующее положение лапы в фазе опоры рыси.
class TrotStanceController {
  public:
    /// @param phase_length     Общая длина цикла [тики]
    /// @param stance_ticks     Длина фазы опоры [тики]
    /// @param swing_ticks      Длина фазы переноса [тики]
    /// @param time_step        Шаг симуляции [с]
    /// @param z_error_constant Коэффициент коррекции высоты (регулировка z)
    TrotStanceController(int phase_length, int stance_ticks, int swing_ticks, double time_step,
                         double z_error_constant);

    /// Дельта изменения положения лапы за один тик.
    ///
    /// @param leg_index    Индекс лапы (0..3)
    /// @param state_foot   Текущие положения лап (3×4)
    /// @param cmd_vel      Целевая скорость [vx, vy, vz]
    /// @param robot_height Целевая высота корпуса [м]
    ///
    /// @return Вектор [dx, dy, dz] смещения лапы в системе корпуса.
    Eigen::Vector3d position_delta(int leg_index, const LegsMatrix& state_foot, const Eigen::Vector3d& cmd_vel,
                                   double robot_height) const;

    /// Следующее положение лапы в системе корпуса.
    ///
    /// @param leg_index    Индекс лапы (0..3)
    /// @param state_foot   Текущие положения лап (3×4)
    /// @param cmd_vel      Целевая скорость [vx, vy, vz]
    /// @param robot_height Целевая высота корпуса [м]
    ///
    /// @return Новое положение лапы (3×1) в системе корпуса.
    Eigen::Vector3d next_foot_location(int leg_index, const LegsMatrix& state_foot, const Eigen::Vector3d& cmd_vel,
                                       double robot_height) const;

  private:
    int phase_length_, stance_ticks_, swing_ticks_;
    double time_step_, z_error_constant_, inv_scale_;
    double inv_z_error_;
};

}  // namespace quadropted
