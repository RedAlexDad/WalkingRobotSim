#include <gtest/gtest.h>

#include <cmath>

#include <Eigen/Dense>

#include "quadropted_controller_cpp/controllers/crawl/crawl_gait.hpp"
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

TEST(Gait, phase_ticks_has_4_elements) {
    Eigen::MatrixXi cp(4, 4);
    cp << 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0;
    quadropted::GaitController gc(0.04, 0.18, 0.02, cp, Eigen::MatrixXd::Zero(3, 4));
    const auto& pt = gc.phase_ticks();
    ASSERT_EQ(pt.size(), 4u);
    EXPECT_EQ(pt[0], 2);
    EXPECT_EQ(pt[1], 9);
    EXPECT_EQ(pt[2], 2);
    EXPECT_EQ(pt[3], 9);
}

TEST(Gait, contacts_has_4_elements) {
    Eigen::MatrixXi cp(4, 4);
    cp << 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0;
    quadropted::GaitController gc(0.04, 0.18, 0.02, cp, Eigen::MatrixXd::Zero(3, 4));
    auto c = gc.contacts(0);
    ASSERT_EQ(c.size(), 4);
}

TEST(CrawlGait, construct_and_reset) {
    Eigen::MatrixXd ds = Eigen::MatrixXd::Zero(3, 4);
    quadropted::CrawlGaitController cgc(0.04, 0.18, 0.02, ds);
    EXPECT_TRUE(cgc.is_first_cycle());
    EXPECT_EQ(cgc.default_stance().rows(), 3);
    EXPECT_EQ(cgc.default_stance().cols(), 4);
}

TEST(CrawlGait, reset_restores_first_cycle) {
    Eigen::MatrixXd ds = Eigen::MatrixXd::Zero(3, 4);
    quadropted::CrawlGaitController cgc(0.04, 0.18, 0.02, ds);
    quadropted::LegsMatrix current = ds;
    Eigen::Vector3d cmd_vel(0.0, 0.0, 0.0);
    const double robot_height = -0.25;

    quadropted::LegsMatrix result = cgc.step(0, current, cmd_vel, robot_height);
    EXPECT_TRUE(cgc.is_first_cycle());

    result = cgc.step(cgc.phase_length(), current, cmd_vel, robot_height);
    EXPECT_FALSE(cgc.is_first_cycle());

    cgc.reset();
    EXPECT_TRUE(cgc.is_first_cycle());
}

TEST(CrawlGait, step_returns_valid_matrix) {
    Eigen::MatrixXd ds = Eigen::MatrixXd::Zero(3, 4);
    quadropted::CrawlGaitController cgc(0.04, 0.18, 0.02, ds);
    quadropted::LegsMatrix current = ds;
    Eigen::Vector3d cmd_vel(0.0, 0.0, 0.0);

    auto result = cgc.step(0, current, cmd_vel, -0.25);
    EXPECT_EQ(result.rows(), 3);
    EXPECT_EQ(result.cols(), 4);
}

TEST(CrawlGait, step_maintains_leg_count) {
    Eigen::MatrixXd ds = Eigen::MatrixXd::Zero(3, 4);
    quadropted::CrawlGaitController cgc(0.04, 0.18, 0.02, ds);
    quadropted::LegsMatrix current = ds;
    Eigen::Vector3d cmd_vel(0.3, 0.0, 0.0);

    for (int t = 0; t < cgc.phase_length() * 2; ++t) {
        auto result = cgc.step(t, current, cmd_vel, -0.25);
        EXPECT_EQ(result.cols(), 4);
    }
}
