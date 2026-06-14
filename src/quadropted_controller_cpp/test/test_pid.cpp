#include <gtest/gtest.h>

#include "quadropted_controller_cpp/controllers/pid_controller.hpp"

TEST(PID, run_returns_2_elements) {
    quadropted::PIDController pid(0.15, 0.02, 0.002);
    pid.reset(0.0);
    auto result = pid.run(0.1, -0.05, 0.02);
    ASSERT_EQ(result.size(), 2u);
}

TEST(PID, first_call_returns_zero) {
    quadropted::PIDController pid(1.0, 0.0, 0.0);
    auto result = pid.run(0.1, 0.2, 1.0);
    EXPECT_DOUBLE_EQ(result[0], 0.0);
    EXPECT_DOUBLE_EQ(result[1], 0.0);
}

TEST(PID, proportional_convergence) {
    quadropted::PIDController pid(2.0, 0.0, 0.0);
    pid.reset(0.0);
    double t = 0.0;
    constexpr double dt = 0.01;
    pid.run(0.0, 0.0, t);

    // Sustained error of 1.0 rad on roll
    for (int i = 0; i < 5; ++i) {
        t += dt;
        auto result = pid.run(1.0, 0.0, t);
        EXPECT_NEAR(result[0], -2.0, 1e-12);
    }
}

TEST(PID, integral_clamping) {
    quadropted::PIDController pid(0.0, 1.0, 0.0);
    pid.reset(0.0);
    double t = 0.0;
    constexpr double dt = 0.01;
    pid.run(0.0, 0.0, t);

    // error = desired - actual = 0 - 10 = -10, I-term clamps at -max_i_ after ~20 steps
    for (int i = 0; i < 100; ++i) {
        t += dt;
        pid.run(10.0, 0.0, t);
    }
    t += dt;
    auto result = pid.run(10.0, 0.0, t);
    EXPECT_NEAR(result[0], -0.2, 1e-12);
}

TEST(PID, integral_windup_negative_clamping) {
    quadropted::PIDController pid(0.0, 1.0, 0.0);
    pid.reset(0.0);
    double t = 0.0;
    constexpr double dt = 0.01;
    pid.run(0.0, 0.0, t);

    // error = desired - actual = 0 - (-10) = 10, I-term clamps at +max_i_
    for (int i = 0; i < 100; ++i) {
        t += dt;
        pid.run(-10.0, 0.0, t);
    }
    t += dt;
    auto result = pid.run(-10.0, 0.0, t);
    EXPECT_NEAR(result[0], 0.2, 1e-12);
}

TEST(PID, set_desired_changes_setpoint) {
    quadropted::PIDController pid(2.0, 0.0, 0.0);
    pid.reset(0.0);
    pid.set_desired(0.5, -0.3);
    pid.run(0.0, 0.0, 0.0);

    auto result = pid.run(0.0, 0.0, 0.01);
    // error = desired - actual = (0.5, -0.3) - (0, 0) = (0.5, -0.3)
    EXPECT_NEAR(result[0], 2.0 * 0.5, 1e-12);
    EXPECT_NEAR(result[1], 2.0 * (-0.3), 1e-12);
}

TEST(PID, reset_restores_initial_state) {
    quadropted::PIDController pid(1.0, 0.5, 0.1);
    pid.reset(0.0);
    pid.run(1.0, 0.0, 0.0);

    auto after_run = pid.run(1.0, 0.0, 0.01);
    EXPECT_NE(after_run[0], 0.0);

    pid.reset(1.0);
    auto after_reset = pid.run(1.0, 0.0, 1.0);
    EXPECT_DOUBLE_EQ(after_reset[0], 0.0);
}

TEST(PID, zero_step_returns_zero) {
    quadropted::PIDController pid(1.0, 0.0, 0.0);
    pid.reset(0.0);

    auto first = pid.run(0.1, 0.0, 0.0);
    EXPECT_DOUBLE_EQ(first[0], 0.0);

    auto second = pid.run(0.1, 0.0, 0.0);
    EXPECT_DOUBLE_EQ(second[0], 0.0);
}

TEST(PID, p_and_i_convergence) {
    quadropted::PIDController pid(2.0, 0.5, 0.0);
    pid.set_desired(0.5, -0.5);
    pid.reset(0.0);
    double t = 0.0;
    constexpr double dt = 0.01;

    // State at setpoint -> output should approach 0 as error decays
    pid.run(0.5, -0.5, t);
    t += dt;
    auto result = pid.run(0.5, -0.5, t);
    // error = 0, so output = 0 + ki * integral + 0
    // integral was 0, so output should be 0
    EXPECT_NEAR(result[0], 0.0, 1e-12);
    EXPECT_NEAR(result[1], 0.0, 1e-12);
}
