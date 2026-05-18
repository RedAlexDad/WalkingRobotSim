#pragma once
#include <Eigen/Dense>
#include <algorithm>
#include <array>
#include <optional>
#include <vector>

namespace quadropted {

class RingBuffer {
  public:
    RingBuffer() = default;
    explicit RingBuffer(int capacity) : buf_(capacity) {}

    void push_back(double v) {
        if (buf_.empty()) buf_.resize(1);
        double old = buf_[head_];
        buf_[head_] = v;
        head_ = (head_ + 1) % buf_.size();
        sum_ += v - old;
        if (count_ < static_cast<int>(buf_.size())) count_++;
    }

    void pop_front() {
        if (count_ <= 0) return;
        double old = buf_[(head_ - count_ + buf_.size()) % buf_.size()];
        sum_ -= old;
        count_--;
    }

    double front() const {
        return buf_[(head_ - count_ + buf_.size()) % buf_.size()];
    }

    int size() const { return count_; }
    bool empty() const { return count_ == 0; }
    double sum() const { return sum_; }

    void clear() {
        head_ = 0;
        count_ = 0;
        sum_ = 0.0;
    }

    void reserve(int capacity) {
        if (static_cast<int>(buf_.size()) < capacity) {
            buf_.resize(capacity);
            head_ = 0;
            count_ = 0;
            sum_ = 0.0;
        }
    }

  private:
    std::vector<double> buf_;
    int head_ = 0;
    int count_ = 0;
    double sum_ = 0.0;
};

struct OdometryState {
    double x = 0.0, y = 0.0, theta = 0.0;
    double linear_velocity_x = 0.0, linear_velocity_y = 0.0, imu_angular_velocity = 0.0;

    int filter_window_size = 14;
    RingBuffer delta_x_queue, delta_y_queue;

    std::array<Eigen::Vector3d, 4> foot_positions{Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero(),
                                                  Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero()};
    std::array<std::optional<Eigen::Vector2d>, 4> prev_foot_positions{};
    std::array<bool, 4> foot_contacts{false, false, false, false};
    std::array<double, 12> joint_positions{};

    int gazebo_clock_sec = 0, gazebo_clock_nanosec = 0, encoder_pos = 0;

    OdometryState() = default;
    explicit OdometryState(int window);

    void append_delta(double dx, double dy);
    std::pair<double, double> average_delta() const;
    void reset();
};

double normalize_angle(double angle) noexcept;
void update_odometry(OdometryState& state, double dt, double contact_count_coeff = 0.65);

}  // namespace quadropted
