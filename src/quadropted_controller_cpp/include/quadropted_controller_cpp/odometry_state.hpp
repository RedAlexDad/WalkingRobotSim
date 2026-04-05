#pragma once
#include <deque>
#include <array>
#include <optional>
#include <Eigen/Dense>

namespace quadropted {

struct OdometryState {
    // Позиция и ориентация
    double x = 0.0, y = 0.0, theta = 0.0;

    // Скорости
    double linear_velocity_x = 0.0, linear_velocity_y = 0.0;
    double imu_angular_velocity = 0.0;

    // Фильтр скользящего среднего — O(1) append/average
    int filter_window_size = 14;
    std::deque<double> delta_x_queue, delta_y_queue;
    double sum_delta_x = 0.0, sum_delta_y = 0.0;

    // Позиции лап
    std::array<Eigen::Vector3d, 4> foot_positions{Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero(),
                                                   Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero()};
    std::array<std::optional<Eigen::Vector2d>, 4> prev_foot_positions{};

    // Контакты и суставы
    std::array<bool, 4> foot_contacts{false, false, false, false};
    std::array<double, 12> joint_positions{};

    // Внешние данные
    int gazebo_clock_sec = 0, gazebo_clock_nanosec = 0;
    int encoder_pos = 0;

    OdometryState() = default;
    explicit OdometryState(int window);

    void append_delta(double dx, double dy);

    std::pair<double, double> average_delta() const;

    void reset();
};

} // namespace quadropted
