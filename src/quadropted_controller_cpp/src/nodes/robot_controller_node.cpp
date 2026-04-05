#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <quadropted_msgs/msg/robot_velocity.hpp>
#include <quadropted_msgs/msg/robot_mode_command.hpp>

#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/controllers/trot_gait.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/utils/math_utils.hpp"
#include <cmath>

namespace quadropted {

class RobotControllerNode : public rclcpp::Node {
public:
    RobotControllerNode() : Node("robot_controller_cpp"), rate_(60), state_(0.25) {
        declare_parameter("verbose", false);
        verbose_ = get_parameter("verbose").as_bool();

        // Геометрия робота
        double body[] = {0.3762, 0.0935};
        double legs[] = {0.0, 0.0955, 0.213, 0.213};

        // Default stance
        double dx = body[0] * 0.5 + 0.02;
        double dy = body[1] * 0.5 + legs[1];
        default_stance_ <<  dx,  dx, -dx, -dx,
                           -dy,  dy, -dy,  dy,
                            0,   0,   0,   0;

        state_.foot_locations = default_stance_;
        state_.behavior_state = BehaviorState::REST;

        // Контроллеры
        trot_gait_ = std::make_unique<TrotGaitController>(0.04, 0.18, 0.02, true, default_stance_);
        rest_ctrl_ = std::make_unique<RestController>(default_stance_);
        use_trot_ = false;

        // Начинаем с REST → TROT
        command_.trot_event = true;
        command_.rest_event = true;
        change_controller();

        // IK
        ik_ = std::make_unique<InverseKinematics>(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);

        // Publishers
        joint_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
            "joint_group_controller/commands", 10);

        // Subscriptions
        velocity_sub_ = create_subscription<quadropted_msgs::msg::RobotVelocity>(
            "robot_velocity", 10,
            [this](const quadropted_msgs::msg::RobotVelocity::SharedPtr msg) {
                if (msg->robot_id == 1) {
                    command_.velocity = {msg->cmd_vel.linear.x, msg->cmd_vel.linear.y, msg->cmd_vel.linear.z};
                    command_.yaw_rate = {msg->cmd_vel.angular.x, msg->cmd_vel.angular.y, msg->cmd_vel.angular.z};
                    if (verbose_)
                        RCLCPP_INFO(get_logger(), "Velocity: vx=%.3f vy=%.3f yaw=%.3f",
                                   command_.velocity[0], command_.velocity[1], command_.yaw_rate[2]);
                }
            });

        mode_sub_ = create_subscription<quadropted_msgs::msg::RobotModeCommand>(
            "robot_mode", 10,
            [this](const quadropted_msgs::msg::RobotModeCommand::SharedPtr msg) {
                if (msg->robot_id == 1) {
                    if (msg->mode == "REST") {
                        command_.rest_event = true; command_.trot_event = false;
                        command_.crawl_event = false; command_.stand_event = false;
                    } else if (msg->mode == "TROT") {
                        command_.rest_event = false; command_.trot_event = true;
                        command_.crawl_event = false; command_.stand_event = false;
                    } else if (msg->mode == "CRAWL") {
                        command_.rest_event = false; command_.trot_event = false;
                        command_.crawl_event = true; command_.stand_event = false;
                    } else if (msg->mode == "STAND") {
                        command_.rest_event = false; command_.trot_event = false;
                        command_.crawl_event = false; command_.stand_event = true;
                    }
                    change_controller();
                    controller_change_needed_ = true;
                }
            });

        // Control loop timer
        timer_ = create_wall_timer(
            std::chrono::milliseconds(1000 / rate_),
            std::bind(&RobotControllerNode::control_loop, this));

        RCLCPP_INFO(get_logger(), "Robot Controller Node (C++) started at %d Hz", rate_);
    }

private:
    void change_controller() {
        if (command_.trot_event && command_.rest_event) {
            state_.behavior_state = BehaviorState::REST;
            rest_ctrl_->pid().reset(this->now().seconds());
            command_.rest_event = false;

            state_.behavior_state = BehaviorState::TROT;
            use_trot_ = true;
            trot_gait_->pid_controller().reset(this->now().seconds());
            state_.ticks = 0;
            command_.trot_event = false;
            RCLCPP_INFO(get_logger(), "Switched to TROT controller");
        } else if (command_.trot_event) {
            if (state_.behavior_state == BehaviorState::REST) {
                state_.behavior_state = BehaviorState::TROT;
                use_trot_ = true;
                trot_gait_->pid_controller().reset(this->now().seconds());
                state_.ticks = 0;
            }
            command_.trot_event = false;
            RCLCPP_INFO(get_logger(), "Switched to TROT controller");
        } else if (command_.rest_event) {
            state_.behavior_state = BehaviorState::REST;
            use_trot_ = false;
            rest_ctrl_->pid().reset(this->now().seconds());
            command_.rest_event = false;
            RCLCPP_INFO(get_logger(), "Switched to REST controller");
        } else if (command_.stand_event) {
            if (state_.behavior_state != BehaviorState::STAND) {
                state_.behavior_state = BehaviorState::STAND;
                use_trot_ = false;
                state_.body_local_position[2] = 0.005;
            }
            command_.stand_event = false;
        } else if (command_.crawl_event) {
            state_.behavior_state = BehaviorState::CRAWL;
            use_trot_ = false;
            state_.ticks = 0;
            command_.crawl_event = false;
        }
    }

    Eigen::Matrix3d step_trot(State& state, const Command& cmd) {
        // Auto-rest: если нет движения — стоим
        bool needs_trot = true;
        if (std::abs(cmd.velocity[0]) < 1e-9 && std::abs(cmd.velocity[1]) < 1e-9 &&
            std::abs(cmd.yaw_rate[2]) < 1e-9) {
            if (state.ticks % (2 * trot_gait_->phase_length()) == 0)
                needs_trot = false;
        }

        if (!needs_trot) {
            Eigen::MatrixXd result = default_stance_;
            result.row(2).setConstant(cmd.robot_height);
            return result;
        }

        Eigen::VectorXi contacts = trot_gait_->contacts(state.ticks);
        Eigen::MatrixXd new_foot_locations = Eigen::Matrix3d::Zero();

        for (int leg = 0; leg < 4; ++leg) {
            if (contacts(leg) == 1) {
                // Stance phase
                Eigen::Vector3d foot_loc = state.foot_locations.col(leg);
                double z = foot_loc.z();

                double step_dist_x = cmd.velocity[0] * (double)trot_gait_->phase_length() / trot_gait_->swing_ticks();
                double step_dist_y = cmd.velocity[1] * (double)trot_gait_->phase_length() / trot_gait_->swing_ticks();

                Eigen::Vector3d velocity;
                velocity.x() = -(step_dist_x / 4.0) / (trot_gait_->time_step() * trot_gait_->stance_ticks());
                velocity.y() = -(step_dist_y / 4.0) / (trot_gait_->time_step() * trot_gait_->stance_ticks());
                velocity.z() = (cmd.robot_height - z) / 0.02;

                Eigen::Vector3d delta_pos = velocity * trot_gait_->time_step();
                Eigen::Matrix3d delta_ori = rotxyz(
                    -cmd.yaw_rate[0] * trot_gait_->time_step(),
                    -cmd.yaw_rate[1] * trot_gait_->time_step(),
                    -cmd.yaw_rate[2] * trot_gait_->time_step());

                new_foot_locations.col(leg) = delta_ori * foot_loc + delta_pos;
            } else {
                // Swing phase
                int sub_ticks = trot_gait_->subphase_ticks(state.ticks);
                double swing_prop = static_cast<double>(sub_ticks) / trot_gait_->swing_ticks();

                new_foot_locations.col(leg) = trot_gait_->swing_controller().next_foot_location(
                    swing_prop, leg, state.foot_locations,
                    Eigen::Vector3d{cmd.velocity[0], cmd.velocity[1], cmd.yaw_rate[2]});
            }
        }

        // IMU compensation
        if (trot_gait_->use_imu()) {
            auto comp = trot_gait_->pid_controller().run(state.imu_roll, state.imu_pitch, this->now().seconds());
            Eigen::Matrix3d rot = rotxyz(-comp[0], -comp[1], 0);
            new_foot_locations = rot * new_foot_locations;
        }

        state.ticks++;
        return new_foot_locations;
    }

    Eigen::Matrix3d step_rest(State& state, const Command& cmd) {
        (void)state;
        Eigen::MatrixXd result = default_stance_;
        result.row(2).setConstant(cmd.robot_height);
        return result;
    }

    void control_loop() {
        // Run controller
        Eigen::MatrixXd leg_positions;
        if (use_trot_) {
            leg_positions = step_trot(state_, command_);
        } else {
            leg_positions = step_rest(state_, command_);
        }

        state_.foot_locations = leg_positions;
        state_.robot_height = command_.robot_height;

        if (controller_change_needed_) {
            change_controller();
            controller_change_needed_ = false;
        }

        // IK
        try {
            auto joint_angles = ik_->inverse_kinematics(
                leg_positions,
                state_.body_local_position[0], state_.body_local_position[1], state_.body_local_position[2],
                state_.body_local_orientation[0], state_.body_local_orientation[1], state_.body_local_orientation[2]);

            auto msg = std::make_unique<std_msgs::msg::Float64MultiArray>();
            msg->data.assign(joint_angles.begin(), joint_angles.end());
            joint_pub_->publish(std::move(msg));
        } catch (const std::exception& e) {
            RCLCPP_ERROR(get_logger(), "IK error: %s", e.what());
        }
    }

    // Members
    int rate_;
    bool verbose_;
    bool controller_change_needed_ = false;
    bool use_trot_ = false;

    Eigen::MatrixXd default_stance_;
    State state_;
    Command command_;

    std::unique_ptr<TrotGaitController> trot_gait_;
    std::unique_ptr<RestController> rest_ctrl_;
    std::unique_ptr<InverseKinematics> ik_;

    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr joint_pub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotVelocity>::SharedPtr velocity_sub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotModeCommand>::SharedPtr mode_sub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

} // namespace quadropted

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<quadropted::RobotControllerNode>());
    rclcpp::shutdown();
    return 0;
}
