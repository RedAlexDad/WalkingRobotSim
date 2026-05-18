#include <algorithm>

#include "quadropted_controller_cpp/odometry/odometry.hpp"

namespace quadropted {

OdometryState::OdometryState(int window)
    : filter_window_size(window), delta_x_queue(window), delta_y_queue(window) {
    for (int i = 0; i < 4; ++i) {
        prev_foot_positions[i] = std::nullopt;
    }
}

void OdometryState::append_delta(double dx, double dy) {
    delta_x_queue.reserve(filter_window_size);
    delta_y_queue.reserve(filter_window_size);
    if (delta_x_queue.size() == filter_window_size) {
        delta_x_queue.pop_front();
        delta_y_queue.pop_front();
    }
    delta_x_queue.push_back(dx);
    delta_y_queue.push_back(dy);
}

std::pair<double, double> OdometryState::average_delta() const {
    int n = delta_x_queue.size();
    if (n == 0) return {0.0, 0.0};
    return {delta_x_queue.sum() / n, delta_y_queue.sum() / n};
}

void OdometryState::reset() {
    x = 0.0;
    y = 0.0;
    theta = 0.0;
    linear_velocity_x = 0.0;
    linear_velocity_y = 0.0;
    imu_angular_velocity = 0.0;
    delta_x_queue.clear();
    delta_y_queue.clear();
    for (int i = 0; i < 4; ++i) {
        foot_positions[i] = Eigen::Vector3d::Zero();
        prev_foot_positions[i] = std::nullopt;
        foot_contacts[i] = false;
    }
    joint_positions.fill(0.0);
    gazebo_clock_sec = 0;
    gazebo_clock_nanosec = 0;
    encoder_pos = 0;
}

}  // namespace quadropted
