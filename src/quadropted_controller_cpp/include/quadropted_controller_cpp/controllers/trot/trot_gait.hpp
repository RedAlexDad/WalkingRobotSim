/// @file trot_gait.hpp
/// @brief Контроллер походки «рысь» (trot) — диагональные пары.
///
/// Рысь — симметричная походка, в которой диагональные пары лап (FR+RL, FL+RR)
/// движутся синхронно. Обеспечивает максимальную скорость среди всех gait.
///
/// ## Фазы
/// 1. **Stance** (0..stance_ticks-1) — две диагональные лапы на земле,
///    корпус движется вперёд. Положение лап рассчитывается через TrotStanceController.
/// 2. **Swing** (stance_ticks..phase_length-1) — те же лапы переносятся
///    по траектории Райберта через TrotSwingController.
///
/// ## Стабилизация
/// Встроенный ПИД-регулятор (PIDController) компенсирует крен/тангаж
/// по показаниям IMU. Активируется флагом use_imu.
///
/// @note В наследство от GaitController получает:
///   - contact_phases = [[1,0],[1,0],[0,1],[0,1]]  (диагонали FR+RL, FL+RR)
///   - stance_time = 0.25 с, swing_time = 0.15 с (настраивается)
///
/// @warning Настройка PID требует осторожности: высокий kp может вызвать
///   автоколебания корпуса. Рекомендуется kd > 0 для демпфирования.
///
/// @see GaitController, TrotStanceController, TrotSwingController, PIDController

#pragma once
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_stance.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_swing.hpp"

namespace quadropted {

/// Контроллер рыси с управлением по Райберту и ПИД-стабилизацией.
///
/// Для каждого тика вызывает step(), который:
///   1. Определяет фазу (stance/swing) по ticks.
///   2. Вычисляет положение каждой лапы через соответствующий подконтроллер.
///   3. Применяет ПИД-коррекцию по IMU (если use_imu_ true).
///
/// @note Метод step() является константным — все mutable состояния хранятся
///   в State::ticks, а не внутри контроллера.
class TrotGaitController : public GaitController {
  public:
    /// @param stance_time    Длительность опоры [с]
    /// @param swing_time     Длительность переноса [с]
    /// @param time_step      Шаг симуляции [с]
    /// @param use_imu        Включить ПИД-стабилизацию по IMU
    /// @param default_stance Положения лап в покое (3×4)
    /// @param z_leg_lift     Высота подъёма лапы при переносе [м] (по умолчанию 0.14)
    /// @param z_error_constant Коэффициент коррекции высоты [м] (по умолчанию 0.02)
    /// @param pid_kp         Пропорциональный коэффициент ПИД
    /// @param pid_ki         Интегральный коэффициент ПИД
    /// @param pid_kd         Дифференциальный коэффициент ПИД
    TrotGaitController(double stance_time, double swing_time, double time_step, bool use_imu,
                       Eigen::MatrixXd default_stance, double z_leg_lift = 0.14,
                       double z_error_constant = 0.02, double pid_kp = 0.15, double pid_ki = 0.02,
                       double pid_kd = 0.002);

    /// Выполнить шаг походки.
    ///
    /// @param ticks       Текущий tick счётчика (State::ticks)
    /// @param current     Текущие положения лап (3×4)
    /// @param cmd_vel     Целевая скорость [vx, vy, vz] [м/с]
    /// @param robot_height Целевая высота корпуса [м]
    ///
    /// @return Новые положения лап (3×4)
    LegsMatrix step(int ticks, const LegsMatrix& current, const Eigen::Vector3d& cmd_vel, double robot_height) const;

    bool use_imu() const { return use_imu_; }
    TrotSwingController& swing_controller() { return swing_; }
    PIDController& pid_controller() { return pid_; }

    double time_step() const { return time_step_; }
    int stance_ticks() const { return GaitController::stance_ticks(); }
    int swing_ticks() const { return GaitController::swing_ticks(); }
    int phase_length() const { return GaitController::phase_length(); }

  private:
    bool use_imu_;                        ///< Флаг использования IMU
    TrotSwingController swing_;           ///< Контроллер фазы переноса
    TrotStanceController stance_;         ///< Контроллер фазы опоры
    PIDController pid_;                   ///< ПИД-стабилизация корпуса
};

}  // namespace quadropted
