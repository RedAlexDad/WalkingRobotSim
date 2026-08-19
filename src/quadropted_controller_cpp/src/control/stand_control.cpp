#include "quadropted_controller_cpp/nodes/robot_controller_node.hpp"

namespace quadropted {

LegsMatrix RobotControllerNode::step_stand(State& state, Command& cmd) {
    static int stand_debug_counter = 0;
    stand_debug_counter++;

    if (stand_debug_counter % 30 == 0) {
        RCLCPP_INFO(get_logger(),
                    "[STAND DEBUG] cmd: vx=%.4f vy=%.4f vz=%.4f ax=%.4f ay=%.4f az=%.4f | "
                    "pos: x=%.4f y=%.4f z=%.4f | ori: r=%.4f p=%.4f y=%.4f",
                    cmd.velocity[0], cmd.velocity[1], cmd.velocity[2], cmd.yaw_rate[0], cmd.yaw_rate[1],
                    cmd.yaw_rate[2], state.body_local_position[0], state.body_local_position[1],
                    state.body_local_position[2], state.body_local_orientation[0], state.body_local_orientation[1],
                    state.body_local_orientation[2]);
    }

    return stand_ctrl_->run(state, cmd);
}

}  // namespace quadropted
