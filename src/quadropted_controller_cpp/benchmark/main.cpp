#include <iostream>
#include <string>

#include "benchmark_controllers.h"
#include "benchmark_gait.h"
#include "benchmark_kinematics.h"
#include "benchmark_timing.h"

int main(int argc, char* argv[]) {
    int iterations = 10000;
    if (argc > 1) {
        iterations = std::stoi(argv[1]);
    }
    std::cout << "╔══════════════════════════════════════════════════════════╗\n";
    std::cout << "║     C++ Quadruped Controller Benchmark v0.0.2            ║\n";
    std::cout << "╚══════════════════════════════════════════════════════════╝\n";

    benchmark_gait_controller();
    benchmark_trot_step();
    benchmark_inverse_kinematics();
    benchmark_forward_kinematics();
    benchmark_rest_controller();
    benchmark_stand_controller();
    benchmark_trot_swing();
    benchmark_trot_stance();
    benchmark_pid_controller();
    benchmark_timing_json(iterations);

    std::cout << "\n" << std::string(60, '=') << "\n";
    std::cout << "Benchmark completed successfully!\n";
    std::cout << std::string(60, '=') << "\n";

    return 0;
}
