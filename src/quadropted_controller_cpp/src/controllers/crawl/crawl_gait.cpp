#include "quadropted_controller_cpp/controllers/crawl/crawl_gait.hpp"

namespace quadropted {

CrawlGaitController::CrawlGaitController(double stance_time, double swing_time, double time_step,
                                         Eigen::MatrixXd default_stance)
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

LegsMatrix CrawlGaitController::step(int ticks, const LegsMatrix& current, const Eigen::Vector3d& cmd_vel,
                                     double robot_height) {
    LegsMatrix new_foot_locations{};

    Eigen::VectorXi contact_modes = contacts(ticks);
    int phase_idx = phase_index(ticks);
    double swing_prop = static_cast<double>(subphase_ticks(ticks)) / static_cast<double>(swing_ticks());
    bool move_sideways = (phase_idx == 0 || phase_idx == 4);
    bool move_left = (phase_idx == 0);

    for (int leg_index = 0; leg_index < 4; ++leg_index) {
        int contact_mode = contact_modes(leg_index);
        if (contact_mode == 1) {
            new_foot_locations.col(leg_index) =
                stance_.next_foot_location(leg_index, current, cmd_vel, robot_height, first_cycle_, move_sideways, move_left);
        } else {
            bool shifted_left = (contact_modes(0) == 0 || contact_modes(2) == 0);
            new_foot_locations.col(leg_index) =
                swing_.next_foot_location(swing_prop, leg_index, current, cmd_vel, robot_height, shifted_left);
        }
    }

    // Сброс first_cycle_ после первого полного цикла
    if (ticks >= phase_length()) {
        first_cycle_ = false;
    }

    return new_foot_locations;
}

}  // namespace quadropted
