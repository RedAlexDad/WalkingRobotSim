#pragma once
#include <cmath>
#include <Eigen/Dense>

namespace quadropted {

inline Eigen::Matrix3d rotx(double alpha) {
    return (Eigen::Matrix3d() <<
        1, 0, 0,
        0, std::cos(alpha), -std::sin(alpha),
        0, std::sin(alpha), std::cos(alpha)).finished();
}

inline Eigen::Matrix3d roty(double beta) {
    return (Eigen::Matrix3d() <<
        std::cos(beta), 0, std::sin(beta),
        0, 1, 0,
        -std::sin(beta), 0, std::cos(beta)).finished();
}

inline Eigen::Matrix3d rotz(double gamma) {
    return (Eigen::Matrix3d() <<
        std::cos(gamma), -std::sin(gamma), 0,
        std::sin(gamma), std::cos(gamma), 0,
        0, 0, 1).finished();
}

/// Аналитическая формула Rx*Ry*Rz — быстрее 3 матриц + 2 dot
inline Eigen::Matrix3d rotxyz(double alpha, double beta, double gamma) {
    double ca = std::cos(alpha), sa = std::sin(alpha);
    double cb = std::cos(beta),  sb = std::sin(beta);
    double cg = std::cos(gamma), sg = std::sin(gamma);

    Eigen::Matrix3d m;
    m << cb*cg,        -cb*sg,         sb,
         sa*sb*cg+ca*sg, -sa*sb*sg+ca*cg, -sa*cb,
        -ca*sb*cg+sa*sg,  ca*sb*sg+sa*cg,  ca*cb;
    return m;
}

}
