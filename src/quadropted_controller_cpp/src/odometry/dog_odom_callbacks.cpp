#include <cmath>

#include "quadropted_controller_cpp/nodes/dog_odometry_node.hpp"

void DogOdometryNode::imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg) {
    double qx = msg->orientation.x;
    double qy = msg->orientation.y;
    double qz = msg->orientation.z;
    double qw = msg->orientation.w;

    double siny_cosp = 2.0 * (qw * qz + qx * qy);
    double cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz);
    double yaw = std::atan2(siny_cosp, cosy_cosp);

    odom_state_->theta = quadropted::normalize_angle(yaw);
    odom_state_->imu_angular_velocity = -msg->angular_velocity.z;
    odom_state_->imu_linear_acceleration_x = msg->linear_acceleration.x;
    odom_state_->imu_linear_acceleration_y = msg->linear_acceleration.y;
    odom_state_->imu_linear_acceleration_z = msg->linear_acceleration.z;
}

void DogOdometryNode::joint_states_callback(const std_msgs::msg::Float64MultiArray::SharedPtr msg) {
    if (msg->data.size() != 12) {
        RCLCPP_ERROR(get_logger(), "Unexpected number of joint angles: %zu. Expected 12.", msg->data.size());
        return;
    }
    for (size_t i = 0; i < 12; ++i) {
        odom_state_->joint_positions[i] = msg->data[i];
    }
}

void DogOdometryNode::foot_contacts_callback(const quadropted_msgs::msg::RobotFootContact::SharedPtr msg) {
    if (msg->contacts.size() != 4) {
        RCLCPP_ERROR(get_logger(), "Unexpected number of contacts: %zu. Expected 4.", msg->contacts.size());
        for (int i = 0; i < 4; ++i)
            odom_state_->foot_contacts[i] = false;
        return;
    }
    for (int i = 0; i < 4; ++i) {
        odom_state_->foot_contacts[i] = msg->contacts[i];
    }
}
