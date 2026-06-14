#include "quadropted_controller_cpp/nodes/robot_controller_node.hpp"

#include <algorithm>
#include <cmath>
#include <memory>
#include <string>

namespace quadropted {

RobotControllerNode::RobotControllerNode() : Node("robot_controller_cpp"), rate_(60), state_(0.25) {
    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};

    double dx_front = body[0] * 0.5 + 0.02;
    double dx_back = body[0] * 0.5 + 0.0;
    double dy = body[1] * 0.5 + legs[1];
    default_stance_ << dx_front, dx_front, -dx_back, -dx_back, -dy, dy, -dy, dy, 0, 0, 0, 0;

    state_.foot_locations = default_stance_;
    state_.behavior_state = BehaviorState::REST;

    trot_gait_ = std::make_unique<TrotGaitController>(0.04, 0.18, 0.02, false, default_stance_);
    crawl_gait_ = std::make_unique<CrawlGaitController>(0.55, 0.45, 0.02, default_stance_);
    rest_ctrl_ = std::make_unique<RestController>(default_stance_);
    stand_ctrl_ = std::make_unique<StandController>(default_stance_);

    command_.trot_event = true;
    command_.rest_event = true;
    change_controller();

    ik_ = std::make_unique<InverseKinematics>(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);

    joint_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>("joint_group_controller/commands", 10);
    foot_contact_pub_ =
        create_publisher<quadropted_msgs::msg::RobotFootContact>("foot_contact", rclcpp::SensorDataQoS());

    velocity_sub_ = create_subscription<quadropted_msgs::msg::RobotVelocity>(
        "robot_velocity", 10, [this](const quadropted_msgs::msg::RobotVelocity::SharedPtr msg) {
            if (msg->robot_id == 1) {
                command_.velocity = {msg->cmd_vel.linear.x, msg->cmd_vel.linear.y, msg->cmd_vel.linear.z};
                command_.yaw_rate = {msg->cmd_vel.angular.x, msg->cmd_vel.angular.y, msg->cmd_vel.angular.z};

                if (state_.behavior_state == BehaviorState::STAND) {
                    RCLCPP_INFO(get_logger(), "[STAND VELOCITY] vx=%.4f vy=%.4f vz=%.4f | ax=%.4f ay=%.4f az=%.4f",
                                command_.velocity[0], command_.velocity[1], command_.velocity[2], command_.yaw_rate[0],
                                command_.yaw_rate[1], command_.yaw_rate[2]);
                }

                if (state_.behavior_state == BehaviorState::CRAWL) {
                    constexpr double crawl_max_vx = 0.011;
                    constexpr double crawl_max_yaw = 0.15;
                    command_.velocity[0] = std::clamp(command_.velocity[0], -crawl_max_vx, crawl_max_vx);
                    command_.velocity[1] = std::clamp(command_.velocity[1], -crawl_max_vx * 0.5, crawl_max_vx * 0.5);
                    command_.yaw_rate[2] = std::clamp(command_.yaw_rate[2], -crawl_max_yaw, crawl_max_yaw);
                }
            }
        });

    imu_sub_ =
        create_subscription<sensor_msgs::msg::Imu>("imu", 10, [this](const sensor_msgs::msg::Imu::SharedPtr msg) {
            double w = msg->orientation.w;
            double x = msg->orientation.x;
            double y = msg->orientation.y;
            double z = msg->orientation.z;
            state_.imu_roll = std::atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y));
            state_.imu_pitch = std::asin(2.0 * (w * y - z * x));
        });

    mode_sub_ = create_subscription<quadropted_msgs::msg::RobotModeCommand>(
        "robot_mode", 10, [this](const quadropted_msgs::msg::RobotModeCommand::SharedPtr msg) {
            if (msg->robot_id == 1) {
                if (msg->mode == "REST") {
                    command_.rest_event = true;
                    command_.trot_event = false;
                    command_.crawl_event = false;
                    command_.stand_event = false;
                } else if (msg->mode == "TROT") {
                    command_.rest_event = false;
                    command_.trot_event = true;
                    command_.crawl_event = false;
                    command_.stand_event = false;
                } else if (msg->mode == "CRAWL") {
                    command_.rest_event = false;
                    command_.trot_event = false;
                    command_.crawl_event = true;
                    command_.stand_event = false;
                } else if (msg->mode == "STAND") {
                    command_.rest_event = false;
                    command_.trot_event = false;
                    command_.crawl_event = false;
                    command_.stand_event = true;
                }
                change_controller();
            }
        });

    timer_ = create_wall_timer(std::chrono::microseconds(static_cast<long long>(1000000.0 / rate_)),
                               std::bind(&RobotControllerNode::control_loop, this));

    RCLCPP_INFO(get_logger(), "Robot Controller Node (C++) started at %d Hz", rate_);
    RCLCPP_INFO(get_logger(), "Startup grace period: 2 seconds (waiting for robot to land)");

    behavior_srv_ = create_service<quadropted_msgs::srv::RobotBehaviorCommand>(
        "robot_behavior_command",
        [this](const std::shared_ptr<quadropted_msgs::srv::RobotBehaviorCommand::Request> request,
               std::shared_ptr<quadropted_msgs::srv::RobotBehaviorCommand::Response> response) {
            std::string cmd = request->command;
            std::transform(cmd.begin(), cmd.end(), cmd.begin(), ::tolower);
            RCLCPP_INFO(get_logger(), "Received behavior command: %s", cmd.c_str());

            if (cmd == "sit") {
                command_.stand_event = true;
                command_.rest_event = false;
                command_.trot_event = false;
                command_.crawl_event = false;
                change_controller();
                state_.body_local_position[2] = -0.15;
                response->success = true;
                response->message = "Robot sat down.";
            } else if (cmd == "up") {
                command_.rest_event = true;
                command_.stand_event = false;
                command_.trot_event = false;
                command_.crawl_event = false;
                change_controller();
                state_.body_local_position[2] = 0.0;
                response->success = true;
                response->message = "Robot stood up.";
            } else if (cmd == "walk") {
                command_.rest_event = true;
                command_.trot_event = true;
                command_.stand_event = false;
                command_.crawl_event = false;
                change_controller();
                state_.body_local_position[2] = 0.0;
                response->success = true;
                response->message = "Robot started walking.";
            } else {
                response->success = false;
                response->message = "Unknown command: " + request->command;
            }
        });
}

void RobotControllerNode::change_controller() {
    if (command_.trot_event && command_.rest_event) {
        state_.behavior_state = BehaviorState::REST;
        rest_ctrl_->pid().reset(this->now().seconds());
        command_.rest_event = false;

        state_.behavior_state = BehaviorState::TROT;
        trot_gait_->pid_controller().reset(this->now().seconds());
        state_.ticks = 0;
        state_.body_local_position[2] = 0.0;
        command_.trot_event = false;
        RCLCPP_INFO(get_logger(), "Switched to TROT controller");
    } else if (command_.trot_event) {
        auto prev = state_.behavior_state;
        state_.behavior_state = BehaviorState::TROT;
        trot_gait_->pid_controller().reset(this->now().seconds());
        state_.ticks = 0;
        state_.body_local_position[2] = 0.0;
        command_.trot_event = false;
        if (prev == BehaviorState::CRAWL) {
            RCLCPP_INFO(get_logger(), "Switched to TROT controller (from CRAWL)");
        } else if (prev == BehaviorState::STAND) {
            RCLCPP_INFO(get_logger(), "Switched to TROT controller (from STAND)");
        }
    } else if (command_.rest_event) {
        state_.behavior_state = BehaviorState::REST;
        rest_ctrl_->pid().reset(this->now().seconds());
        state_.body_local_position[2] = -0.15;
        command_.rest_event = false;
        RCLCPP_INFO(get_logger(), "Switched to REST controller — lying down");
    } else if (command_.stand_event) {
        if (state_.behavior_state != BehaviorState::STAND) {
            state_.behavior_state = BehaviorState::STAND;
            state_.body_local_position[2] = 0.005;
            RCLCPP_INFO(get_logger(), "Switched to STAND controller");
        }
        command_.stand_event = false;
    } else if (command_.crawl_event) {
        state_.behavior_state = BehaviorState::CRAWL;
        crawl_gait_->reset();
        state_.ticks = 0;
        state_.body_local_position[2] = 0.0;
        command_.crawl_event = false;
    }
}

void RobotControllerNode::publish_foot_contacts() {
    auto msg = std::make_unique<quadropted_msgs::msg::RobotFootContact>();
    switch (state_.behavior_state) {
        case BehaviorState::REST:
        case BehaviorState::STAND:
            msg->contacts = {true, true, true, true};
            break;
        case BehaviorState::TROT: {
            Eigen::VectorXi contacts = trot_gait_->contacts(state_.ticks);
            msg->contacts = {contacts(0) != 0, contacts(1) != 0, contacts(2) != 0, contacts(3) != 0};
            break;
        }
        case BehaviorState::CRAWL: {
            Eigen::VectorXi contacts = crawl_gait_->contacts(state_.ticks);
            msg->contacts = {contacts(0) != 0, contacts(1) != 0, contacts(2) != 0, contacts(3) != 0};
            break;
        }
    }
    foot_contact_pub_->publish(std::move(msg));
}

void RobotControllerNode::control_loop() {
    if (startup_grace_ > 0) {
        startup_grace_--;
        if (startup_grace_ == 0) {
            RCLCPP_INFO(get_logger(), "Startup grace period complete, controller active");
        }
        return;
    }

    rclcpp::Time now = this->now();
    LegsMatrix leg_positions;
    switch (state_.behavior_state) {
        case BehaviorState::TROT:
            leg_positions = step_trot(state_, command_, now.seconds());
            break;
        case BehaviorState::CRAWL:
            leg_positions = step_crawl(state_, command_);
            break;
        case BehaviorState::STAND:
            leg_positions = step_stand(state_, command_);
            break;
        case BehaviorState::REST:
        default:
            leg_positions = step_rest(state_, command_);
            break;
    }

    state_.foot_locations = leg_positions;
    state_.robot_height = command_.robot_height;

    publish_foot_contacts();

    if (state_.ticks < 5) {
        RCLCPP_INFO(get_logger(), "[IK DEBUG] leg_positions: %dx%d, dx=%.3f dy=%.3f dz=%.3f", (int)leg_positions.rows(),
                    (int)leg_positions.cols(), state_.body_local_position[0], state_.body_local_position[1],
                    state_.robot_height);
    }

    try {
        auto joint_angles = ik_->inverse_kinematics(
            leg_positions, state_.body_local_position[0], state_.body_local_position[1], state_.body_local_position[2],
            state_.body_local_orientation[0], state_.body_local_orientation[1], state_.body_local_orientation[2]);

        auto msg = std::make_unique<std_msgs::msg::Float64MultiArray>();
        msg->data.assign(joint_angles.begin(), joint_angles.end());
        joint_pub_->publish(std::move(msg));

        if (state_.ticks % 60 == 0) {
            RCLCPP_INFO(get_logger(),
                        "[DEBUG] cmd: vx=%.4f vy=%.4f vz=%.4f yaw=%.4f | "
                        "pos: x=%.4f y=%.4f z=%.4f | "
                        "joints[0-2]: %.4f %.4f %.4f",
                        command_.velocity[0], command_.velocity[1], command_.velocity[2], command_.yaw_rate[2],
                        state_.body_local_position[0], state_.body_local_position[1], state_.body_local_position[2],
                        joint_angles[0], joint_angles[1], joint_angles[2]);
        }
    } catch (const std::exception& e) {
        RCLCPP_ERROR(get_logger(), "IK error: %s", e.what());
    }
}

}  // namespace quadropted

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<quadropted::RobotControllerNode>());
    rclcpp::shutdown();
    return 0;
}
