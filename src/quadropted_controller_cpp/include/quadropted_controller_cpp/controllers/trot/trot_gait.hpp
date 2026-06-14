#pragma once
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_stance.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_swing.hpp"

namespace quadropted {

class TrotGaitController : public GaitController {
  public:
    TrotGaitController(double stance_time, double swing_time, double time_step, bool use_imu,
                       Eigen::MatrixXd default_stance, double z_leg_lift = 0.14,
                       double z_error_constant = 0.02, double pid_kp = 0.15, double pid_ki = 0.02,
                       double pid_kd = 0.002);
    LegsMatrix step(int ticks, const LegsMatrix& current, const Eigen::Vector3d& cmd_vel, double robot_height) const;
    bool use_imu() const { return use_imu_; }
    TrotSwingController& swing_controller() { return swing_; }
    PIDController& pid_controller() { return pid_; }
    double time_step() const { return time_step_; }
    int stance_ticks() const { return GaitController::stance_ticks(); }
    int swing_ticks() const { return GaitController::swing_ticks(); }
    int phase_length() const { return GaitController::phase_length(); }

  private:
    bool use_imu_;
    TrotSwingController swing_;
    TrotStanceController stance_;
    PIDController pid_;
};

}  // namespace quadropted
