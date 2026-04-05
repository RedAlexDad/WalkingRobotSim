#pragma once
#include <Eigen/Dense>
#include "quadropted_controller_cpp/trot_swing.hpp"
#include "quadropted_controller_cpp/gait_controller.hpp"
#include "quadropted_controller_cpp/pid_controller.hpp"

namespace quadropted {

class TrotGaitController : public GaitController {
public:
    TrotGaitController(double stance_time, double swing_time, double time_step,
                       bool use_imu, Eigen::MatrixXd default_stance)
        : GaitController(stance_time, swing_time, time_step,
                         (Eigen::MatrixXi(4, 4) << 1,1,1,0, 1,0,1,1, 1,0,1,1, 1,1,1,0).finished(),
                         default_stance),
          use_imu_(use_imu),
          swing_(2, 9, time_step, 22, 0.05, default_stance) {}

    Eigen::MatrixXd step(int ticks, const Eigen::MatrixXd& current,
                          const Eigen::Vector3d& cmd_vel) {
        Eigen::MatrixXd next = current;
        for (int leg = 0; leg < 4; ++leg) {
            int phase = phase_index(ticks);
            int sub = subphase_ticks(ticks);
            auto contacts_vec = contacts(ticks);

            if (contacts_vec(leg) == 1) {
                next.col(leg) = current.col(leg) + cmd_vel * time_step_;
            } else {
                double swing_prop = static_cast<double>(sub) / swing_ticks_;
                next.col(leg) = swing_.next_foot_location(swing_prop, leg, current, cmd_vel);
            }
        }
        return next;
    }

    bool use_imu() const { return use_imu_; }
    TrotSwingController& swing_controller() { return swing_; }

private:
    bool use_imu_;
    TrotSwingController swing_;
};

} // namespace quadropted
