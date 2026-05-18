#pragma once
#include <Eigen/Dense>
#include <vector>

#include "quadropted_controller_cpp/states/state_command.hpp"

namespace quadropted {

class GaitController {
  public:
    GaitController(double stance_time, double swing_time, double time_step, Eigen::MatrixXi contact_phases,
                   FootMatrix default_stance);

    virtual FootMatrix step(int ticks, const FootMatrix& current, const Eigen::Vector3d& cmd_vel,
                            double robot_height) const;

    const FootMatrix& default_stance() const { return default_stance_; }

    int swing_ticks() const { return swing_ticks_; }
    int stance_ticks() const { return stance_ticks_; }
    int phase_length() const { return phase_length_; }

    int phase_index(int ticks) const;
    Eigen::VectorXi contacts(int ticks) const;
    int subphase_ticks(int ticks) const;
    static int mod(int a, int b);
    const std::vector<int>& phase_ticks() const { return phase_ticks_; }

  protected:
    double stance_time_, swing_time_, time_step_;
    double inv_swing_ticks_ = 0.0;
    Eigen::MatrixXi contact_phases_;
    FootMatrix default_stance_{FootMatrix::Zero()};
    int stance_ticks_ = 0, swing_ticks_ = 0, phase_length_ = 0;
    std::vector<int> phase_ticks_;
    void compute_phase_ticks();
};

}  // namespace quadropted
