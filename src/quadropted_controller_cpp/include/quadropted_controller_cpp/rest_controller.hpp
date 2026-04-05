#pragma once
#include <Eigen/Dense>
#include "quadropted_controller_cpp/rotation_matrices.hpp"
#include "quadropted_controller_cpp/pid_controller.hpp"

namespace quadropted {

struct StandState {
    std::array<double, 3> body_local_position{0, 0, 0};
    std::array<double, 3> body_local_orientation{0, 0, 0};
    double imu_roll = 0, imu_pitch = 0;
    int ticks = 0;
};

struct Command {
    double robot_height = 0.0;
    std::array<double, 3> velocity{0, 0, 0};
    std::array<double, 3> yaw_rate{0, 0, 0};
    bool trot_event = false, rest_event = false, crawl_event = false, stand_event = false;
};

class RestController {
public:
    explicit RestController(Eigen::MatrixXd default_stance)
        : default_stance_(std::move(default_stance)),
          pid_(0.15, 0.02, 0.002) {}

    Eigen::MatrixXd step(const StandState& state, const Command& cmd) {
        Eigen::MatrixXd result = default_stance_;
        result.row(2).setConstant(cmd.robot_height);
        return result;
    }

    const Eigen::MatrixXd& default_stance() const { return default_stance_; }
    PIDController& pid() { return pid_; }

private:
    Eigen::MatrixXd default_stance_;
    PIDController pid_;
};

class StandController {
public:
    explicit StandController(Eigen::MatrixXd default_stance)
        : default_stance_(std::move(default_stance)) {}

    const Eigen::MatrixXd& default_stance() const { return default_stance_; }

    Eigen::MatrixXd run(StandState& state, Command& cmd) {
        Eigen::MatrixXd result = default_stance_;
        result.row(2).setConstant(cmd.robot_height);
        return result;
    }

private:
    Eigen::MatrixXd default_stance_;
};

} // namespace quadropted
