#pragma once
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"
#include "quadropted_controller_cpp/controllers/crawl_swing.hpp"

namespace quadropted {

class CrawlGaitController : public GaitController {
public:
    CrawlGaitController(double stance_time, double swing_time, double time_step, Eigen::MatrixXd default_stance);
    Eigen::MatrixXd step(int ticks, const Eigen::MatrixXd& current, const Eigen::Vector3d& cmd_vel) const;
private:
    CrawlSwingController swing_;
};

}
