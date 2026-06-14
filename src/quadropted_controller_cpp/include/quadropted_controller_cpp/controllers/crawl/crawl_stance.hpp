/// @file crawl_stance.hpp
/// @brief Расчёт положений лап в фазе опоры для походки crawl.
///
/// Аналогично TrotStanceController, но с дополнительным боковым смещением
/// корпуса (body_shift_y) для переноса веса на опорные лапы.
///
/// ## Логика
/// - Три лапы стоят на земле, одна переносится.
/// - Корпус смещается вбок (Y), чтобы перенести вес с переставляемой лапы.
/// - Смещение зависит от first_cycle, move_sideways, move_left.
///
/// @note Коррекция по Z через z_error_constant работает так же, как в рыси.
///
/// @warning Если body_shift_y слишком большой, робот может опрокинуться
///   на бок при перестановке.
///
/// @see CrawlGaitController, CrawlSwingController

#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

/// Вычисляет следующее положение лапы в фазе опоры шагающей походки.
class CrawlStanceController {
  public:
    /// @param phase_length     Общая длина цикла [тики]
    /// @param stance_ticks     Длина фазы опоры [тики]
    /// @param swing_ticks      Длина фазы переноса [тики]
    /// @param time_step        Шаг симуляции [с]
    /// @param z_error_constant Коэффициент коррекции высоты
    /// @param body_shift_y     Смещение корпуса вбок [м]
    CrawlStanceController(int phase_length, int stance_ticks, int swing_ticks, double time_step,
                          double z_error_constant, double body_shift_y);

    /// Следующее положение лапы в системе корпуса (фаза опоры).
    ///
    /// @param leg_index    Индекс лапы (0..3)
    /// @param state_foot   Текущие положения лап (3×4)
    /// @param cmd_vel      Целевая скорость [vx, vy, vz]
    /// @param robot_height Целевая высота корпуса [м]
    /// @param first_cycle  Флаг первого цикла
    /// @param move_sideways Нужно ли смещать корпус вбок
    /// @param move_left    Направление смещения (true = влево)
    ///
    /// @return Новое положение лапы (3×1)
    Eigen::Vector3d next_foot_location(int leg_index, const LegsMatrix& state_foot, const Eigen::Vector3d& cmd_vel,
                                       double robot_height, bool first_cycle, bool move_sideways, bool move_left) const;

  private:
    int phase_length_, stance_ticks_, swing_ticks_;
    double time_step_, z_error_constant_, body_shift_y_;
    double phase_over_swing_;         ///< phase_length / swing_ticks
    double inv_stance_total_time_;    ///< 1 / (stance_ticks * time_step)
    double inv_z_error_;              ///< 1 / z_error_constant
};

}  // namespace quadropted
