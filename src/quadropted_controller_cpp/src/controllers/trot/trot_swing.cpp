#include "quadropted_controller_cpp/controllers/trot/trot_swing.hpp"

#include "quadropted_controller_cpp/utils/math_utils.hpp"

namespace quadropted {

TrotSwingController::TrotSwingController(int swing_ticks, double time_step, double z_leg_lift,
                                         Eigen::MatrixXd default_stance, int phase_length, int stance_ticks)
    : swing_ticks_(swing_ticks),
      time_step_(time_step),
      z_leg_lift_(z_leg_lift),
      default_stance_(default_stance),
      phase_length_(phase_length),
      stance_ticks_(stance_ticks),
      total_time_(phase_length * time_step),
      stance_yaw_time_(stance_ticks * time_step),
      swing_total_time_(swing_ticks * time_step),
      two_z_lift_(2.0 * z_leg_lift) {}

Eigen::Vector3d TrotSwingController::raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel) const {
    double total_time = total_time_;
    Eigen::Vector3d delta_pos;
    delta_pos << cmd_vel.x() * total_time, cmd_vel.y() * total_time, 0.0;

    // Python: stance_ticks * time_step для yaw rotation
    double theta = stance_yaw_time_ * cmd_vel.z();
    Eigen::Matrix3d rotation = rotz(theta);

    return rotation * default_stance_.col(leg_index) + delta_pos;
}

double TrotSwingController::swing_height(double swing_prop) const {
    if (swing_prop < 0.5) {
        return (swing_prop * 2.0) * z_leg_lift_;
    } else {
        return z_leg_lift_ * (1.0 - (swing_prop - 0.5) * 2.0);
    }
}

Eigen::Vector3d TrotSwingController::next_foot_location(double swing_prop, int leg_index, const LegsMatrix& current,
                                                        const Eigen::Vector3d& cmd_vel, double robot_height) const {
    assert(swing_prop >= 0.0 && swing_prop <= 1.0);

    Eigen::Vector3d foot_location = current.col(leg_index);
    double swing_h = swing_height(swing_prop);
    Eigen::Vector3d touchdown = raibert_touchdown_location(leg_index, cmd_vel);

    double time_left = swing_total_time_ * (1.0 - swing_prop);
    if (time_left < 1e-6) return touchdown;

    double inv_time_left = 1.0 / time_left;
    // Как в Python: velocity * XY_MASK — Z игнорируется
    Eigen::Vector3d velocity;
    velocity.x() = (touchdown.x() - foot_location.x()) * inv_time_left;
    velocity.y() = (touchdown.y() - foot_location.y()) * inv_time_left;
    velocity.z() = 0.0;

    Eigen::Vector3d delta_foot = velocity * time_step_;

    // Как в Python: foot_location * XY_MASK + z_vector + delta_foot
    // z_vector = [0, 0, swing_height + robot_height]
    Eigen::Vector3d result;
    result.x() = foot_location.x();
    result.y() = foot_location.y();
    result.z() = swing_h + robot_height;  // FIX: используем переданный robot_height
    result += delta_foot;

    return result;
}

}  // namespace quadropted
