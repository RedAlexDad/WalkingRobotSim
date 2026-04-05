#include "quadropted_controller_cpp/rest_controller.hpp"

namespace quadropted {

RestController::RestController(Eigen::MatrixXd default_stance)
    : default_stance_(std::move(default_stance)),
      pid_(0.15, 0.02, 0.002) {}

Eigen::MatrixXd RestController::step(const StandState& state, const Command& cmd) {
    Eigen::MatrixXd result = default_stance_;
    result.row(2).setConstant(cmd.robot_height);
    return result;
}

const Eigen::MatrixXd& RestController::default_stance() const { return default_stance_; }
PIDController& RestController::pid() { return pid_; }

} // namespace quadropted
