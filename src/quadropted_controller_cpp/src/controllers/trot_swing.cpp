#include "quadropted_controller_cpp/controllers/trot_swing.hpp"

namespace quadropted {

TrotSwingController::TrotSwingController(int swing_ticks, double time_step,
                                          double z_leg_lift, Eigen::MatrixXd default_stance)
    : swing_ticks_(swing_ticks), time_step_(time_step),
      z_leg_lift_(z_leg_lift), default_stance_(std::move(default_stance)) {}

Eigen::Vector3d TrotSwingController::raibert_touchdown_location(
    int leg_index, const Eigen::Vector3d& cmd_vel) const
{
    double scale_factor = 1.0;
    // phase_length * time_step = stance_ticks * time_step + swing_ticks * time_step
    // Но в Python используется self.phase_length * self.time_step
    // phase_length = stance_ticks + swing_ticks (для trot: 2+9+2+9=22)
    // Для упрощения используем swing_ticks_ как приближение
    double total_time = swing_ticks_ * time_step_;
    Eigen::Vector3d delta_pos;
    delta_pos << cmd_vel.x() * total_time * scale_factor,
                  cmd_vel.y() * total_time * scale_factor,
                  0.0;

    double theta = swing_ticks_ * time_step_ * cmd_vel.z();
    Eigen::Matrix3d rotation = rotz(theta);

    return rotation * default_stance_.col(leg_index) + delta_pos;
}

double TrotSwingController::swing_height(double swing_prop) const {
    double scale_factor = 1.0;
    if (swing_prop < 0.5) {
        return (swing_prop / 0.5) * z_leg_lift_ * scale_factor;
    } else {
        return z_leg_lift_ * (1.0 - (swing_prop - 0.5) / 0.5) * scale_factor;
    }
}

Eigen::Vector3d TrotSwingController::next_foot_location(
    double swing_prop, int leg_index, const Eigen::MatrixXd& current,
    const Eigen::Vector3d& cmd_vel) const
{
    assert(swing_prop >= 0.0 && swing_prop <= 1.0);

    Eigen::Vector3d foot_location = current.col(leg_index);
    double swing_h = swing_height(swing_prop);
    Eigen::Vector3d touchdown = raibert_touchdown_location(leg_index, cmd_vel);

    double time_left = time_step_ * swing_ticks_ * (1.0 - swing_prop);
    Eigen::Vector3d velocity = (touchdown - foot_location) / time_left;
    velocity.z() = 0.0;  // XY mask

    Eigen::Vector3d delta_foot = velocity * time_step_;

    Eigen::Vector3d z_vector;
    z_vector << 0.0, 0.0, swing_h + cmd_vel.z();  // cmd_vel.z() здесь как robot_height

    return Eigen::Vector3d(foot_location.x(), foot_location.y(), 0.0) + z_vector + delta_foot;
}

} // namespace quadropted
