#include "quadropted_controller_cpp/nodes/robot_controller_node.hpp"

namespace quadropted {

LegsMatrix RobotControllerNode::step_crawl(State& state, const Command& cmd) {
    state.ticks++;

    bool has_command =
        std::abs(cmd.velocity[0]) > 1e-4 || std::abs(cmd.velocity[1]) > 1e-4 || std::abs(cmd.yaw_rate[2]) > 1e-4;
    if (!has_command) {
        LegsMatrix result = default_stance_;
        result.row(2).setConstant(cmd.robot_height);
        constexpr double alpha = 0.1;
        return state.foot_locations * (1.0 - alpha) + result * alpha;
    }

    Eigen::VectorXi contacts = crawl_gait_->contacts(state.ticks);
    int phase_idx = crawl_gait_->phase_index(state.ticks);
    LegsMatrix new_foot_locations{};

    for (int leg = 0; leg < 4; ++leg) {
        if (contacts(leg) == 1) {
            bool move_sideways = (phase_idx == 0 || phase_idx == 4);
            bool move_left = (phase_idx == 0);
            new_foot_locations.col(leg) = crawl_gait_->stance().next_foot_location(
                leg, state.foot_locations, Eigen::Vector3d{cmd.velocity[0], cmd.velocity[1], cmd.yaw_rate[2]},
                cmd.robot_height, crawl_gait_->is_first_cycle(), move_sideways, move_left);
        } else {
            int sub_ticks = crawl_gait_->subphase_ticks(state.ticks);
            double swing_prop = static_cast<double>(sub_ticks) / crawl_gait_->swing_ticks();

            new_foot_locations.col(leg) = crawl_gait_->swing().next_foot_location(
                swing_prop, leg, state.foot_locations,
                Eigen::Vector3d{cmd.velocity[0], cmd.velocity[1], cmd.yaw_rate[2]}, cmd.robot_height);
        }
    }

    if (state.ticks % 60 == 0) {
        RCLCPP_INFO(get_logger(), "[DEBUG] CRAWL step: ticks=%d contacts=[%d,%d,%d,%d]", state.ticks, contacts(0),
                    contacts(1), contacts(2), contacts(3));
    }

    return new_foot_locations;
}

}  // namespace quadropted
