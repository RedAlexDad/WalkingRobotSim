#include "quadropted_controller_cpp/rest_controller.hpp"

namespace quadropted {

StandController::StandController(Eigen::MatrixXd default_stance)
    : default_stance_(std::move(default_stance)) {}

const Eigen::MatrixXd& StandController::default_stance() const { return default_stance_; }

Eigen::MatrixXd StandController::run(StandState& state, Command& cmd) {
    Eigen::MatrixXd result = default_stance_;
    result.row(2).setConstant(cmd.robot_height);
    return result;
}

} // namespace quadropted
