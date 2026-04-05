#pragma once
#include <Eigen/Dense>
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

class RestController {
public:
    explicit RestController(Eigen::MatrixXd default_stance);
    Eigen::MatrixXd step(const State& state, const Command& cmd) const;
    const Eigen::MatrixXd& default_stance() const { return default_stance_; }
    PIDController& pid() { return pid_; }
private:
    Eigen::MatrixXd default_stance_;
    PIDController pid_;
};

} // namespace quadropted
