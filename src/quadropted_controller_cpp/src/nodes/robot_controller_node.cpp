#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <quadropted_msgs/msg/robot_velocity.hpp>
#include <quadropted_msgs/msg/robot_mode_command.hpp>

#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/controllers/trot_gait.hpp"
#include "quadropted_controller_cpp/controllers/crawl_gait.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/utils/math_utils.hpp"
#include <cmath>

namespace quadropted {

class RobotControllerNode : public rclcpp::Node {
public:
    RobotControllerNode() : Node("robot_controller_cpp"), rate_(60), state_(0.25) {
        declare_parameter("verbose", false);
        // debug_mode removed
        verbose_ = get_parameter("verbose").as_bool();
        // debug_mode removed

        // Геометрия робота
        double body[] = {0.3762, 0.0935};
        double legs[] = {0.0, 0.0955, 0.213, 0.213};

        // Default stance
        double dx = body[0] * 0.5 + 0.02;
        double dy = body[1] * 0.5 + legs[1];
        default_stance_.resize(3, 4);
        default_stance_ <<  dx,  dx, -dx, -dx,
                           -dy,  dy, -dy,  dy,
                            0,   0,   0,   0;

        state_.foot_locations = default_stance_;
        state_.behavior_state = BehaviorState::REST;

        // Контроллеры
        // FIX: вернуть оригинальные timing как в Python RobotController.py
        // stance_time=0.04, swing_time=0.18 → stance_ticks=2, swing_ticks=9
        trot_gait_ = std::make_unique<TrotGaitController>(0.04, 0.18, 0.02, false, default_stance_);
        crawl_gait_ = std::make_unique<CrawlGaitController>(0.55, 0.45, 0.02, default_stance_);
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
                    if (false)
                        RCLCPP_DEBUG(get_logger(), "[DEBUG] Velocity: vx=%.4f vy=%.4f vz=%.4f yaw=%.4f",
                                   command_.velocity[0], command_.velocity[1], command_.velocity[2], command_.yaw_rate[2]);
                }
            });

        // IMU subscription — обновляем roll/pitch для компенсации
        imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
            "imu", 10,
            [this](const sensor_msgs::msg::Imu::SharedPtr msg) {
                // Конвертируем quaternion в euler angles
                double w = msg->orientation.w;
                double x = msg->orientation.x;
                double y = msg->orientation.y;
                double z = msg->orientation.z;
                state_.imu_roll = std::atan2(2.0*(w*x + y*z), 1.0 - 2.0*(x*x + y*y));
                state_.imu_pitch = std::asin(2.0*(w*y - z*x));
                if (false)
                    RCLCPP_DEBUG(get_logger(), "[DEBUG] IMU: roll=%.4f pitch=%.4f", state_.imu_roll, state_.imu_pitch);
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
        RCLCPP_INFO(get_logger(), "Startup grace period: 2 seconds (waiting for robot to land)");
    }

private:
    void change_controller() {
        if (command_.trot_event && command_.rest_event) {
            state_.behavior_state = BehaviorState::REST;
            rest_ctrl_->pid().reset(this->now().seconds());
            command_.rest_event = false;

            state_.behavior_state = BehaviorState::TROT;
            use_crawl_ = false;
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
            use_crawl_ = false;
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
            use_crawl_ = true;
            use_trot_ = false;
            // crawl_gait_->reset_ticks();  // method not available
            state_.ticks = 0;
            command_.crawl_event = false;
        }
    }

    Eigen::MatrixXd step_trot(State& state, const Command& cmd) {
        state.ticks++;  // Инкрементируем каждый тик
        // При нулевой скорости — стабильная стойка
        bool has_command = std::abs(cmd.velocity[0]) > 1e-4 ||
                           std::abs(cmd.velocity[1]) > 1e-4 ||
                           std::abs(cmd.yaw_rate[2]) > 1e-4;
        if (!has_command) {
            Eigen::MatrixXd result = default_stance_;
            result.row(2).setConstant(cmd.robot_height);
            return result;
        }

        Eigen::VectorXi contacts = trot_gait_->contacts(state.ticks);
        Eigen::MatrixXd new_foot_locations = Eigen::MatrixXd::Zero(3, 4);

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
                velocity.z() = (cmd.robot_height - z) / trot_gait_->time_step();
                // Ограничиваем Z velocity чтобы не было резких скачков
                if (velocity.z() > 2.0) velocity.z() = 2.0;
                if (velocity.z() < -2.0) velocity.z() = -2.0;

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
            if (false)
                RCLCPP_DEBUG(get_logger(), "[DEBUG] IMU comp: roll=%.3f pitch=%.3f comp_x=%.3f comp_y=%.3f",
                           state.imu_roll, state.imu_pitch, -comp[0], -comp[1]);
        }


        // DEBUG: каждые 60 тиков
        if (state.ticks % 60 == 0) {
            RCLCPP_INFO(get_logger(), "[DEBUG] TROT step: ticks=%d contacts=[%d,%d,%d,%d]",
                       state.ticks, contacts(0), contacts(1), contacts(2), contacts(3));
        }

        return new_foot_locations;
    }

    Eigen::MatrixXd step_crawl(State& state, const Command& cmd) {
        state.ticks++;
        // При нулевой скорости — стабильная стойка
        bool has_command = std::abs(cmd.velocity[0]) > 1e-4 ||
                           std::abs(cmd.velocity[1]) > 1e-4 ||
                           std::abs(cmd.yaw_rate[2]) > 1e-4;
        if (!has_command) {
            Eigen::MatrixXd result = default_stance_;
            result.row(2).setConstant(cmd.robot_height);
            return result;
        }

        Eigen::VectorXi contacts = crawl_gait_->contacts(state.ticks);
        Eigen::MatrixXd new_foot_locations = Eigen::MatrixXd::Zero(3, 4);

        for (int leg = 0; leg < 4; ++leg) {
            if (contacts(leg) == 1) {
                Eigen::Vector3d foot_loc = state.foot_locations.col(leg);
                double step_dist_x = cmd.velocity[0] * (double)crawl_gait_->phase_length() / crawl_gait_->swing_ticks();
                double step_dist_y = cmd.velocity[1] * (double)crawl_gait_->phase_length() / crawl_gait_->swing_ticks();
                Eigen::Vector3d delta;
                delta.x() = -(step_dist_x / 4.0) / (0.02 * crawl_gait_->stance_ticks()) * 0.02;
                delta.y() = -(step_dist_y / 4.0) / (0.02 * crawl_gait_->stance_ticks()) * 0.02;
                delta.z() = 0.0;
                new_foot_locations.col(leg) = foot_loc + delta;
            } else {
                int sub_ticks = crawl_gait_->subphase_ticks(state.ticks);
                double swing_prop = static_cast<double>(sub_ticks) / crawl_gait_->swing_ticks();
                new_foot_locations.col(leg) = trot_gait_->swing_controller().next_foot_location(
                    swing_prop, leg, state.foot_locations,
                    Eigen::Vector3d{cmd.velocity[0], cmd.velocity[1], cmd.yaw_rate[2]});
            }
        }

        // DEBUG
        if (state.ticks % 60 == 0) {
            RCLCPP_INFO(get_logger(), "[DEBUG] CRAWL step: ticks=%d contacts=[%d,%d,%d,%d]",
                       state.ticks, contacts(0), contacts(1), contacts(2), contacts(3));
        }

        return new_foot_locations;
    }

    Eigen::MatrixXd step_rest(State& state, const Command& cmd) {
        state.ticks++;  // Инкрементируем ticks как в trot
        Eigen::MatrixXd result = default_stance_;
        result.row(2).setConstant(cmd.robot_height);
        // DEBUG: каждые 60 тиков
        if (state.ticks % 60 == 0) {
            RCLCPP_INFO(get_logger(), "[DEBUG] REST: Z=%.3f, ticks=%d", cmd.robot_height, state.ticks);
        }
        return result;
    }

    void control_loop() {
        // Grace period при старте — ждём пока робот приземлится
        if (startup_grace_ > 0) {
            startup_grace_--;
            if (startup_grace_ == 0) {
                RCLCPP_INFO(get_logger(), "Startup grace period complete, controller active");
            }
            return;
        }

        // Run controller
        Eigen::MatrixXd leg_positions;
        if (use_trot_) {
            leg_positions = step_trot(state_, command_);
        } else if (use_crawl_) {
            leg_positions = step_crawl(state_, command_);
        } else {
            leg_positions = step_rest(state_, command_);
        }

        state_.foot_locations = leg_positions;
        state_.robot_height = command_.robot_height;

        if (controller_change_needed_) {
            change_controller();
            controller_change_needed_ = false;
        }

        // IK debug — проверяем размеры
        if (state_.ticks < 5) {
            RCLCPP_INFO(get_logger(), "[IK DEBUG] leg_positions: %dx%d, dx=%.3f dy=%.3f dz=%.3f",
                       (int)leg_positions.rows(), (int)leg_positions.cols(),
                       state_.body_local_position[0], state_.body_local_position[1], state_.robot_height);
        }

        try {
            auto joint_angles = ik_->inverse_kinematics(
                leg_positions,
                state_.body_local_position[0], state_.body_local_position[1], state_.body_local_position[2],
                state_.body_local_orientation[0], state_.body_local_orientation[1], state_.body_local_orientation[2]);

            auto msg = std::make_unique<std_msgs::msg::Float64MultiArray>();
            msg->data.assign(joint_angles.begin(), joint_angles.end());
            joint_pub_->publish(std::move(msg));

            // DEBUG: выводим каждые 60 тиков (раз в секунду)
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

    // Members
    int rate_;
    bool verbose_;
    bool debug_mode_ = false; // removed
    bool controller_change_needed_ = false;
    bool use_trot_ = false;
    bool use_crawl_ = false;
    int startup_grace_ = 120;  // 2 секунды задержки при старте

    Eigen::MatrixXd default_stance_;
    State state_;
    Command command_;

    std::unique_ptr<TrotGaitController> trot_gait_;
    std::unique_ptr<CrawlGaitController> crawl_gait_;
    std::unique_ptr<RestController> rest_ctrl_;
    std::unique_ptr<InverseKinematics> ik_;

    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr joint_pub_;
    rclcpp::Subscription<quadropted_msgs::msg::RobotVelocity>::SharedPtr velocity_sub_;
    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
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
