#include "benchmark_kinematics.h"

#include "benchmark_utils.h"
#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"

using namespace quadropted;

void benchmark_inverse_kinematics() {
    benchmark::print_header("Inverse Kinematics Benchmark");

    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};
    InverseKinematics ik(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);

    auto stance = benchmark::create_default_stance();

    std::cout << "Testing IK for default stance (standing):\n";
    auto joints = ik.inverse_kinematics(stance, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    benchmark::print_joints("  joints[0-11] (all legs)", joints);

    std::cout << "\nPer-leg joints (hip, thigh, calf):\n";
    for (int leg = 0; leg < 4; ++leg) {
        std::cout << "  Leg " << leg << ": [" << joints[leg * 3] << ", " << joints[leg * 3 + 1] << ", "
                  << joints[leg * 3 + 2] << "]\n";
    }

    std::cout << "\nIK with body offset (dx=0.1, dy=0.05, dz=0.25):\n";
    auto joints2 = ik.inverse_kinematics(stance, 0.1, 0.05, 0.25, 0.0, 0.0, 0.0);
    benchmark::print_joints("  joints[0-11]", joints2);
}

void benchmark_forward_kinematics() {
    benchmark::print_header("Forward Kinematics Benchmark");

    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};
    ForwardKinematics fk(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);

    std::vector<double> hip_angles = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};

    std::cout << "Testing FK with zero angles:\n";
    auto pos = fk.forward_kinematics_all_legs(hip_angles);
    std::cout << "  Leg 0: [" << pos[0](0) << ", " << pos[0](1) << ", " << pos[0](2) << "]\n";

    hip_angles = {0.0, 0.86, -1.88, 0.0, 0.86, -1.88, 0.0, 0.86, -1.88, 0.0, 0.86, -1.88};
    pos = fk.forward_kinematics_all_legs(hip_angles);
    std::cout << "\nFK with typical standing angles (0, 0.86, -1.88) for all legs:\n";
    std::cout << "  Leg 0: [" << pos[0](0) << ", " << pos[0](1) << ", " << pos[0](2) << "]\n";
}
