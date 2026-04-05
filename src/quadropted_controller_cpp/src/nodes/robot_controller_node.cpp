#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <quadropted_msgs/msg/robot_foot_contact.hpp>
#include <quadropted_msgs/msg/robot_velocity.hpp>
#include <quadropted_msgs/msg/robot_mode_command.hpp>

#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/controllers/trot_gait.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/controllers/crawl_gait.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/utils/math_utils.hpp"

#include <Eigen/Dense>
#include <cmath>
#include <array>

class RobotControllerNode : public rclcpp::Node {
public:
    RobotControllerNode() : Node("robot_controller_cpp") {
        // Параметры
        declare_parameter("verbose", false);
        declare_parameter("use_imu", true);
        declare_parameter("time_step", 0.02);
        declare_parameter("stance_time", 0.04);
        declare_parameter("swing_time", 0.18);
        declare_parameter("control_rate", 50.0);
        declare_parameter("robot_id", 1);

        verbose_     = get_parameter("verbose").as_bool();
        use_imu_     = get_parameter("use_imu").as_bool();
        time_step_   = get_parameter("time_step").as_double();
        stance_time_ = get_parameter("stance_time").as_double();
        swing_time_  = get_parameter("swing_time").as_double();
        control_rate_= get_parameter("control_rate").as_double();
        robot_id_    = static_cast<int>(get_parameter("robot_id").as_int());

        // Параметры робота
        double body_length = 0.3762, body_width = 0.0935;
        double l1 = 0.0, l2 = 0.0955, l3 = 0.213, l4 = 0.213;

        // Default stance
        double delta_x = body_length / 2.0;
        double delta_y = body_width / 2.0 + l2;
        double x_shift_front = 0.02;
        double x_shift_back = 0.0;
        default_height_ = 0.25;

        default_stance_ = Eigen::MatrixXd(3, 4);
        default_stance_ << delta_x + x_shift_front,  delta_x + x_shift_front,  -delta_x + x_shift_back, -delta_x + x_shift_back,
                          -delta_y,                  delta_y,                  -delta_y,                 delta_y,
                           0.0,                       0.0,                       0.0,                     0.0;

        // IK solver
        ik_ = std::make_unique<quadropted::InverseKinematics>(
            body_length, body_width, l1, l2, l3, l4);

        // Контроллеры
        trot_gait_ = std::make_unique<quadropted::TrotGaitController>(
            stance_time_, swing_time_, time_step_, use_imu_, default_stance_);

        rest_controller_ = std::make_unique<quadropted::RestController>(default_stance_);

        // Состояние и команды
        state_.body_height = default_height_;
        state_.robot_height = default_height_;
        state_.behavior_state = quadropted::BehaviorState::REST;
        command_.robot_height = default_height_;

        // Начальная позиция ног — default stance
        for (int i = 0; i < 4; ++i) {
            state_.foot_locations[i] = default_stance_.col(i);
        }

        // Publisher
        joint_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
            "joint_group_controller/commands", 10);

        // Subscriptions
        imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
            "imu_plugin/out", 10,
            [this](const sensor_msgs::msg::Imu::SharedPtr msg) { imu_callback(msg); });

        velocity_sub_ = create_subscription<quadropted_msgs::msg::RobotVelocity>(
            "robot_velocity", 10,
            [this](const quadropted_msgs::msg::RobotVelocity::SharedPtr msg) { velocity_callback(msg); });

        mode_sub_ = create_subscription<quadropted_msgs::msg::RobotModeCommand>(
            "robot_mode_command", 10,
            [this](const quadropted_msgs::msg::RobotModeCommand::SharedPtr msg) { mode_callback(msg); });

        // Timer
        double timer_period = 1.0 / control_rate_;
        timer_ = create_wall_timer(
            std::chrono::duration<double>(timer_period),
            [this]() { control_callback(); });

        RCLCPP_INFO(get_logger(), "Robot Controller Node (C++) has been started.");
    }

private:
    void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg) {
        double qx = msg->orientation.x;
        double qy = msg->orientation.y;
        double qz = msg->orientation.z;
        double qw = msg->orientation.w;

        // Roll и Pitch из кватерниона
        double sinr_cosp = 2.0 * (qw * qx + qy * qz);
        double cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy);
        state_.imu_roll = std::atan2(sinr_cosp, cosr_cosp);

        double sinp = 2.0 * (qw * qy - qz * qx);
        if (std::abs(sinp) >= 1)
            state_.imu_pitch = std::copysign(M_PI / 2.0, sinp);
        else
            state_.imu_pitch = std::asin(sinp);
    }

    void velocity_callback(const quadropted_msgs::msg::RobotVelocity::SharedPtr msg) {
        if (static_cast<int>(msg->robot_id) != robot_id_) return;

        command_.velocity[0] = msg->cmd_vel.linear.x;
        command_.velocity[1] = msg->cmd_vel.linear.y;
        command_.velocity[2] = msg->cmd_vel.linear.z;

        command_.yaw_rate[0] = msg->cmd_vel.angular.x;
        command_.yaw_rate[1] = msg->cmd_vel.angular.y;
        command_.yaw_rate[2] = msg->cmd_vel.angular.z;
    }

    void mode_callback(const quadropted_msgs::msg::RobotModeCommand::SharedPtr msg) {
        if (static_cast<int>(msg->robot_id) != robot_id_) return;

        std::string mode = msg->mode;
        if (mode == "REST") {
            command_.rest_event = true;
            command_.trot_event = false;
            command_.crawl_event = false;
            command_.stand_event = false;
        } else if (mode == "TROT") {
            command_.rest_event = false;
            command_.trot_event = true;
            command_.crawl_event = false;
            command_.stand_event = false;
        } else if (mode == "CRAWL") {
            command_.rest_event = false;
            command_.trot_event = false;
            command_.crawl_event = true;
            command_.stand_event = false;
        } else if (mode == "STAND") {
            command_.rest_event = false;
            command_.trot_event = false;
            command_.crawl_event = false;
            command_.stand_event = true;
        }

        change_controller();
    }

    void change_controller() {
        if (command_.trot_event && command_.rest_event) {
            // REST
            state_.behavior_state = quadropted::BehaviorState::REST;
            state_.body_local_position[2] = -0.15;
            command_.rest_event = false;

            // TROT
            state_.behavior_state = quadropted::BehaviorState::TROT;
            state_.ticks = 0;
            command_.trot_event = false;
            RCLCPP_INFO(get_logger(), "Switched to TROT controller");
        } else if (command_.trot_event) {
            if (state_.behavior_state == quadropted::BehaviorState::REST) {
                state_.behavior_state = quadropted::BehaviorState::TROT;
                state_.ticks = 0;
            }
            command_.trot_event = false;
            RCLCPP_INFO(get_logger(), "Switched to TROT controller");
        } else if (command_.rest_event) {
            state_.behavior_state = quadropted::BehaviorState::REST;
            command_.rest_event = false;
            RCLCPP_INFO(get_logger(), "Switched to REST controller");
        } else if (command_.stand_event) {
            if (state_.behavior_state != quadropted::BehaviorState::STAND) {
                state_.behavior_state = quadropted::BehaviorState::STAND;
                state_.body_local_position[2] = 0.005;
            }
            command_.stand_event = false;
            RCLCPP_INFO(get_logger(), "Switched to STAND controller");
        }
    }

    void control_callback() {
        Eigen::MatrixXd new_foot_locations(3, 4);

        // Инициализация foot_locations из state
        Eigen::MatrixXd current(3, 4);
        for (int i = 0; i < 4; ++i) {
            current.col(i) = state_.foot_locations[i];
        }

        switch (state_.behavior_state) {
            case quadropted::BehaviorState::REST: {
                new_foot_locations = default_stance_;
                new_foot_locations.row(2).setConstant(command_.robot_height);
                break;
            }
            case quadropted::BehaviorState::TROT: {
                Eigen::Vector3d cmd_vel;
                cmd_vel << command_.velocity[0], command_.velocity[1], command_.velocity[2];
                new_foot_locations = trot_gait_->step(state_.ticks, current, cmd_vel);
                state_.ticks++;
                break;
            }
            case quadropted::BehaviorState::STAND: {
                new_foot_locations = default_stance_;
                new_foot_locations.row(2).setConstant(command_.robot_height);
                break;
            }
            default: {
                new_foot_locations = default_stance_;
                new_foot_locations.row(2).setConstant(command_.robot_height);
                break;
            }
        }

        // Обновляем состояние
        for (int i = 0; i < 4; ++i) {
            state_.foot_locations[i] = new_foot_locations.col(i);
        }

        // Вычисляем углы суставов через IK
        std::vector<double> angles = ik_->inverse_kinematics(
            new_foot_locations,
            state_.body_local_position[0], state_.body_local_position[1], state_.body_local_position[2],
            state_.body_local_orientation[0], state_.body_local_orientation[1], state_.body_local_orientation[2]);

        // Публикуем
        std_msgs::msg::Float64MultiArray joint_msg;
        joint_msg.data = angles;
        joint_pub_->publish(joint_msg);
    }

    // Members
    bool verbose_ = false;
    bool use_imu_ = true;
    double time_step_ = 0.02;
    double stance_time_ = 0.04;
    double swing_time_ = 0.18;
    double control_rate_ = 50.0;
    int robot_id_ = 1;
    double default_height_ = 0.25;

    Eigen::MatrixXd default_stance_;
    std::unique_ptr<quadropted::InverseKinematics> ik_;
    std::unique_ptr<quadropted::TrotGaitController> trot_gait_;
    std::unique_ptr<quadropted::RestController> rest_controller_;

    quadropted::State state_;
    quadropted::Command command_;

    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr joint_pub_;
    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotVelocity>::SharedPtr velocity_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotModeCommand>::SharedPtr mode_sub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<RobotControllerNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
