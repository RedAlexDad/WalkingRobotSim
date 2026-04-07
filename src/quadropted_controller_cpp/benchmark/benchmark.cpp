#include <iostream>
#include <iomanip>
#include <vector>
#include <chrono>
#include <cmath>
#include <array>
#include <Eigen/Dense>
#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot_gait.hpp"
#include "quadropted_controller_cpp/controllers/trot_swing.hpp"
#include "quadropted_controller_cpp/controllers/trot_stance.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"

using namespace quadropted;

void print_header(const std::string& title) {
    std::cout << "\n" << std::string(60, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(60, '=') << "\n";
}

void print_joints(const std::string& label, const std::vector<double>& joints) {
    std::cout << label << ": [";
    for (size_t i = 0; i < joints.size(); ++i) {
        std::cout << std::fixed << std::setprecision(4) << joints[i];
        if (i < joints.size() - 1) std::cout << ", ";
    }
    std::cout << "]\n";
}

void print_foot_locations(const std::string& label, const Eigen::MatrixXd& feet) {
    std::cout << label << ":\n";
    std::cout << "  FR: [" << feet(0,0) << ", " << feet(1,0) << ", " << feet(2,0) << "]\n";
    std::cout << "  FL: [" << feet(0,1) << ", " << feet(1,1) << ", " << feet(2,1) << "]\n";
    std::cout << "  RR: [" << feet(0,2) << ", " << feet(1,2) << ", " << feet(2,2) << "]\n";
    std::cout << "  RL: [" << feet(0,3) << ", " << feet(1,3) << ", " << feet(2,3) << "]\n";
}

Eigen::MatrixXd create_default_stance() {
    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};
    double dx = body[0] * 0.5 + 0.02;
    double dy = body[1] * 0.5 + legs[1];
    
    Eigen::MatrixXd stance(3, 4);
    stance <<  dx,  dx, -dx, -dx,
              -dy,  dy, -dy,  dy,
                0,   0,   0,   0;
    return stance;
}

void benchmark_gait_controller() {
    print_header("Gait Controller Benchmark");
    
    auto stance = create_default_stance();
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
    print_header("Trot Step Benchmark (vx=0.03)");
    
    auto stance = create_default_stance();
    TrotGaitController trot(0.04, 0.18, 0.02, false, stance);
    
    Eigen::Vector3d cmd_vel;
    cmd_vel << 0.03, 0.0, 0.0;
    double robot_height = 0.25;
    
    Eigen::MatrixXd current = stance;
    
    std::cout << "Initial foot_locations:\n";
    print_foot_locations("  ", current);
    
    std::cout << "\nStep evolution (ticks 0-20):\n";
    for (int tick = 0; tick <= 20; ++tick) {
        auto contacts = trot.contacts(tick);
        int subphase = trot.subphase_ticks(tick);
        
        Eigen::MatrixXd next = trot.step(tick, current, cmd_vel, robot_height);
        
        std::cout << "tick=" << std::setw(2) << tick 
                  << " phase=" << trot.phase_index(tick)
                  << " subphase=" << std::setw(2) << subphase
                  << " contacts: [" << contacts(0) << contacts(1) << contacts(2) << contacts(3) << "]"
                  << " -> foot_z: [" << std::fixed << std::setprecision(2) << next(2,0) << ", " << next(2,1) << ", " << next(2,2) << ", " << next(2,3) << "]\n";
        
        current = next;
    }
}

void benchmark_inverse_kinematics() {
    print_header("Inverse Kinematics Benchmark");
    
    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};
    InverseKinematics ik(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);
    
    auto stance = create_default_stance();
    
    std::cout << "Testing IK for default stance (standing):\n";
    auto joints = ik.inverse_kinematics(stance, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    print_joints("  joints[0-11] (all legs)", joints);
    
    std::cout << "\nPer-leg joints (hip, thigh, calf):\n";
    for (int leg = 0; leg < 4; ++leg) {
        std::cout << "  Leg " << leg << ": [" 
                  << joints[leg*3] << ", " << joints[leg*3+1] << ", " << joints[leg*3+2] << "]\n";
    }
    
    std::cout << "\nIK with body offset (dx=0.1, dy=0.05, dz=0.25):\n";
    auto joints2 = ik.inverse_kinematics(stance, 0.1, 0.05, 0.25, 0.0, 0.0, 0.0);
    print_joints("  joints[0-11]", joints2);
}

void benchmark_forward_kinematics() {
    print_header("Forward Kinematics Benchmark");
    
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

void benchmark_rest_controller() {
    print_header("Rest Controller Benchmark");
    
    auto stance = create_default_stance();
    RestController rest(stance);
    
    State state(0.25);
    state.foot_locations = stance;
    Command cmd;
    cmd.robot_height = 0.25;
    
    std::cout << "Testing Rest controller step:\n";
    auto result = rest.step(state, cmd);
    print_foot_locations("  Result", result);
}

void benchmark_stand_controller() {
    print_header("Stand Controller Benchmark");
    
    auto stance = create_default_stance();
    StandController stand(stance);
    
    State state(0.25);
    state.foot_locations = stance;
    Command cmd;
    cmd.robot_height = 0.25;
    cmd.velocity = {0.0, 0.0, 0.0};
    cmd.yaw_rate = {0.0, 0.0, 0.0};
    
    std::cout << "Testing Stand controller step:\n";
    auto result = stand.run(state, cmd);
    print_foot_locations("  Result", result);
}

void benchmark_trot_swing() {
    print_header("TrotSwing Controller Benchmark");
    
    auto stance = create_default_stance();
    TrotSwingController swing(9, 0.02, 0.14, stance);
    
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
    print_header("TrotStance Controller Benchmark");
    
    auto stance = create_default_stance();
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
    print_header("PID Controller Benchmark");
    
    PIDController pid(0.15, 0.02, 0.002);
    
    std::cout << "Parameters: kp=0.15, ki=0.02, kd=0.002\n";
    
    std::cout << "\nPID response to roll=0.1, pitch=0.1 over 10 steps:\n";
    for (int i = 0; i <= 10; ++i) {
        auto output = pid.run(0.1, 0.1, (double)i * 0.02);
        std::cout << "  step=" << i << ": roll_comp=" << output[0] << ", pitch_comp=" << output[1] << "\n";
    }
}

void benchmark_timing() {
    print_header("Performance Timing Benchmark");
    
    auto stance = create_default_stance();
    TrotGaitController trot(0.04, 0.18, 0.02, false, stance);
    
    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};
    InverseKinematics ik(body[0], body[1], legs[0], legs[1], legs[2], legs[3]);
    
    Eigen::Vector3d cmd_vel;
    cmd_vel << 0.03, 0.0, 0.0;
    double robot_height = 0.25;
    
    const int iterations = 10000;
    
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto next = trot.step(i % 22, stance, cmd_vel, robot_height);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    
    std::cout << "TrotGaitController.step():\n";
    std::cout << "  " << iterations << " iterations in " << duration << " microseconds\n";
    std::cout << "  ~" << (double)duration / iterations << " microseconds per call\n";
    
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        auto joints = ik.inverse_kinematics(stance, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    
    std::cout << "\nInverseKinematics.inverse_kinematics():\n";
    std::cout << "  " << iterations << " iterations in " << duration << " microseconds\n";
    std::cout << "  ~" << (double)duration / iterations << " microseconds per call\n";
}

int main() {
    std::cout << "╔══════════════════════════════════════════════════════════╗\n";
    std::cout << "║     C++ Quadruped Controller Benchmark v0.0.1            ║\n";
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
    benchmark_timing();
    
    std::cout << "\n" << std::string(60, '=') << "\n";
    std::cout << "Benchmark completed successfully!\n";
    std::cout << std::string(60, '=') << "\n";
    
    return 0;
}
