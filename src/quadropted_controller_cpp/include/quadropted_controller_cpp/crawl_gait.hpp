#pragma once
#include <Eigen/Dense>
#include <cmath>
#include "quadropted_controller_cpp/gait_controller.hpp"

namespace quadropted {

class CrawlStanceController {
public:
    CrawlStanceController() = default;
    Eigen::Vector3d position_delta(const Eigen::Vector3d&) { return Eigen::Vector3d::Zero(); }
    Eigen::Vector3d next_foot_location(int, const Eigen::MatrixXd&, const Eigen::Vector3d&) {
        return Eigen::Vector3d::Zero();
    }
};

class CrawlSwingController {
public:
    CrawlSwingController(int, int, double ts, int, double z_lift, Eigen::MatrixXd stance, double body_shift_y)
        : time_step_(ts), z_leg_lift_(z_lift), body_shift_y_(body_shift_y), default_stance_(std::move(stance)) {}

    Eigen::Vector3d raibert_touchdown_location(int leg_index, const Eigen::Vector3d& cmd_vel, bool) {
        Eigen::Vector2d delta = cmd_vel.head<2>() * phase_length_ * time_step_;
        Eigen::Vector3d delta_pos{delta.x(), delta.y(), 0};
        double theta = stance_ticks_ * time_step_ * cmd_vel.z();
        Eigen::Matrix3d rot = Eigen::AngleAxisd(theta, Eigen::Vector3d::UnitZ()).toRotationMatrix();
        Eigen::Vector3d result = rot * default_stance_.col(leg_index) + delta_pos;
        return result;
    }

    double swing_height(double p) {
        return (p < 0.5) ? (p / 0.5) * z_leg_lift_ : z_leg_lift_ * (1.0 - (p - 0.5) / 0.5);
    }

    Eigen::Vector3d next_foot_location(double swing_prop, int leg_index,
                                        const Eigen::MatrixXd& current,
                                        const Eigen::Vector3d& cmd_vel, bool) {
        double swing_h = swing_height(swing_prop);
        Eigen::Vector3d touchdown = raibert_touchdown_location(leg_index, cmd_vel, false);
        Eigen::Vector3d foot_loc = current.col(leg_index);
        double time_left = time_step_ * swing_ticks_ * (1.0 - swing_prop);
        if (time_left < 1e-6) { Eigen::Vector3d r = touchdown; r.z() = swing_h; return r; }
        Eigen::Vector3d velocity = (touchdown - foot_loc) / time_left;
        velocity.head<2>().array() *= 1.0;
        Eigen::Vector3d result = foot_loc;
        result.head<2>().array() *= 1.0;
        result += velocity * time_step_;
        result.z() = swing_h;
        return result;
    }

private:
    double time_step_, z_leg_lift_, body_shift_y_;
    Eigen::MatrixXd default_stance_;
    int stance_ticks_ = 27, swing_ticks_ = 22, phase_length_ = 200;
};

class CrawlGaitController : public GaitController {
public:
    CrawlGaitController(double stance_time, double swing_time, double time_step,
                        Eigen::MatrixXd default_stance)
        : GaitController(stance_time, swing_time, time_step,
                         (Eigen::MatrixXi(4, 8) << 0,0,0,1,1,1,1,0, 1,0,0,0,0,1,1,1,
                                                  1,1,0,0,0,0,1,1, 1,1,1,1,0,0,0,1).finished(),
                         default_stance),
          swing_(27, 22, time_step, 200, 0.05, default_stance, 0.02) {}

    Eigen::MatrixXd step(int ticks, const Eigen::MatrixXd& current,
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

private:
    CrawlSwingController swing_;
};

} // namespace quadropted
