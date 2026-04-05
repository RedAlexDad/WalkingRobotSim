#include "quadropted_controller_cpp/trot_swing.hpp"

namespace quadropted {

Eigen::Vector3d TrotStanceController::position_delta(const Eigen::Vector3d& cmd_vel) {
    return cmd_vel;
}

Eigen::Vector3d TrotStanceController::next_foot_location(int leg_index, const Eigen::MatrixXd& stance,
                                       const Eigen::Vector3d& cmd_vel) {
    Eigen::Vector3d loc = stance.col(leg_index);
    loc += cmd_vel;
    return loc;
}

} // namespace quadropted
