#include "benchmark_timing.h"

#include <chrono>

#include "benchmark_utils.h"
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_gait.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_stance.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_swing.hpp"
#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

using namespace quadropted;

void benchmark_timing_json(int iterations) {
    auto stance = benchmark::create_default_stance();
    TrotGaitController trot(0.04, 0.18, 0.02, false, stance);

    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};
    InverseKinematics ik(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);
    ForwardKinematics fk(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);

    Eigen::Vector3d cmd_vel;
    cmd_vel << 0.03, 0.0, 0.0;
    double robot_height = 0.25;

    State state(0.25);
    state.foot_locations = stance;
    Command cmd;
    cmd.velocity = {0.03, 0.0, 0.0};
    cmd.yaw_rate = {0.0, 0.0, 0.0};
    cmd.robot_height = 0.25;

    TrotSwingController swing(9, 0.02, 0.14, stance, 22, 2);
    TrotStanceController stance_ctrl(22, 2, 9, 0.02, 0.02);
    StandController stand(stance);
    RestController rest(stance);

    std::cout << "ITERATIONS=" << iterations << "\n";

    std::cout << "=== BENCHMARK_JSON_START ===\n";

    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto c = trot.contacts(5);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "GaitController.contacts(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto s = trot.subphase_ticks(5);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "GaitController.subphase_ticks(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto h = swing.swing_height(0.5);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "TrotSwingController.swing_height(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto n = swing.next_foot_location(0.5, 0, stance, cmd_vel, robot_height);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "TrotSwingController.next_foot_location(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto r = swing.raibert_touchdown_location(0, cmd_vel);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "TrotSwingController.raibert_touchdown(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto d = stance_ctrl.position_delta(0, stance, cmd_vel, robot_height);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "TrotStanceController.position_delta(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto n = stance_ctrl.next_foot_location(0, stance, cmd_vel, robot_height);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "TrotStanceController.next_foot_location(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto r = stand.run(state, cmd);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "StandController.run(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        quadropted::JointAngles ja = {0.0, 0.86, -1.88, 0.0, 0.86, -1.88, 0.0, 0.86, -1.88, 0.0, 0.86, -1.88};
        auto p = fk.forward_kinematics_all_legs(ja);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "ForwardKinematics.forward_kinematics_all_legs(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto r = rest.step(state, cmd);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "RestController.step(): " << (double)duration / iterations << "\n";

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto j = ik.inverse_kinematics(stance, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "InverseKinematics.inverse_kinematics(): " << (double)duration / iterations << "\n";

    PIDController pid(0.15, 0.02, 0.002);
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto o = pid.run(0.1, 0.1, 0.02);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "PIDController.run(): " << (double)duration / iterations << "\n";

    Eigen::MatrixXd current_stance = stance;
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        int tick = i % 22;
        auto contacts = trot.contacts(tick);
        Eigen::MatrixXd step_result = current_stance;
        for (int leg = 0; leg < 4; ++leg) {
            if (contacts(leg) == 1) {
                step_result.col(leg) = stance_ctrl.next_foot_location(leg, current_stance, cmd_vel, robot_height);
            } else {
                int sub = trot.subphase_ticks(tick);
                double swing_prop = (double)sub / 9.0;
                step_result.col(leg) = swing.next_foot_location(swing_prop, leg, current_stance, cmd_vel, robot_height);
            }
        }
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << "Trot Step (full cycle): " << (double)duration / iterations << "\n";

    std::cout << "=== BENCHMARK_JSON_END ===\n";
}
