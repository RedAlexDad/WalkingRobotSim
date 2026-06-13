#pragma once

#include <tf2_ros/transform_broadcaster.h>

#include <geometry_msgs/msg/transform_stamped.hpp>
#include <memory>
#include <nav_msgs/msg/odometry.hpp>
#include <quadropted_msgs/msg/robot_foot_contact.hpp>
#include <quadropted_msgs/msg/robot_velocity.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <std_msgs/msg/bool.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <string>
#include <visualization_msgs/msg/marker.hpp>
#include <visualization_msgs/msg/marker_array.hpp>

#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/odometry/odometry.hpp"
#include "quadropted_controller_cpp/utils/message_builders.hpp"

class DogOdometryNode : public rclcpp::Node {
  public:
    DogOdometryNode();

  private:
    void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg);
    void joint_states_callback(const std_msgs::msg::Float64MultiArray::SharedPtr msg);
    void foot_contacts_callback(const quadropted_msgs::msg::RobotFootContact::SharedPtr msg);
    void calculate_foot_positions();
    void update_odometry_step();
    void publish_odometry();
    void publish_markers();
    void publish_stall_status();
    void timer_callback();

    std::unique_ptr<quadropted::ForwardKinematics> fk_;
    std::unique_ptr<quadropted::OdometryState> odom_state_;
    rclcpp::Time last_position_time_;

    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr stall_pub_;
    rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_pub_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
    rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr joint_states_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotFootContact>::SharedPtr foot_contacts_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotVelocity>::SharedPtr velocity_sub_;

    rclcpp::TimerBase::SharedPtr timer_;

    bool verbose_ = false;
    int publish_rate_ = 50;
    bool has_imu_heading_ = true;
    bool enable_odom_tf_ = false;
    std::string base_frame_id_ = "base";
    std::string odom_frame_id_ = "odom";
};
