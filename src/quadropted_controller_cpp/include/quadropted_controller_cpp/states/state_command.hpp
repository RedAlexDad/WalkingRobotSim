#pragma once
#include <array>
#include <Eigen/Dense>

namespace quadropted {

enum class BehaviorState { REST = 0, TROT, CRAWL, STAND };

struct State {
    double body_height = 0.25;
    Eigen::Vector3d foot_locations[4]{Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero(),
                                       Eigen::Vector3d::Zero(), Eigen::Vector3d::Zero()};
    std::array<double, 3> body_local_position{0, 0, 0};
    std::array<double, 3> body_local_orientation{0, 0, 0};
    double imu_roll = 0, imu_pitch = 0;
    int ticks = 0;
    BehaviorState behavior_state = BehaviorState::REST;
    double robot_height = 0.0;
};

struct Command {
    std::array<double, 3> velocity{0, 0, 0};
    std::array<double, 3> yaw_rate{0, 0, 0};
    double robot_height = 0.0;
    bool trot_event = false, rest_event = false, crawl_event = false, stand_event = false;
};

}
