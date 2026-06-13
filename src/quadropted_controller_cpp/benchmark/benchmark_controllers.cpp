#include "benchmark_controllers.h"

#include "benchmark_utils.h"
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_stance.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_swing.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

using namespace quadropted;

void benchmark_rest_controller() {
    benchmark::print_header("Rest Controller Benchmark");

    auto stance = benchmark::create_default_stance();
    RestController rest(stance);

    State state(0.25);
    state.foot_locations = stance;
    Command cmd;
    cmd.robot_height = 0.25;

    std::cout << "Testing Rest controller step:\n";
    auto result = rest.step(state, cmd);
    benchmark::print_foot_locations("  Result", result);
}

void benchmark_stand_controller() {
    benchmark::print_header("Stand Controller Benchmark");

    auto stance = benchmark::create_default_stance();
    StandController stand(stance);

    State state(0.25);
    state.foot_locations = stance;
    Command cmd;
    cmd.robot_height = 0.25;
    cmd.velocity = {0.0, 0.0, 0.0};
    cmd.yaw_rate = {0.0, 0.0, 0.0};

    std::cout << "Testing Stand controller step:\n";
    auto result = stand.run(state, cmd);
    benchmark::print_foot_locations("  Result", result);
}

void benchmark_trot_swing() {
    benchmark::print_header("TrotSwing Controller Benchmark");

    auto stance = benchmark::create_default_stance();
    TrotSwingController swing(9, 0.02, 0.14, stance, 22, 2);

    std::cout << "Parameters: swing_ticks=9, time_step=0.02, z_leg_lift=0.14\n";

    std::cout << "\nswing_height at different phases:\n";
    for (double p = 0.0; p <= 1.0; p += 0.1) {
        std::cout << "  swing_prop=" << p << ": height=" << swing.swing_height(p) << "\n";
    }

    Eigen::Vector3d cmd_vel;
    cmd_vel << 0.03, 0.0, 0.0;

    std::cout << "\nraibert_touchdown_location for leg 0 (vx=0.03):\n";
    auto touch = swing.raibert_touchdown_location(0, cmd_vel);
    std::cout << "  [" << touch(0) << ", " << touch(1) << ", " << touch(2) << "]\n";

    std::cout << "\nnext_foot_location (swing_prop=0.5, leg=0, robot_height=0.25):\n";
    auto next = swing.next_foot_location(0.5, 0, stance, cmd_vel, 0.25);
    std::cout << "  [" << next(0) << ", " << next(1) << ", " << next(2) << "]\n";
}

void benchmark_trot_stance() {
    benchmark::print_header("TrotStance Controller Benchmark");

    auto stance = benchmark::create_default_stance();
    TrotStanceController stance_ctrl(22, 2, 9, 0.02, 0.02);

    Eigen::Vector3d cmd_vel;
    cmd_vel << 0.03, 0.0, 0.0;

    std::cout << "Parameters: phase_length=22, stance_ticks=2, swing_ticks=9, z_error_constant=0.02\n";

    std::cout << "\nposition_delta for leg 0 (vx=0.03, robot_height=0.25):\n";
    auto delta = stance_ctrl.position_delta(0, stance, cmd_vel, 0.25);
    std::cout << "  [" << delta(0) << ", " << delta(1) << ", " << delta(2) << "]\n";

    std::cout << "\nnext_foot_location for leg 0:\n";
    auto next = stance_ctrl.next_foot_location(0, stance, cmd_vel, 0.25);
    std::cout << "  [" << next(0) << ", " << next(1) << ", " << next(2) << "]\n";
}

void benchmark_pid_controller() {
    benchmark::print_header("PID Controller Benchmark");

    PIDController pid(0.15, 0.02, 0.002);

    std::cout << "Parameters: kp=0.15, ki=0.02, kd=0.002\n";

    std::cout << "\nPID response to roll=0.1, pitch=0.1 over 10 steps:\n";
    for (int i = 0; i <= 10; ++i) {
        auto output = pid.run(0.1, 0.1, (double)i * 0.02);
        std::cout << "  step=" << i << ": roll_comp=" << output[0] << ", pitch_comp=" << output[1] << "\n";
    }
}
