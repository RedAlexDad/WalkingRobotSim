#include <gtest/gtest.h>

#include <cmath>

#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

TEST(StandController, construct_default_stance) {
    quadropted::StandController sc(Eigen::MatrixXd::Zero(3, 4));
    EXPECT_EQ(sc.default_stance().rows(), 3);
    EXPECT_EQ(sc.default_stance().cols(), 4);
}

TEST(StandController, run_returns_default_stance_height) {
    Eigen::MatrixXd ds(3, 4);
    ds << 0.19, 0.19, -0.19, -0.19, -0.15, 0.15, -0.15, 0.15, -0.25, -0.25, -0.25, -0.25;
    quadropted::StandController sc(ds);
    quadropted::State state;
    quadropted::Command cmd;
    cmd.robot_height = -0.20;

    auto result = sc.run(state, cmd);
    EXPECT_EQ(result.rows(), 3);
    EXPECT_EQ(result.cols(), 4);
    EXPECT_NEAR(result(2, 0), -0.20, 1e-12);
    EXPECT_NEAR(result(2, 1), -0.20, 1e-12);
    EXPECT_NEAR(result(2, 2), -0.20, 1e-12);
    EXPECT_NEAR(result(2, 3), -0.20, 1e-12);
}

TEST(StandController, run_updates_body_position) {
    quadropted::StandController sc(Eigen::MatrixXd::Zero(3, 4));
    quadropted::State state;
    quadropted::Command cmd;
    cmd.velocity = {0.1, 0.0, 0.0};
    cmd.robot_height = -0.25;

    sc.run(state, cmd);
    EXPECT_GT(state.body_local_position[0], 0.0);
    EXPECT_DOUBLE_EQ(state.body_local_position[1], 0.0);
    EXPECT_DOUBLE_EQ(state.body_local_position[2], 0.0);
}

TEST(StandController, run_clamps_linear_velocity) {
    quadropted::StandController sc(Eigen::MatrixXd::Zero(3, 4));
    quadropted::State state;
    quadropted::Command cmd;
    cmd.velocity = {10.0, 0.0, 0.0};
    cmd.robot_height = -0.25;

    sc.run(state, cmd);
    double max_step = 0.2 * 0.01;
    EXPECT_LE(std::abs(state.body_local_position[0]), max_step + 1e-12);
}

TEST(StandController, run_zero_command_decays_position) {
    quadropted::StandController sc(Eigen::MatrixXd::Zero(3, 4));
    quadropted::State state;
    state.body_local_position = {1.0, 0.0, 0.0};
    quadropted::Command cmd;
    cmd.robot_height = -0.25;

    for (int i = 0; i < 100; ++i) {
        sc.run(state, cmd);
    }
    EXPECT_LT(std::abs(state.body_local_position[0]), 0.01);
}
