/// @file stand_controller.hpp
/// @brief Контроллер стояния — поза с возможностью наклона корпуса.
///
/// StandController удерживает лапы в позе покоя, но позволяет смещать
/// корпус (двигать/наклонять) через cmd_vel. Это «интерактивный» режим:
/// оператор может наклонять робота, не меняя походку.
///
/// ## Отличие от RestController
/// - Нет ПИД-стабилизации (корпус подчиняется команде)
/// - Положение корпуса меняется через body_local_position/orientation
/// - Скорость наклона масштабируется через body_velocity_scale_
///
/// ## Применение
/// - Режим STAND (mode_sub)
/// - Калибровка положения лап
/// - Отладка кинематики
///
/// @warning max_linear_velocity_ и max_angular_velocity_ ограничивают
///   скорость движения корпуса для безопасности.
///
/// @see RestController, State::body_local_position

#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

/// Контроллер стояния с управлением положением корпуса.
class StandController {
  public:
    /// @param default_stance       Положения лап в покое (3×4)
    /// @param body_velocity_scale  Масштаб скорости корпуса от cmd_vel (0.01)
    /// @param body_angular_scale   Масштаб угловой скорости (0.005)
    /// @param max_linear_velocity  Максимальная линейная скорость [м/с] (0.2)
    /// @param max_angular_velocity Максимальная угловая скорость [рад/с] (0.5)
    explicit StandController(Eigen::MatrixXd default_stance, double body_velocity_scale = 0.01,
                             double body_angular_scale = 0.005, double max_linear_velocity = 0.2,
                             double max_angular_velocity = 0.5);

    /// Выполнить шаг контроллера стояния.
    ///
    /// @param state  Состояние робота (модифицируется: body_local_position)
    /// @param cmd    Команда (velocity, yaw_rate)
    ///
    /// @return Положения лап (3×4) с учётом смещения корпуса.
    ///
    /// @note state.body_local_position изменяется каждый вызов на величину
    ///   cmd.velocity * масштаб. Это обеспечивает плавное движение.
    LegsMatrix run(State& state, Command& cmd) const;

    const LegsMatrix& default_stance() const { return default_stance_; }

  private:
    LegsMatrix default_stance_;
    double body_velocity_scale_ = 0.01;
    double body_angular_scale_ = 0.005;
    double max_linear_velocity_ = 0.2;   ///< Максимальная скорость корпуса [м/с]
    double max_angular_velocity_ = 0.5;  ///< Максимальная угловая скорость [рад/с]
};

}  // namespace quadropted
