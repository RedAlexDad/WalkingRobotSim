#include "quadropted_controller_cpp/controllers/rest_controller.hpp"

namespace quadropted {

RestController::RestController(Eigen::MatrixXd default_stance)
    : default_stance_(std::move(default_stance)), pid_(0.75, 2.29, 0.0) {}

Eigen::MatrixXd RestController::step(const State& state, const Command& cmd) const {
    (void)state;
    Eigen::MatrixXd temp = default_stance_;
    temp.row(2).setConstant(cmd.robot_height);
    return temp;
}

} // namespace quadropted
