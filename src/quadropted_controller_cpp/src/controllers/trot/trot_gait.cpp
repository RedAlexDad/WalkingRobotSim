#include "quadropted_controller_cpp/controllers/trot/trot_gait.hpp"

namespace quadropted {

TrotGaitController::TrotGaitController(double stance_time, double swing_time, double time_step, bool use_imu,
                                       Eigen::MatrixXd default_stance, double z_leg_lift,
                                       double z_error_constant, double pid_kp, double pid_ki,
                                       double pid_kd)
    : GaitController(stance_time, swing_time, time_step,
                     (Eigen::MatrixXi(4, 4) << 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0).finished(),
                     default_stance),
      use_imu_(use_imu),
      swing_(static_cast<int>(swing_time / time_step), time_step, z_leg_lift, default_stance, phase_length(),
             static_cast<int>(stance_time / time_step)),
      stance_(phase_length(), stance_ticks(), swing_ticks(), time_step, z_error_constant),
      pid_(pid_kp, pid_ki, pid_kd) {}

LegsMatrix TrotGaitController::step(int ticks, const LegsMatrix& current, const Eigen::Vector3d& cmd_vel,
                                    double robot_height) const {
    LegsMatrix next = current;
    Eigen::VectorXi contacts_vec = contacts(ticks);
    int sub = subphase_ticks(ticks);
    double swing_prop = static_cast<double>(sub) / swing_ticks_;
    for (int leg = 0; leg < 4; ++leg) {
        if (contacts_vec(leg) == 1) {
            next.col(leg) = stance_.next_foot_location(leg, current, cmd_vel, robot_height);
        } else {
            next.col(leg) = swing_.next_foot_location(swing_prop, leg, current, cmd_vel, robot_height);
        }
    }
    return next;
}

}  // namespace quadropted
