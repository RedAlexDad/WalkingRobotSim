#include "quadropted_controller_cpp/trot_swing.hpp"

namespace quadropted {

TrotSwingController::TrotSwingController(int stance_ticks, int swing_ticks, double time_step,
                        int phase_length, double z_leg_lift, Eigen::MatrixXd default_stance)
    : swing_ticks_(swing_ticks), time_step_(time_step),
      z_leg_lift_(z_leg_lift), default_stance_(std::move(default_stance)) {}

Eigen::Vector3d TrotSwingController::raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel) {
    Eigen::Vector2d delta_pos_2d = cmd_vel.head<2>() * phase_length_ * time_step_;
    Eigen::Vector3d delta_pos{delta_pos_2d.x(), delta_pos_2d.y(), 0};
    double theta = swing_ticks_ * time_step_ * cmd_vel.z();
    Eigen::Matrix3d rot = rotz(theta);
    return rot * default_stance_.col(leg_index) + delta_pos;
}

double TrotSwingController::swing_height(double swing_prop) {
    if (swing_prop < 0.5) return (swing_prop / 0.5) * z_leg_lift_;
    return z_leg_lift_ * (1.0 - (swing_prop - 0.5) / 0.5);
}

Eigen::Vector3d TrotSwingController::next_foot_location(double swing_prop, int leg_index,
                                        const Eigen::MatrixXd& current,
                                        const Eigen::Vector3d& cmd_vel) {
    Eigen::Vector3d foot_loc = current.col(leg_index);
    double swing_h = swing_height(swing_prop);
    Eigen::Vector3d touchdown = raibert_touchdown_location(leg_index, cmd_vel);

    double time_left = time_step_ * swing_ticks_ * (1.0 - swing_prop);
    if (time_left < 1e-6) return touchdown;

    Eigen::Vector3d velocity = (touchdown - foot_loc) / time_left;
    velocity.head<2>().array() *= 1.0;  // XY mask
    Eigen::Vector3d delta = velocity * time_step_;

    Eigen::Vector3d result = foot_loc;
    result.head<2>().array() *= 1.0;  // XY mask
    result += delta;
    result.z() = swing_h;
    return result;
}

} // namespace quadropted
