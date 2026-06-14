#include "quadropted_controller_cpp/controllers/crawl/crawl_swing.hpp"

#include "quadropted_controller_cpp/utils/math_utils.hpp"

namespace quadropted {

CrawlSwingController::CrawlSwingController(int swing_ticks, double time_step, double z_leg_lift,
                                           Eigen::MatrixXd default_stance, int phase_length, int stance_ticks,
                                           double body_shift_y)
    : swing_ticks_(swing_ticks),
      time_step_(time_step),
      z_leg_lift_(z_leg_lift),
      default_stance_(default_stance),
      phase_length_(phase_length),
      stance_ticks_(stance_ticks),
      body_shift_y_(body_shift_y),
      total_time_(phase_length * time_step),
      stance_yaw_time_(stance_ticks * time_step),
      swing_total_time_(swing_ticks * time_step) {}

Eigen::Vector3d CrawlSwingController::raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel,
                                                                 bool shifted_left) const {
    // Python: delta_pos_2d = command.velocity * phase_length * time_step
    double total_time = total_time_;
    Eigen::Vector3d delta_pos;
    delta_pos << cmd_vel.x() * total_time, cmd_vel.y() * total_time, 0.0;

    // Python: theta = stance_ticks * time_step * command.yaw_rate
    double theta = stance_yaw_time_ * cmd_vel.z();
    Eigen::Matrix3d rotation = rotz(theta);

    // Python: shift_correction[1] = -body_shift_y if shifted_left else body_shift_y
    Eigen::Vector3d shift_correction;
    shift_correction << 0.0, (shifted_left ? -body_shift_y_ : body_shift_y_), 0.0;

    return rotation * default_stance_.col(leg_index) + delta_pos + shift_correction;
}

double CrawlSwingController::swing_height(double swing_prop) const {
    if (swing_prop < 0.5) {
        return (swing_prop * 2.0) * z_leg_lift_;
    } else {
        return z_leg_lift_ * (1.0 - (swing_prop - 0.5) * 2.0);
    }
}

Eigen::Vector3d CrawlSwingController::next_foot_location(double swing_prop, int leg_index, const LegsMatrix& current,
                                                         const Eigen::Vector3d& cmd_vel, double robot_height,
                                                         bool shifted_left) const {
    assert(swing_prop >= 0.0 && swing_prop <= 1.0);

    // Python: foot_location = state.foot_locations[:, leg_index]
    Eigen::Vector3d foot_location = current.col(leg_index);

    double swing_h = swing_height(swing_prop);

    Eigen::Vector3d touchdown = raibert_touchdown_location(leg_index, cmd_vel, shifted_left);

    double time_left = swing_total_time_ * (1.0 - swing_prop);
    if (time_left < 1e-6) return touchdown;

    // Python: velocity * np.array([1, 1, 0]) — XY mask
    Eigen::Vector3d velocity = (touchdown - foot_location) / time_left;
    velocity.z() = 0.0;

    Eigen::Vector3d delta_foot = velocity * time_step_;

    // Python: z_vector = [0, 0, swing_height_ + command.robot_height]
    Eigen::Vector3d z_vector;
    z_vector << 0.0, 0.0, swing_h + robot_height;

    // Python: foot_location * [1,1,0] + z_vector + delta_foot
    return Eigen::Vector3d(foot_location.x(), foot_location.y(), 0.0) + z_vector + delta_foot;
}

}  // namespace quadropted
