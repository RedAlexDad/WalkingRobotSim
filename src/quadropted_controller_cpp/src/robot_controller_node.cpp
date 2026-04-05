#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <Eigen/Dense>

#include "quadropted_controller_cpp/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/trot_gait.hpp"
#include "quadropted_controller_cpp/crawl_gait.hpp"
#include "quadropted_controller_cpp/rest_controller.hpp"
#include "quadropted_controller_cpp/pid_controller.hpp"

class RobotControllerNode : public rclcpp::Node {
public:
    RobotControllerNode() : Node("robot_controller_cpp"), rate_(60) {
        declare_parameter("verbose", false);
        verbose_ = get_parameter("verbose").as_bool();

        Eigen::MatrixXd default_stance(3, 4);
        double dx = 0.3762 * 0.5 + 0.02;
        double dy = 0.0935 * 0.5 + 0.0955;
        default_stance << dx, dx, -dx, -dx,
                          -dy, dy, -dy, dy,
                          0, 0, 0, 0;

        ik_ = std::make_unique<quadropted::InverseKinematics>(0.3762, 0.0935, 0.0, 0.0955, 0.213, 0.213);
        trot_ = std::make_unique<quadropted::TrotGaitController>(0.04, 0.18, 0.02, true, default_stance);

        joint_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
            "joint_group_controller/commands", 10);

        timer_ = create_wall_timer(
            std::chrono::milliseconds(1000 / rate_),
            std::bind(&RobotControllerNode::control_loop, this));

        RCLCPP_INFO(get_logger(), "Robot Controller C++ Node started");
    }

private:
    void control_loop() {
        // TODO: подписка на joint_states и imu
        // Для демонстрации — publish нулевых углов
        std_msgs::msg::Float64MultiArray msg;
        msg.data.resize(12, 0.0);
        joint_pub_->publish(msg);
    }

    int rate_;
    bool verbose_;
    std::unique_ptr<quadropted::InverseKinematics> ik_;
    std::unique_ptr<quadropted::TrotGaitController> trot_;
    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr joint_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<RobotControllerNode>());
    rclcpp::shutdown();
    return 0;
}
