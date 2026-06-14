#include <gtest/gtest.h>

#include <cmath>
#include <limits>

#include <Eigen/Dense>

#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include "quadropted_controller_cpp/utils/fast_math.hpp"

TEST(FastMath, atan2_extreme_values) {
    double r = quadropted::fast_atan2(1e6, 1.0);
    EXPECT_NEAR(r, M_PI_2, 1e-3);

    r = quadropted::fast_atan2(1.0, 1e6);
    EXPECT_NEAR(r, 0.0, 1e-3);

    r = quadropted::fast_atan2(-1e6, -1.0);
    EXPECT_NEAR(r, -M_PI_2, 1e-3);
}

TEST(FastMath, atan2_subnormal) {
    double r = quadropted::fast_atan2(1e-300, 1.0);
    EXPECT_NEAR(r, 1e-300, 1e-6);

    r = quadropted::fast_atan2(1.0, 1e300);
    EXPECT_NEAR(r, 0.0, 1e-6);
}

TEST(PID, nan_input_propagates) {
    quadropted::PIDController pid(1.0, 0.0, 0.0);
    pid.reset(0.0);
    double t = 0.0;
    pid.run(0.0, 0.0, t);

    auto result = pid.run(std::numeric_limits<double>::quiet_NaN(), 0.0, t + 0.01);
    EXPECT_TRUE(std::isnan(result[0]));
}

TEST(PID, extreme_error_no_crash) {
    quadropted::PIDController pid(1.0, 0.5, 0.1);
    pid.reset(0.0);
    double t = 0.0;
    pid.run(0.0, 0.0, t);

    auto result = pid.run(1e6, 0.0, t + 0.01);
    EXPECT_TRUE(std::isfinite(result[0]));
    EXPECT_TRUE(std::isfinite(result[1]));
}

TEST(StandController, nan_velocity_no_crash) {
    quadropted::StandController sc(Eigen::MatrixXd::Zero(3, 4));
    quadropted::State state;
    quadropted::Command cmd;
    cmd.velocity = {std::numeric_limits<double>::quiet_NaN(), 0.0, 0.0};
    cmd.robot_height = -0.25;

    auto result = sc.run(state, cmd);
    EXPECT_TRUE(std::isfinite(result(0, 0)));
}
