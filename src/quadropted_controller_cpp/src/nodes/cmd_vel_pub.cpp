#include <cmath>
#include <geometry_msgs/msg/twist.hpp>
#include <quadropted_msgs/msg/robot_velocity.hpp>
#include <rclcpp/rclcpp.hpp>

namespace quadropted {

class CmdVelPub : public rclcpp::Node {
  public:
    CmdVelPub() : Node("cmd_vel_pub_cpp"), motion_start_time_(0.0) {
        declare_parameter("verbose", false);
        declare_parameter("vel_x_scale", 0.035);
        declare_parameter("vel_y_scale", 0.012);
        declare_parameter("vel_curve_factor", 100.0);
        declare_parameter("vel_clamp_max", 1.0);
        verbose_ = get_parameter("verbose").as_bool();
        vel_x_scale_ = get_parameter("vel_x_scale").as_double();
        vel_y_scale_ = get_parameter("vel_y_scale").as_double();
        vel_curve_factor_ = get_parameter("vel_curve_factor").as_double();
        vel_clamp_max_ = get_parameter("vel_clamp_max").as_double();

        cmd_vel_sub_ = create_subscription<geometry_msgs::msg::Twist>(
            "cmd_vel", 10, std::bind(&CmdVelPub::twist_callback, this, std::placeholders::_1));

        robot_vel_pub_ = create_publisher<quadropted_msgs::msg::RobotVelocity>("robot_velocity", 10);

        RCLCPP_INFO(get_logger(), "CmdVelPub C++ Node started");
    }

  private:
    void twist_callback(const geometry_msgs::msg::Twist::SharedPtr msg) {
        bool has_velocity =
            (std::abs(msg->linear.x) > 1e-6 || std::abs(msg->linear.y) > 1e-6 || std::abs(msg->linear.z) > 1e-6 ||
             std::abs(msg->angular.x) > 1e-6 || std::abs(msg->angular.y) > 1e-6 || std::abs(msg->angular.z) > 1e-6);

        auto current_time = this->now();
        if (has_velocity && motion_start_time_ == 0.0) {
            motion_start_time_ = current_time.seconds();
            if (verbose_) RCLCPP_INFO(get_logger(), "Motion started at: %.3f", motion_start_time_);
        }

        if (!has_velocity && motion_start_time_ > 0.0) {
            double elapsed = current_time.seconds() - motion_start_time_;
            if (verbose_) RCLCPP_INFO(get_logger(), "Motion stopped, elapsed: %.3f sec", elapsed);
            motion_start_time_ = 0.0;
        }

        auto out = std::make_unique<quadropted_msgs::msg::RobotVelocity>();
        out->robot_id = 1;

        out->cmd_vel.linear.x = multiply_and_limit(msg->linear.x);
        out->cmd_vel.linear.y = multiply_and_limit_y(msg->linear.y);
        out->cmd_vel.linear.z = msg->linear.z;
        out->cmd_vel.angular.x = msg->angular.x;
        out->cmd_vel.angular.y = msg->angular.y;
        out->cmd_vel.angular.z = limit(msg->angular.z);

        robot_vel_pub_->publish(std::move(out));
    }

    double multiply_and_limit(double value) {
        double adjusted = value * vel_x_scale_;
        double scaled = vel_x_scale_ * (1.0 - std::exp(-vel_curve_factor_ * std::abs(adjusted)));
        return limit(value >= 0 ? scaled : -scaled);
    }

    double multiply_and_limit_y(double value) {
        double adjusted = value * vel_y_scale_;
        double scaled = vel_y_scale_ * (1.0 - std::exp(-vel_curve_factor_ * std::abs(adjusted)));
        return limit(value >= 0 ? scaled : -scaled);
    }

    double limit(double value) const {
        if (value > vel_clamp_max_) return vel_clamp_max_;
        if (value < -vel_clamp_max_) return -vel_clamp_max_;
        return value;
    }

    bool verbose_;
    double vel_x_scale_;
    double vel_y_scale_;
    double vel_curve_factor_;
    double vel_clamp_max_;
    double motion_start_time_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
    rclcpp::Publisher<quadropted_msgs::msg::RobotVelocity>::SharedPtr robot_vel_pub_;
};

}  // namespace quadropted

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<quadropted::CmdVelPub>());
    rclcpp::shutdown();
    return 0;
}
