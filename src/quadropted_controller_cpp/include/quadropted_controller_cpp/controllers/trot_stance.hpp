#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

class TrotStanceController {
  public:
    TrotStanceController(int phase_length, int stance_ticks, int swing_ticks, double time_step,
                         double z_error_constant);
    Eigen::Vector3d position_delta(int leg_index, const LegsMatrix& state_foot, const Eigen::Vector3d& cmd_vel,
                                   double robot_height) const;
    Eigen::Vector3d next_foot_location(int leg_index, const LegsMatrix& state_foot, const Eigen::Vector3d& cmd_vel,
                                       double robot_height) const;

  private:
    int phase_length_, stance_ticks_, swing_ticks_;
    double time_step_, z_error_constant_, inv_scale_;
};

}  // namespace quadropted
