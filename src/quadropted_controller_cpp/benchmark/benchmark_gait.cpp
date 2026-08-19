#include "benchmark_gait.h"

#include "benchmark_utils.h"
#include "quadropted_controller_cpp/controllers/trot/trot_gait.hpp"

using namespace quadropted;

void benchmark_gait_controller() {
    benchmark::print_header("Gait Controller Benchmark");

    auto stance = benchmark::create_default_stance();
    TrotGaitController trot(0.04, 0.18, 0.02, false, stance);

    std::cout << "Parameters:\n";
    std::cout << "  stance_time: 0.04, swing_time: 0.18, time_step: 0.02\n";
    std::cout << "  stance_ticks: " << trot.stance_ticks() << "\n";
    std::cout << "  swing_ticks: " << trot.swing_ticks() << "\n";
    std::cout << "  phase_length: " << trot.phase_length() << "\n";

    auto pt = trot.phase_ticks();
    std::cout << "  phase_ticks: [";
    for (size_t i = 0; i < pt.size(); ++i) {
        std::cout << pt[i];
        if (i < pt.size() - 1) std::cout << ", ";
    }
    std::cout << "]\n";

    std::cout << "\nPhase contacts at ticks:\n";
    for (int tick = 0; tick <= 22; tick += 2) {
        auto c = trot.contacts(tick);
        std::cout << "  tick=" << tick << ": [" << c(0) << ", " << c(1) << ", " << c(2) << ", " << c(3) << "]\n";
    }
}

void benchmark_trot_step() {
    benchmark::print_header("Trot Step Benchmark (vx=0.03)");

    auto stance = benchmark::create_default_stance();
    TrotGaitController trot(0.04, 0.18, 0.02, false, stance);

    Eigen::Vector3d cmd_vel;
    cmd_vel << 0.03, 0.0, 0.0;
    double robot_height = 0.25;

    Eigen::MatrixXd current = stance;

    std::cout << "Initial foot_locations:\n";
    benchmark::print_foot_locations("  ", current);

    std::cout << "\nStep evolution (ticks 0-20):\n";
    for (int tick = 0; tick <= 20; ++tick) {
        auto contacts = trot.contacts(tick);
        int subphase = trot.subphase_ticks(tick);

        Eigen::MatrixXd next = trot.step(tick, current, cmd_vel, robot_height);

        std::cout << "tick=" << std::setw(2) << tick << " phase=" << trot.phase_index(tick)
                  << " subphase=" << std::setw(2) << subphase << " contacts: [" << contacts(0) << contacts(1)
                  << contacts(2) << contacts(3) << "]" << " -> foot_z: [" << std::fixed << std::setprecision(2)
                  << next(2, 0) << ", " << next(2, 1) << ", " << next(2, 2) << ", " << next(2, 3) << "]\n";

        current = next;
    }
}
