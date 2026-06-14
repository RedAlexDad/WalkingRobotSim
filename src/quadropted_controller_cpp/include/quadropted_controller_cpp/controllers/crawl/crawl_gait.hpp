#pragma once
#include "quadropted_controller_cpp/controllers/crawl/crawl_stance.hpp"
#include "quadropted_controller_cpp/controllers/crawl/crawl_swing.hpp"
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"

namespace quadropted {

class CrawlGaitController : public GaitController {
  public:
    CrawlGaitController(double stance_time, double swing_time, double time_step, Eigen::MatrixXd default_stance,
                        double z_leg_lift = 0.14, double body_shift_y = 0.06,
                        double z_error_constant = 0.02);
    LegsMatrix step(int ticks, const LegsMatrix& current, const Eigen::Vector3d& cmd_vel, double robot_height);
    void reset();
    CrawlSwingController& swing() { return swing_; }
    CrawlStanceController& stance() { return stance_; }
    bool is_first_cycle() const { return first_cycle_; }

  private:
    CrawlSwingController swing_;
    CrawlStanceController stance_;
    bool first_cycle_ = true;
};

}  // namespace quadropted
