#pragma once
#include <Eigen/Dense>

#include "quadropted_controller_cpp/controllers/crawl_stance.hpp"
#include "quadropted_controller_cpp/controllers/crawl_swing.hpp"
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"

namespace quadropted {

class CrawlGaitController : public GaitController {
  public:
    CrawlGaitController(double stance_time, double swing_time, double time_step, FootMatrix default_stance);
    FootMatrix step(int ticks, const FootMatrix& current, const Eigen::Vector3d& cmd_vel,
                    double robot_height) const override;
    CrawlStanceController& stance() { return stance_; }
    CrawlSwingController& swing() { return swing_; }
    bool is_first_cycle() const { return first_cycle_; }
    void reset();

  private:
    CrawlStanceController stance_;
    CrawlSwingController swing_;
    mutable bool first_cycle_ = true;
};

}  // namespace quadropted
