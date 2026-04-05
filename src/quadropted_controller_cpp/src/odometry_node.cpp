#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <Eigen/Dense>

#include "quadropted_controller_cpp/forward_kinematics.hpp"
#include "quadropted_controller_cpp/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/odometry_state.hpp"
#include "quadropted_controller_cpp/odometry_update.hpp"

class OdometryNode : public rclcpp::Node {
public:
    OdometryNode() : Node("dog_odometry_cpp") {
        declare_parameter("verbose", false);
        declare_parameter("publish_rate", 50);
        declare_parameter("base_frame_id", "base");
        declare_parameter("odom_frame_id", "odom");
        declare_parameter("is_gazebo", true);

        verbose_ = get_parameter("verbose").as_bool();
        int rate = get_parameter("publish_rate").as_int();
        base_frame_ = get_parameter("base_frame_id").as_string();
        odom_frame_ = get_parameter("odom_frame_id").as_string();
        is_gazebo_ = get_parameter("is_gazebo").as_bool();

        fk_ = std::make_unique<quadropted::ForwardKinematics>(0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);

        odom_pub_ = create_publisher<nav_msgs::msg::Odometry>("odom", 10);
        tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

        joint_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
            "joint_group_controller/commands", 10,
            [this](const std_msgs::msg::Float64MultiArray::SharedPtr msg) {
                if (msg->data.size() == 12) {
                    for (int i = 0; i < 12; ++i) state_.joint_positions[i] = msg->data[i];
                }
            });

        timer_ = create_wall_timer(
            std::chrono::milliseconds(1000 / rate),
            std::bind(&OdometryNode::timer_callback, this));

        RCLCPP_INFO(get_logger(), "Dog Odometry C++ Node started");
    }

private:
    void timer_callback() {
        auto current_time = this->now();
        double dt = (current_time - last_time_).seconds();
        if (dt <= 0.0) return;

        // FK
        std::vector<double> angles(state_.joint_positions.begin(), state_.joint_positions.end());
        auto foot_pos = fk_->forward_kinematics_all_legs(angles);
        for (int i = 0; i < 4; ++i)
            state_.foot_positions[i] = foot_pos[i];

        // Odometry update
        quadropted::update_odometry(state_, dt);

        // Publish
        auto odom = nav_msgs::msg::Odometry();
        odom.header.stamp = current_time;
        odom.header.frame_id = odom_frame_;
        odom.child_frame_id = base_frame_;
        odom.pose.pose.position.x = state_.x;
        odom.pose.pose.position.y = state_.y;
        odom.pose.pose.orientation.w = std::cos(state_.theta / 2);
        odom.pose.pose.orientation.z = std::sin(state_.theta / 2);
        odom.twist.twist.linear.x = state_.linear_velocity_x;
        odom_pub_->publish(odom);

        // TF
        geometry_msgs::msg::TransformStamped tf;
        tf.header.stamp = current_time;
        tf.header.frame_id = odom_frame_;
        tf.child_frame_id = base_frame_;
        tf.transform.translation.x = state_.x;
        tf.transform.translation.y = state_.y;
        tf.transform.rotation.w = std::cos(state_.theta / 2);
        tf.transform.rotation.z = std::sin(state_.theta / 2);
        tf_broadcaster_->sendTransform(tf);

        last_time_ = current_time;
    }

    bool verbose_, is_gazebo_;
    std::string base_frame_, odom_frame_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr joint_sub_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Time last_time_;
    std::unique_ptr<quadropted::ForwardKinematics> fk_;
    quadropted::OdometryState state_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OdometryNode>());
    rclcpp::shutdown();
    return 0;
}
