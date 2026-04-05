#include "quadropted_controller_cpp/odometry_state.hpp"

namespace quadropted {

OdometryState::OdometryState(int window)
    : filter_window_size(window), delta_x_queue(window, 0), delta_y_queue(window, 0) {}

void OdometryState::append_delta(double dx, double dy) {
    if (static_cast<int>(delta_x_queue.size()) >= filter_window_size) {
        sum_delta_x -= delta_x_queue.front();
        sum_delta_y -= delta_y_queue.front();
    }
    delta_x_queue.push_back(dx);
    delta_y_queue.push_back(dy);
    sum_delta_x += dx;
    sum_delta_y += dy;
}

std::pair<double, double> OdometryState::average_delta() const {
    int n = static_cast<int>(delta_x_queue.size());
    if (n == 0) return {0.0, 0.0};
    return {sum_delta_x / n, sum_delta_y / n};
}

void OdometryState::reset() {
    x = y = theta = linear_velocity_x = linear_velocity_y = imu_angular_velocity = 0.0;
    delta_x_queue.clear(); delta_y_queue.clear();
    sum_delta_x = sum_delta_y = 0.0;
    prev_foot_positions = {};
    foot_positions = {};
    foot_contacts = {};
    joint_positions = {};
}

} // namespace quadropted
