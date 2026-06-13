#pragma once

#include <cmath>
#include <geometry_msgs/msg/twist.hpp>
#include <memory>
#include <quadropted_msgs/msg/robot_foot_contact.hpp>
#include <quadropted_msgs/msg/robot_mode_command.hpp>
#include <quadropted_msgs/msg/robot_velocity.hpp>
#include <quadropted_msgs/srv/robot_behavior_command.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>

#include "quadropted_controller_cpp/controllers/crawl_gait.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot_gait.hpp"
#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/utils/math_utils.hpp"

namespace quadropted {

class RobotControllerNode : public rclcpp::Node {
  public:
    RobotControllerNode();

  private:
    void change_controller();
    LegsMatrix step_trot(State& state, const Command& cmd, double now_seconds);
    LegsMatrix step_crawl(State& state, const Command& cmd);
    LegsMatrix step_rest(State& state, const Command& cmd);
    LegsMatrix step_stand(State& state, Command& cmd);
    void publish_foot_contacts();
    void control_loop();

    int rate_;
    bool debug_mode_ = false;
    bool controller_change_needed_ = false;
    bool use_trot_ = false;
    bool use_crawl_ = false;
    bool use_stand_ = false;
    int startup_grace_ = 120;

    LegsMatrix default_stance_;
    State state_;
    Command command_;

    std::unique_ptr<TrotGaitController> trot_gait_;
    std::unique_ptr<CrawlGaitController> crawl_gait_;
    std::unique_ptr<RestController> rest_ctrl_;
    std::unique_ptr<StandController> stand_ctrl_;
    std::unique_ptr<InverseKinematics> ik_;

    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr joint_pub_;
    rclcpp::Publisher<quadropted_msgs::msg::RobotFootContact>::SharedPtr foot_contact_pub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotVelocity>::SharedPtr velocity_sub_;
    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotModeCommand>::SharedPtr mode_sub_;
    rclcpp::Service<quadropted_msgs::srv::RobotBehaviorCommand>::SharedPtr behavior_srv_;
    rclcpp::TimerBase::SharedPtr timer_;
};

}  // namespace quadropted
