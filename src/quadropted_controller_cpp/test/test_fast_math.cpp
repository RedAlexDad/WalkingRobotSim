#include <gtest/gtest.h>

#include <cmath>
#include <cstdlib>

#include "quadropted_controller_cpp/utils/fast_math.hpp"

TEST(FastMath, atan2_zero_zero) {
    EXPECT_DOUBLE_EQ(quadropted::fast_atan2(0.0, 0.0), 0.0);
}

TEST(FastMath, atan2_positive_axes) {
    EXPECT_NEAR(quadropted::fast_atan2(0.0, 1.0), 0.0, 1e-6);
    EXPECT_NEAR(quadropted::fast_atan2(1.0, 0.0), M_PI_2, 1e-6);
}

TEST(FastMath, atan2_negative_x) {
    double r = quadropted::fast_atan2(0.0, -1.0);
    EXPECT_NEAR(r, M_PI, 1e-6);
}

TEST(FastMath, atan2_negative_y) {
    double r = quadropted::fast_atan2(-1.0, 0.0);
    EXPECT_NEAR(r, -M_PI_2, 1e-6);
}

TEST(FastMath, atan2_both_negative) {
    double r = quadropted::fast_atan2(-1.0, -1.0);
    EXPECT_NEAR(r, -3.0 * M_PI_4, 1e-6);
}

TEST(FastMath, atan2_accuracy_vs_std) {
    double max_error = 0.0;
    for (int i = -100; i <= 100; ++i) {
        for (int j = -100; j <= 100; ++j) {
            double y = static_cast<double>(i);
            double x = static_cast<double>(j);
            double expected = std::atan2(y, x);
            double actual = quadropted::fast_atan2(y, x);
            double error = std::abs(expected - actual);
            if (error > max_error) max_error = error;
        }
    }
    EXPECT_LT(max_error, 0.01);
}
