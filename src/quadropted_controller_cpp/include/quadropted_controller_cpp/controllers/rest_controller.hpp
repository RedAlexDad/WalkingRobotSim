#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

class RestController {
  public:
    explicit RestController(FootMatrix default_stance);
    FootMatrix step(const State& state, const Command& cmd);
    const FootMatrix& default_stance() const { return default_stance_; }
    void reset();
    PIDController& pid() { return pid_; }

  private:
    mutable int step_ = 0;
    mutable double start_height_ = 0.0;
    mutable double target_height_ = 0.0;
    mutable FootMatrix target_stance_{FootMatrix::Zero()};
    mutable bool initial_ = true;
    mutable bool initialized_ = false;
    FootMatrix default_stance_{FootMatrix::Zero()};
    PIDController pid_{0.0, 0.0, 0.0};
    bool use_imu_ = false;
    double pid_last_time_ = 0.0;
};

}  // namespace quadropted
