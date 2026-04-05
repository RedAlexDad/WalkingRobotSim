#pragma once
#include <Eigen/Dense>
#include "quadropted_controller_cpp/trot_swing.hpp"
#include "quadropted_controller_cpp/gait_controller.hpp"
#include "quadropted_controller_cpp/pid_controller.hpp"

namespace quadropted {

class TrotGaitController : public GaitController {
public:
    TrotGaitController(double stance_time, double swing_time, double time_step,
                       bool use_imu, Eigen::MatrixXd default_stance);

    Eigen::MatrixXd step(int ticks, const Eigen::MatrixXd& current,
                          const Eigen::Vector3d& cmd_vel);

    bool use_imu() const;
    TrotSwingController& swing_controller();

private:
    bool use_imu_;
    TrotSwingController swing_;
};

} // namespace quadropted
