#include "quadropted_controller_cpp/controllers/crawl_gait.hpp"

namespace quadropted {

CrawlGaitController::CrawlGaitController(double stance_time, double swing_time, double time_step,
                                         FootMatrix default_stance)
    : GaitController(stance_time, swing_time, time_step,
                     (Eigen::MatrixXi(4, 8) << 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1,
                      1, 1, 1, 1, 1, 0, 1, 1)
                         .finished(),
                     default_stance),
      swing_(swing_ticks(), time_step, 0.14, default_stance, phase_length(), stance_ticks(),
             0.06 /* body_shift_y как в Python */),
      stance_(phase_length(), stance_ticks(), swing_ticks(), time_step, 0.02 /* z_error_constant */,
              0.06 /* body_shift_y */) {}

void CrawlGaitController::reset() {
    first_cycle_ = true;
}

FootMatrix CrawlGaitController::step(int ticks, const FootMatrix& current, const Eigen::Vector3d& cmd_vel,
                                     double robot_height) const {
    FootMatrix new_foot_locations{FootMatrix::Zero()};

    Eigen::VectorXi contact_modes = contacts(ticks);
    int sub = subphase_ticks(ticks);
    double swing_prop = static_cast<double>(sub) * inv_swing_ticks_;

    for (int leg_index = 0; leg_index < 4; ++leg_index) {
        int contact_mode = contact_modes(leg_index);
        if (contact_mode == 1) {
            new_foot_locations.col(leg_index) = current.col(leg_index);
        } else {
            new_foot_locations.col(leg_index) =
                swing_.next_foot_location(swing_prop, leg_index, current, cmd_vel, robot_height);
        }
    }

    // Сброс first_cycle_ после первого полного цикла
    if (ticks >= phase_length()) {
        first_cycle_ = false;
    }

    return new_foot_locations;
}

}  // namespace quadropted
