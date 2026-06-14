/// @file pid_controller.hpp
/// @brief ПИД-регулятор для стабилизации корпуса по IMU.
///
/// Используется в RestController и TrotGaitController для компенсации крена
/// и тангажа. Двухканальный: roll и pitch обрабатываются параллельно.
///
/// ## Особенности
/// - Интегральное насыщение (clamping) на уровне max_i_ = 0.2
/// - Дифференциальная составлящая с фильтрацией по времени
/// - Возможность сброса накопленной суммы при смене режима
///
/// @note Все коэффициенты (kp, ki, kd) настраиваются через YAML-параметры.
/// @warning При reset() интегральная и дифференциальная суммы ОБНУЛЯЮТСЯ.
/// @see RestController, TrotGaitController

#pragma once
#include <array>

namespace quadropted {

/// ПИД-регулятор с интегральным насыщением и фильтрацией производной.
///
/// Работает как двухканальный вектор [roll, pitch]:
///   - Канал 0: крен (roll)
///   - Канал 1: тангаж (pitch)
///
/// Формула: output = kp * error + ki * integral + kd * derivative
class PIDController {
  public:
    /// @param kp  Пропорциональный коэффициент (усиление по ошибке).
    ///            Типичное значение: 0.1–1.0.
    /// @param ki  Интегральный коэффициент (накопление ошибки).
    ///            Типичное значение: 0.01–0.1.
    /// @param kd  Дифференциальный коэффициент (скорость изменения ошибки).
    ///            Типичное значение: 0.001–0.01.
    PIDController(double kp, double ki, double kd);

    /// Вычислить управляющий сигнал ПИД-регулятора.
    ///
    /// @param roll         Текущий крен с IMU [рад].
    /// @param pitch        Текущий тангаж с IMU [рад].
    /// @param current_time  Текущее время [с] (для расчёта dt).
    ///
    /// @return Массив [compensated_roll, compensated_pitch] [рад].
    ///         Положительное значение = наклон корпуса в соответствующую сторону.
    ///
    /// @note dt вычисляется как разница между current_time и last_time_.
    ///   При первом вызове dt = 0 (производная = 0).
    std::array<double, 2> run(double roll, double pitch, double current_time);

    /// Сбросить накопленные суммы (I и D) и last_time_.
    ///
    /// @param current_time  Текущее время [с] — устанавливает last_time_.
    ///
    /// @warning После сброса первый run() даст D = 0 (из-за отсутствия истории).
    /// @see run()
    void reset(double current_time);

    /// Установить желаемые значения roll/pitch.
    ///
    /// @param roll   Целевой крен [рад].
    /// @param pitch  Целевой тангаж [рад].
    ///
    /// @note По умолчанию target = [0, 0] (горизонтальное положение).
    void set_desired(double roll, double pitch);

    const std::array<double, 2>& last_error() const { return last_error_; }
    const std::array<double, 2>& i_term() const { return i_term_; }
    const std::array<double, 2>& d_term() const { return d_term_; }

  private:
    double kp_, ki_, kd_;
    std::array<double, 2> desired_roll_pitch_{0.0, 0.0};
    std::array<double, 2> i_term_{0.0, 0.0}, d_term_{0.0, 0.0};
    std::array<double, 2> last_error_{0.0, 0.0};
    static constexpr double max_i_ = 0.2;   ///< Предел интегральной составляющей
    double last_time_ = -1.0;               ///< Время последнего run() [с]
};

}  // namespace quadropted
