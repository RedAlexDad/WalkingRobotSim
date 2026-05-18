#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

class StandController {
  public:
    explicit StandController(FootMatrix default_stance);
    FootMatrix run(State& state, Command& cmd) const;
    const FootMatrix& default_stance() const { return default_stance_; }

  private:
    FootMatrix default_stance_{FootMatrix::Zero()};
    double body_velocity_scale_ = 0.01;
    double body_angular_scale_ = 0.005;
    double max_linear_velocity_ = 0.2;
    double max_angular_velocity_ = 0.5;
};

}  // namespace quadropted
