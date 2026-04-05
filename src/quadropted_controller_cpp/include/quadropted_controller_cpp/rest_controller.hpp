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
    explicit RestController(Eigen::MatrixXd default_stance);

    Eigen::MatrixXd step(const StandState& state, const Command& cmd);

    const Eigen::MatrixXd& default_stance() const;
    PIDController& pid();

private:
    Eigen::MatrixXd default_stance_;
    PIDController pid_;
};

class StandController {
public:
    explicit StandController(Eigen::MatrixXd default_stance);

    const Eigen::MatrixXd& default_stance() const;

    Eigen::MatrixXd run(StandState& state, Command& cmd);

private:
    Eigen::MatrixXd default_stance_;
};

} // namespace quadropted
