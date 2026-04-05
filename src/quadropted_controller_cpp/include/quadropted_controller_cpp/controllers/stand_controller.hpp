#pragma once
#include <Eigen/Dense>
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"

namespace quadropted {

class StandController {
public:
    explicit StandController(Eigen::MatrixXd default_stance);
    Eigen::MatrixXd run(State& state, Command& cmd) const;
    const Eigen::MatrixXd& default_stance() const { return default_stance_; }
private:
    Eigen::MatrixXd default_stance_;
    double body_velocity_scale_ = 0.01;
    double body_angular_scale_ = 0.005;
    double max_linear_velocity_ = 0.035;
    double max_angular_velocity_ = 0.1;
};

}
