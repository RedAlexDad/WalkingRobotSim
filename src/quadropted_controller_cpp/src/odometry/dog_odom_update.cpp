#include "quadropted_controller_cpp/nodes/dog_odometry_node.hpp"

void DogOdometryNode::calculate_foot_positions() {
    try {
        odom_state_->foot_positions = fk_->forward_kinematics_all_legs(odom_state_->joint_positions);
    } catch (const std::exception& e) {
        RCLCPP_ERROR(get_logger(), "Error in forward kinematics: %s", e.what());
        odom_state_->foot_positions = {};
    }
}

void DogOdometryNode::update_odometry_step() {
    rclcpp::Time current_time = now();
    double dt = (current_time - last_position_time_).seconds();
    if (dt <= 0.0) return;

    quadropted::update_odometry(*odom_state_, dt);
    last_position_time_ = current_time;
}
