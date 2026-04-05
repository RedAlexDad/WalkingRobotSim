#include "quadropted_controller_cpp/controllers/trot_gait.hpp"

namespace quadropted {

TrotGaitController::TrotGaitController(double stance_time, double swing_time,
                                         double time_step, bool use_imu,
                                         Eigen::MatrixXd default_stance)
    : GaitController(stance_time, swing_time, time_step,
                     (Eigen::MatrixXi(4, 4) <<
                       1, 1, 1, 0,
                       1, 0, 1, 1,
                       1, 0, 1, 1,
                       1, 1, 1, 0).finished(),
                     default_stance),
      use_imu_(use_imu),
      swing_(swing_ticks(), time_step, 0.14, default_stance) {}

Eigen::MatrixXd TrotGaitController::step(int ticks, const Eigen::MatrixXd& current,
                                          const Eigen::Vector3d& cmd_vel) const
{
    Eigen::MatrixXd new_foot_locations(3, 4);

    Eigen::VectorXi contact_modes = contacts(ticks);

    for (int leg_index = 0; leg_index < 4; ++leg_index) {
        int contact_mode = contact_modes(leg_index);
        if (contact_mode == 1) {
            // Stance — возвращаем текущую позицию ноги
            new_foot_locations.col(leg_index) = current.col(leg_index);
        } else {
            // Swing
            double swing_prop = static_cast<double>(subphase_ticks(ticks)) /
                                static_cast<double>(swing_ticks());
            // Создаём фейковый state для совместимости с API swing контроллера
            Eigen::MatrixXd state_foot = current;
            new_foot_locations.col(leg_index) =
                swing_.next_foot_location(swing_prop, leg_index, state_foot, cmd_vel);
        }
    }

    return new_foot_locations;
}

} // namespace quadropted
