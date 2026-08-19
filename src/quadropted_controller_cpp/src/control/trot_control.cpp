#include <cmath>

#include "quadropted_controller_cpp/nodes/robot_controller_node.hpp"
#include "quadropted_controller_cpp/utils/math_utils.hpp"

namespace quadropted {

LegsMatrix RobotControllerNode::step_trot(State& state, const Command& cmd, double now_seconds) {
    state.ticks++;

    bool has_command =
        std::abs(cmd.velocity[0]) > 1e-4 || std::abs(cmd.velocity[1]) > 1e-4 || std::abs(cmd.yaw_rate[2]) > 1e-4;
    if (!has_command) {
        LegsMatrix result = default_stance_;
        result.row(2).setConstant(cmd.robot_height);
        constexpr double alpha = 0.1;
        return state.foot_locations * (1.0 - alpha) + result * alpha;
    }

    LegsMatrix new_foot_locations =
        trot_gait_->step(state.ticks, state.foot_locations,
                         Eigen::Vector3d{cmd.velocity[0], cmd.velocity[1], cmd.yaw_rate[2]}, cmd.robot_height);

    if (state.ticks % 60 == 0) {
        RCLCPP_INFO(get_logger(),
                    "[DEBUG] foot_locs: FR=(%.4f,%.4f,%.4f) FL=(%.4f,%.4f,%.4f) "
                    "RR=(%.4f,%.4f,%.4f) RL=(%.4f,%.4f,%.4f)",
                    state.foot_locations(0, 0), state.foot_locations(1, 0), state.foot_locations(2, 0),
                    state.foot_locations(0, 1), state.foot_locations(1, 1), state.foot_locations(2, 1),
                    state.foot_locations(0, 2), state.foot_locations(1, 2), state.foot_locations(2, 2),
                    state.foot_locations(0, 3), state.foot_locations(1, 3), state.foot_locations(2, 3));
    }

    if (trot_gait_->use_imu()) {
        auto comp = trot_gait_->pid_controller().run(state.imu_roll, state.imu_pitch, now_seconds);
        Eigen::Matrix3d rot = rotxyz(-comp[0], -comp[1], 0);
        new_foot_locations = (rot * new_foot_locations).eval();
    }

    if (state.ticks % 60 == 0) {
        Eigen::VectorXi contacts = trot_gait_->contacts(state.ticks);
        RCLCPP_INFO(get_logger(), "[DEBUG] TROT step: ticks=%d contacts=[%d,%d,%d,%d]", state.ticks, contacts(0),
                    contacts(1), contacts(2), contacts(3));
    }

    return new_foot_locations;
}

}  // namespace quadropted
