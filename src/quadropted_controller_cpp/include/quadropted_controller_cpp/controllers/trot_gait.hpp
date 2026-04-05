#pragma once
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot_swing.hpp"

namespace quadropted {

class TrotGaitController : public GaitController {
public:
    TrotGaitController(double stance_time, double swing_time, double time_step, bool use_imu, Eigen::MatrixXd default_stance);
    Eigen::MatrixXd step(int ticks, const Eigen::MatrixXd& current, const Eigen::Vector3d& cmd_vel) const;
    bool use_imu() const { return use_imu_; }
    const TrotSwingController& swing_controller() const { return swing_; }
private:
    bool use_imu_; TrotSwingController swing_;
};

}
