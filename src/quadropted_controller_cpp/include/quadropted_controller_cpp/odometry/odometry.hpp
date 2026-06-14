/// @file odometry.hpp
/// @brief Оценка одометрии по контактам лап и IMU.
///
/// Одометрия строится на основе движения лап в фазе опоры (stance).
/// Когда лапа стоит на земле, её положение в мировой системе фиксировано,
/// и перемещение корпуса равно обратному перемещению лапы в системе корпуса.
///
/// ## Алгоритм
/// ```
/// for каждой лапы в контакте:
///   delta_pos = prev_foot_position - current_foot_position (в системе корпуса)
///   sum += delta_pos
/// odom += sum / contact_count * coeff
/// ```
/// Результат сглаживается скользящим средним (filter_window_size).
///
/// ## Детекция пробуксовки
/// Если угловая скорость IMU ниже порога (stall_ang_vel_threshold) в течение
/// stall_window тиков — робот считается застрявшим (is_stalled = true).
///
/// @note Точность одометрии зависит от качества детекции контакта.
///   В симуляции контакты идеальны; на реальном роботе нужна калибровка.
///
/// @warning stall_ang_vel_threshold должен быть > шума IMU, иначе
///   ложное срабатывание stall.
///
/// @see DogOdometryNode, ForwardKinematics

#pragma once
#include <Eigen/Dense>
#include <array>
#include <deque>
#include <optional>

namespace quadropted {

/// Состояние одометрии.
///
/// Содержит оценку положения (x, y, theta), скорости, а также состояние
/// каждого контакта и положения лап для расчёта дельт.
struct OdometryState {
    double x = 0.0, y = 0.0, theta = 0.0;    ///< Оценка положения [м, м, рад]
    double linear_velocity_x = 0.0, linear_velocity_y = 0.0;
    double imu_angular_velocity = 0.0;        ///< Угловая скорость с IMU [рад/с]
    double imu_linear_acceleration_x = 0.0;   ///< Линейное ускорение по X [м/с²]
    double imu_linear_acceleration_y = 0.0;   ///< Линейное ускорение по Y [м/с²]
    double imu_linear_acceleration_z = 0.0;   ///< Линейное ускорение по Z [м/с²]

    int filter_window_size = 14;              ///< Размер окна скользящего среднего
    std::deque<double> delta_x_queue, delta_y_queue;  ///< Очереди дельт для фильтрации
    double sum_delta_x = 0.0, sum_delta_y = 0.0;      ///< Суммы для скользящего среднего

    /// Текущие положения лап (результат FK) в системе корпуса.
    std::array<Eigen::Vector3d, 4> foot_positions{Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero(),
                                                  Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero()};

    /// Предыдущие положения лап (для расчёта дельты).
    /// std::optional — nullopt, если лапа не была в контакте.
    std::array<std::optional<Eigen::Vector2d>, 4> prev_foot_positions{};

    std::array<bool, 4> foot_contacts{false, false, false, false};  ///< Контакты лап (true = на земле)
    std::array<double, 12> joint_positions{};                       ///< Текущие углы сочленений [рад]

    int gazebo_clock_sec = 0, gazebo_clock_nanosec = 0;
    int encoder_pos = 0;

    bool is_stalled = false;               ///< Флаг пробуксовки
    int stall_consecutive_count = 0;        ///< Счётчик последовательных тиков пробуксовки

    int stall_window = 20;                                  ///< Окно для детекции пробуксовки [тики]
    double stall_ang_vel_threshold = 0.05;                   ///< Порог угловой скорости для stall [рад/с]
    double stall_exit_ang_vel_threshold = 0.1;               ///< Порог выхода из stall [рад/с]

    OdometryState() = default;
    explicit OdometryState(int window);

    /// Добавить дельту перемещения в скользящее среднее.
    ///
    /// @param dx  Перемещение по X [м]
    /// @param dy  Перемещение по Y [м]
    ///
    /// @note Если очередь превышает filter_window_size, удаляется старый элемент.
    void append_delta(double dx, double dy);

    /// @return Усреднённая дельта (dx, dy) из скользящего окна.
    std::pair<double, double> average_delta() const;

    /// Сброс одометрии в нулевое положение.
    void reset();
};

/// Нормализация угла в диапазон (-π, π].
///
/// @param angle  Угол [рад]
/// @return Нормализованный угол (-π, π]
double normalize_angle(double angle);

/// Один шаг обновления одометрии.
///
/// @param state               Состояние одометрии (модифицируется)
/// @param dt                  Шаг времени [с]
/// @param contact_count_coeff Коэффициент коррекции (0.65 по умолчанию)
///
/// @note contact_count_coeff < 1.0 компенсирует завышение скорости
///   из-за неточного детектирования контакта.
///
/// @warning Вызывать каждый control_loop tick.
void update_odometry(OdometryState& state, double dt, double contact_count_coeff = 0.65);

}  // namespace quadropted
