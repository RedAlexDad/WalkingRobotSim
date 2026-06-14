#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

class RestController {
  public:
    explicit RestController(Eigen::MatrixXd default_stance, double pid_kp = 0.75, double pid_ki = 2.29,
                            double pid_kd = 0.0);
    LegsMatrix step(const State& state, const Command& cmd);
    const LegsMatrix& default_stance() const { return default_stance_; }
    PIDController& pid() { return pid_; }
    bool use_imu() const { return use_imu_; }
    void set_use_imu(bool v) { use_imu_ = v; }
    void reset();

  private:
    LegsMatrix default_stance_;
    PIDController pid_;
    bool use_imu_;
    double pid_last_time_ = 0.0;
};

}  // namespace quadropted
