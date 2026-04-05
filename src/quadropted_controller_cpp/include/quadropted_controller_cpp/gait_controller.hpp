#pragma once
#include <Eigen/Dense>
#include <vector>

namespace quadropted {

class GaitController {
public:
    GaitController(double stance_time, double swing_time, double time_step,
                   Eigen::MatrixXi contact_phases, Eigen::MatrixXd default_stance)
        : stance_time_(stance_time), swing_time_(swing_time), time_step_(time_step),
          contact_phases_(std::move(contact_phases)), default_stance_(std::move(default_stance)) {
        stance_ticks_ = static_cast<int>(stance_time_ / time_step_);
        swing_ticks_ = static_cast<int>(swing_time_ / time_step_);
        compute_phase_ticks();
    }

    const Eigen::MatrixXd& default_stance() const { return default_stance_; }
    int stance_ticks() const { return stance_ticks_; }
    int swing_ticks() const { return swing_ticks_; }
    int phase_length() const { return phase_length_; }

    const std::vector<int>& phase_ticks() const { return phase_ticks_; }

    int phase_index(int ticks) const {
        int phase_time = ticks % phase_length_;
        int phase_sum = 0;
        for (size_t i = 0; i < phase_ticks_.size(); ++i) {
            phase_sum += phase_ticks_[i];
            if (phase_time < phase_sum) return static_cast<int>(i);
        }
        return static_cast<int>(phase_ticks_.size() - 1);
    }

    int subphase_ticks(int ticks) const {
        int phase_time = ticks % phase_length_;
        int phase_sum = 0;
        for (size_t i = 0; i < phase_ticks_.size(); ++i) {
            phase_sum += phase_ticks_[i];
            if (phase_time < phase_sum) return phase_time - phase_sum + phase_ticks_[i];
        }
        return 0;
    }

    Eigen::VectorXi contacts(int ticks) const {
        return contact_phases_.col(phase_index(ticks));
    }

protected:
    double stance_time_, swing_time_, time_step_;
    Eigen::MatrixXi contact_phases_;
    Eigen::MatrixXd default_stance_;
    int stance_ticks_ = 0, swing_ticks_ = 0, phase_length_ = 0;
    std::vector<int> phase_ticks_;

private:
    void compute_phase_ticks() {
        phase_ticks_.clear();
        int cols = contact_phases_.cols();
        for (int j = 0; j < cols; ++j) {
            bool has_swing = false;
            for (int i = 0; i < contact_phases_.rows(); ++i)
                if (contact_phases_(i, j) == 0) has_swing = true;
            phase_ticks_.push_back(has_swing ? swing_ticks_ : stance_ticks_);
        }
        phase_length_ = 0;
        for (int v : phase_ticks_) phase_length_ += v;
    }
};

} // namespace quadropted
