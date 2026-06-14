/// @file rest_controller.hpp
/// @brief Контроллер покоя — удержание позы с ПИД-стабилизацией.
///
/// RestController удерживает робота в позе покоя (все лапы на земле).
/// При включённом IMU компенсирует крен/тангаж через ПИД-регулятор.
///
/// ## Когда используется
/// - Режим REST (стартовый режим по умолчанию)
/// - Между сменами походок как промежуточное состояние
/// - Когда робот стоит на месте и нужна стабилизация
///
/// ## Стабилизация
/// ПИД-регулятор работает по отклонению roll/pitch от нуля.
/// Выход ПИД = сдвиг лап по Z для выравнивания корпуса.
///
/// @note В отличие от TrotGaitController, здесь нет цикла — метод step()
///   вычисляет положения лап за один вызов на основе текущего состояния.
///
/// @warning use_imu_ по умолчанию false. Включать только если IMU
///   откалиброван и выдаёт корректные данные.
///
/// @see PIDController, StandController

#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

/// Контроллер покоя: удержание позы + опциональная ПИД-стабилизация.
class RestController {
  public:
    /// @param default_stance  Положения лап в покое (3×4)
    /// @param pid_kp          Пропорциональный коэффициент ПИД (0.75)
    /// @param pid_ki          Интегральный коэффициент ПИД (2.29)
    /// @param pid_kd          Дифференциальный коэффициент ПИД (0.0)
    explicit RestController(Eigen::MatrixXd default_stance, double pid_kp = 0.75, double pid_ki = 2.29,
                            double pid_kd = 0.0);

    /// Выполнить шаг контроллера покоя.
    ///
    /// @param state  Текущее состояние робота (IMU, ticks)
    /// @param cmd    Текущая команда (высота корпуса)
    ///
    /// @return Положения лап (3×4) с учётом ПИД-коррекции.
    ///
    /// @note Если use_imu_ = false, возвращает default_stance_ без изменений.
    LegsMatrix step(const State& state, const Command& cmd);

    const LegsMatrix& default_stance() const { return default_stance_; }
    PIDController& pid() { return pid_; }
    bool use_imu() const { return use_imu_; }
    void set_use_imu(bool v) { use_imu_ = v; }

    /// Сброс ПИД-регулятора и таймера.
    void reset();

  private:
    LegsMatrix default_stance_;    ///< Базовая поза покоя
    PIDController pid_;            ///< ПИД-стабилизация корпуса
    bool use_imu_;                 ///< Флаг использования IMU
    double pid_last_time_ = 0.0;   ///< Время последнего вызова ПИД
};

}  // namespace quadropted
