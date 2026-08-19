#include "quadropted_controller_cpp/nodes/robot_controller_node.hpp"

namespace quadropted {

LegsMatrix RobotControllerNode::step_rest(State& state, const Command& cmd) {
    state.ticks++;
    return rest_ctrl_->step(state, cmd);
}

}  // namespace quadropted
