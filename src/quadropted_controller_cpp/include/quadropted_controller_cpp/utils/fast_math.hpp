#pragma once
#include <algorithm>
#include <cmath>

namespace quadropted {

inline double fast_atan2(double y, double x) noexcept {
    if (x == 0.0 && y == 0.0) return 0.0;

    double ay = std::abs(y);
    double ax = std::abs(x);
    double a = std::min(ax, ay) / std::max(ax, ay);

    // Range reduce to [0, tan(π/8)] ≈ [0, 0.4142]
    // Identity: atan(a) = π/4 - atan((1-a)/(1+a))  for a > 0.4142
    static constexpr double TAN_PI_8 = 0.41421356237309503;
    double r;
    if (a <= TAN_PI_8) {
        double a2 = a * a;
        r = a * (1.0 + a2 * (-0.332932 + a2 * (0.106704 + a2 * (-0.035436))));
    } else {
        double b = (1.0 - a) / (1.0 + a);
        double b2 = b * b;
        r = M_PI_4 - b * (1.0 + b2 * (-0.332932 + b2 * (0.106704 + b2 * (-0.035436))));
    }

    if (ay > ax) r = M_PI_2 - r;
    if (x < 0.0) r = M_PI - r;
    if (y < 0.0) r = -r;

    return r;
}

}  // namespace quadropted
