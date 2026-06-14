/// @file crawl_swing.hpp
/// @brief Расчёт положений лап в фазе переноса для походки crawl.
///
/// Аналогично TrotSwingController, но с боковым смещением (body_shift_y)
/// для переноса веса при шаге.
///
/// ## Отличия от TrotSwingController
/// - Точка Райберта зависит от shifted_left — направления переноса веса
/// - Высота подъёма та же, синусоидальная
/// - В align=left нога смещается вбок при переносе
///
/// @warning Особое внимание при выборе body_shift_y и z_leg_lift:
///   слишком малый shift → недостаточный перенос веса → потеря устойчивости.
///
/// @see CrawlGaitController, CrawlStanceController

#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

/// Вычисляет следующее положение лапы в фазе переноса шагающей походки.
class CrawlSwingController {
  public:
    /// @param swing_ticks     Длина фазы переноса [тики]
    /// @param time_step       Шаг симуляции [с]
    /// @param z_leg_lift      Высота подъёма лапы [м]
    /// @param default_stance  Положения лап в покое (3×4)
    /// @param phase_length    Общая длина цикла [тики]
    /// @param stance_ticks    Длина фазы опоры [тики]
    /// @param body_shift_y    Смещение корпуса вбок [м]
    CrawlSwingController(int swing_ticks, double time_step, double z_leg_lift, Eigen::MatrixXd default_stance,
                         int phase_length, int stance_ticks, double body_shift_y);

    /// Точка приземления по Райберту.
    ///
    /// @param leg_index    Индекс лапы (0..3)
    /// @param cmd_vel      Целевая скорость [vx, vy, vz]
    /// @param shifted_left Направление смещения корпуса (true = влево)
    ///
    /// @return Положение лапы в момент касания.
    Eigen::Vector3d raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel, bool shifted_left) const;

    /// Высота лапы над опорой.
    ///
    /// @param swing_prop  Прогресс фазы переноса [0..1]
    /// @return Высота [м]: 0 → z_leg_lift → 0.
    double swing_height(double swing_prop) const;

    /// Следующее положение лапы.
    ///
    /// @param swing_prop   Прогресс фазы переноса [0..1]
    /// @param leg_index    Индекс лапы (0..3)
    /// @param current      Текущие положения лап (3×4)
    /// @param cmd_vel      Целевая скорость [vx, vy, vz]
    /// @param robot_height Целевая высота корпуса [м]
    /// @param shifted_left Направление смещения (true = влево)
    ///
    /// @return Новое положение лапы (3×1).
    Eigen::Vector3d next_foot_location(double swing_prop, int leg_index, const LegsMatrix& current,
                                       const Eigen::Vector3d& cmd_vel, double robot_height, bool shifted_left) const;

  private:
    int swing_ticks_;
    double time_step_, z_leg_lift_;
    LegsMatrix default_stance_;
    int phase_length_;
    int stance_ticks_;
    double body_shift_y_;
    double total_time_;
    double stance_yaw_time_;
    double swing_total_time_;
};

}  // namespace quadropted
