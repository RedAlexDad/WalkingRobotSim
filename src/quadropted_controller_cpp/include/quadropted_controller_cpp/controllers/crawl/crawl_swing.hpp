#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

class CrawlSwingController {
  public:
    CrawlSwingController(int swing_ticks, double time_step, double z_leg_lift, Eigen::MatrixXd default_stance,
                         int phase_length, int stance_ticks, double body_shift_y);

    Eigen::Vector3d raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel, bool shifted_left) const;
    double swing_height(double swing_prop) const;
    Eigen::Vector3d next_foot_location(double swing_prop, int leg_index, const LegsMatrix& current,
                                       const Eigen::Vector3d& cmd_vel, double robot_height) const;

  private:
    int swing_ticks_;
    double time_step_, z_leg_lift_;
    LegsMatrix default_stance_;
    int phase_length_;
    int stance_ticks_;
    double body_shift_y_;
    double total_time_;
    double stance_yaw_time_;
    double swing_total_time_;
};

}  // namespace quadropted
