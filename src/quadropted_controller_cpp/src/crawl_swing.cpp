#include "quadropted_controller_cpp/crawl_gait.hpp"

namespace quadropted {

CrawlSwingController::CrawlSwingController(int, int, double ts, int, double z_lift, Eigen::MatrixXd stance, double body_shift_y)
    : time_step_(ts), z_leg_lift_(z_lift), body_shift_y_(body_shift_y), default_stance_(std::move(stance)) {}

Eigen::Vector3d CrawlSwingController::raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel, bool) {
    Eigen::Vector2d delta = cmd_vel.head<2>() * phase_length_ * time_step_;
    Eigen::Vector3d delta_pos{delta.x(), delta.y(), 0};
    double theta = stance_ticks_ * time_step_ * cmd_vel.z();
    Eigen::Matrix3d rot = Eigen::AngleAxisd(theta, Eigen::Vector3d::UnitZ()).toRotationMatrix();
    Eigen::Vector3d result = rot * default_stance_.col(leg_index) + delta_pos;
    return result;
}

double CrawlSwingController::swing_height(double p) {
    return (p < 0.5) ? (p / 0.5) * z_leg_lift_ : z_leg_lift_ * (1.0 - (p - 0.5) / 0.5);
}

Eigen::Vector3d CrawlSwingController::next_foot_location(double swing_prop, int leg_index,
                                        const Eigen::MatrixXd& current,
                                        const Eigen::Vector3d& cmd_vel, bool) {
    double swing_h = swing_height(swing_prop);
    Eigen::Vector3d touchdown = raibert_touchdown_location(leg_index, cmd_vel, false);
    Eigen::Vector3d foot_loc = current.col(leg_index);
    double time_left = time_step_ * swing_ticks_ * (1.0 - swing_prop);
    if (time_left < 1e-6) { Eigen::Vector3d r = touchdown; r.z() = swing_h; return r; }
    Eigen::Vector3d velocity = (touchdown - foot_loc) / time_left;
    velocity.head<2>().array() *= 1.0;
    Eigen::Vector3d result = foot_loc;
    result.head<2>().array() *= 1.0;
    result += velocity * time_step_;
    result.z() = swing_h;
    return result;
}

} // namespace quadropted
