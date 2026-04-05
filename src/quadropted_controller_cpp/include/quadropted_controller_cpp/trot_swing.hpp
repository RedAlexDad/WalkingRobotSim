#pragma once
#include <Eigen/Dense>
#include <cmath>
#include "quadropted_controller_cpp/rotation_matrices.hpp"

namespace quadropted {

class TrotStanceController {
public:
    TrotStanceController() = default;

    Eigen::Vector3d position_delta(const Eigen::Vector3d& cmd_vel);

    Eigen::Vector3d next_foot_location(int leg_index, const Eigen::MatrixXd& stance,
                                       const Eigen::Vector3d& cmd_vel);
};

class TrotSwingController {
public:
    TrotSwingController(int stance_ticks, int swing_ticks, double time_step,
                        int phase_length, double z_leg_lift, Eigen::MatrixXd default_stance);

    Eigen::Vector3d raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel);

    double swing_height(double swing_prop);

    Eigen::Vector3d next_foot_location(double swing_prop, int leg_index,
                                        const Eigen::MatrixXd& current,
                                        const Eigen::Vector3d& cmd_vel);

private:
    int swing_ticks_;
    double time_step_, z_leg_lift_;
    Eigen::MatrixXd default_stance_;
    int phase_length_ = 22;
};

} // namespace quadropted
