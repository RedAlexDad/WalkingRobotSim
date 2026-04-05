#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include <algorithm>
#include <cmath>

namespace quadropted {

StandController::StandController(Eigen::MatrixXd default_stance)
    : default_stance_(std::move(default_stance)) {}

Eigen::MatrixXd StandController::run(State& state, Command& cmd) const {
    Eigen::MatrixXd temp = default_stance_;
    temp.row(2).setConstant(cmd.robot_height);

    Eigen::Vector3d linear_vel(cmd.velocity[0], cmd.velocity[1], cmd.velocity[2]);
    Eigen::Vector3d angular_vel(cmd.yaw_rate[0], cmd.yaw_rate[1], cmd.yaw_rate[2]);

    // Clamp velocities
    linear_vel = linear_vel.cwiseMax(-max_linear_velocity_).cwiseMin(max_linear_velocity_);
    angular_vel = angular_vel.cwiseMax(-max_angular_velocity_).cwiseMin(max_angular_velocity_);

    state.body_local_position[0] += linear_vel.x() * body_velocity_scale_;
    state.body_local_position[1] += linear_vel.y() * body_velocity_scale_;
    state.body_local_position[2] += linear_vel.z() * body_velocity_scale_;

    state.body_local_orientation[0] += angular_vel.x() * body_angular_scale_;
    state.body_local_orientation[1] += angular_vel.y() * body_angular_scale_;
    state.body_local_orientation[2] += angular_vel.z() * body_angular_scale_;

    return temp;
}

} // namespace quadropted
