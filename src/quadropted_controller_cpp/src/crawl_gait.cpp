#include "quadropted_controller_cpp/crawl_gait.hpp"

namespace quadropted {

CrawlGaitController::CrawlGaitController(double stance_time, double swing_time, double time_step,
                        Eigen::MatrixXd default_stance)
    : GaitController(stance_time, swing_time, time_step,
                     (Eigen::MatrixXi(4, 8) << 0,0,0,1,1,1,1,0, 1,0,0,0,0,1,1,1,
                                              1,1,0,0,0,0,1,1, 1,1,1,1,0,0,0,1).finished(),
                     default_stance),
      swing_(27, 22, time_step, 200, 0.05, default_stance, 0.02) {}

Eigen::MatrixXd CrawlGaitController::step(int ticks, const Eigen::MatrixXd& current,
                          const Eigen::Vector3d& cmd_vel) {
    Eigen::MatrixXd next = current;
    for (int leg = 0; leg < 4; ++leg) {
        auto contacts_vec = contacts(ticks);
        int sub = subphase_ticks(ticks);
        if (contacts_vec(leg) == 1) {
            next.col(leg) = current.col(leg);
        } else {
            double swing_prop = static_cast<double>(sub) / 22;
            next.col(leg) = swing_.next_foot_location(swing_prop, leg, current, cmd_vel, false);
        }
    }
    return next;
}

} // namespace quadropted
