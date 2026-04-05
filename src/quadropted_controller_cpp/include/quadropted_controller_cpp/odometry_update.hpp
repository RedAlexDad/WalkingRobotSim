#pragma once
#include <cmath>
#include "quadropted_controller_cpp/odometry_state.hpp"

namespace quadropted {

inline double normalize_angle(double angle) {
    return std::atan2(std::sin(angle), std::cos(angle));
}

inline void update_odometry(OdometryState& state, double dt, double contact_count_coeff = 0.65) {
    if (dt <= 0.0) return;

    double delta_x_total = 0.0, delta_y_total = 0.0;
    double contact_count = 0.0;

    for (int i = 0; i < 4; ++i) {
        if (state.foot_contacts[i]) {
            double foot_rel_x = state.foot_positions[i].x();
            double foot_rel_y = state.foot_positions[i].y();

            if (state.prev_foot_positions[i].has_value()) {
                double delta_x = foot_rel_x - state.prev_foot_positions[i]->x();
                double delta_y = foot_rel_y - state.prev_foot_positions[i]->y();
                delta_x_total += delta_x;
                delta_y_total += -delta_y;
                contact_count += contact_count_coeff;
            }
            state.prev_foot_positions[i] = Eigen::Vector2d{foot_rel_x, foot_rel_y};
        }
    }

    double cos_t = std::cos(state.theta);
    double sin_t = std::sin(state.theta);

    if (contact_count > 0.0) {
        double avg_dx = delta_x_total / contact_count;
        double avg_dy = delta_y_total / contact_count;
        state.append_delta(avg_dx, avg_dy);
        auto [avg_delta_x, avg_delta_y] = state.average_delta();

        state.x += avg_delta_x * cos_t - avg_delta_y * sin_t;
        state.y += avg_delta_x * sin_t + avg_delta_y * cos_t;
    } else {
        double delta_x = state.linear_velocity_x * dt;
        double delta_y = state.linear_velocity_y * dt;
        state.append_delta(delta_x, delta_y);
        auto [avg_delta_x, avg_delta_y] = state.average_delta();

        state.x += avg_delta_x * cos_t - avg_delta_y * sin_t;
        state.y += avg_delta_x * sin_t + avg_delta_y * cos_t;
    }
}

} // namespace quadropted
