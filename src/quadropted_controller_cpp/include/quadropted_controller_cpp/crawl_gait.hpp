#pragma once
#include <Eigen/Dense>
#include <cmath>
#include "quadropted_controller_cpp/gait_controller.hpp"

namespace quadropted {

class CrawlStanceController {
public:
    CrawlStanceController() = default;
    Eigen::Vector3d position_delta(const Eigen::Vector3d&);
    Eigen::Vector3d next_foot_location(int, const Eigen::MatrixXd&, const Eigen::Vector3d&);
};

class CrawlSwingController {
public:
    CrawlSwingController(int, int, double ts, int, double z_lift, Eigen::MatrixXd stance, double body_shift_y);

    Eigen::Vector3d raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel, bool);

    double swing_height(double p);

    Eigen::Vector3d next_foot_location(double swing_prop, int leg_index,
                                        const Eigen::MatrixXd& current,
                                        const Eigen::Vector3d& cmd_vel, bool);

private:
    double time_step_, z_leg_lift_, body_shift_y_;
    Eigen::MatrixXd default_stance_;
    int stance_ticks_ = 27, swing_ticks_ = 22, phase_length_ = 200;
};

class CrawlGaitController : public GaitController {
public:
    CrawlGaitController(double stance_time, double swing_time, double time_step,
                        Eigen::MatrixXd default_stance);

    Eigen::MatrixXd step(int ticks, const Eigen::MatrixXd& current,
                          const Eigen::Vector3d& cmd_vel);

private:
    CrawlSwingController swing_;
};

} // namespace quadropted
