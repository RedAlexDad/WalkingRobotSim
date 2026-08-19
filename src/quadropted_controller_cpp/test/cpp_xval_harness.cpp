// cpp_xval_harness.cpp — C++ reference harness for Rust cross-validation.
//
// Usage: cpp_xval_harness <test_name>
// Prints JSON to stdout with C++ reference values for the given test.
// Rust tests (quadropted-core/tests/cross_validation.rs) run this binary
// and compare its output against the Rust implementation.
//
// IMPORTANT: this is a plain executable (not a gmock test) so that its
// stdout stays clean JSON. It is built by colcon alongside the unit tests
// and lives in build/quadropted_controller_cpp/cpp_xval_harness.

#include <Eigen/Dense>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "quadropted_controller_cpp/controllers/crawl/crawl_gait.hpp"
#include "quadropted_controller_cpp/controllers/crawl/crawl_stance.hpp"
#include "quadropted_controller_cpp/controllers/crawl/crawl_swing.hpp"
#include "quadropted_controller_cpp/controllers/gait_controller.hpp"
#include "quadropted_controller_cpp/controllers/pid_controller.hpp"
#include "quadropted_controller_cpp/controllers/rest_controller.hpp"
#include "quadropted_controller_cpp/controllers/stand_controller.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_gait.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_stance.hpp"
#include "quadropted_controller_cpp/controllers/trot/trot_swing.hpp"
#include "quadropted_controller_cpp/kinematics/forward_kinematics.hpp"
#include "quadropted_controller_cpp/kinematics/inverse_kinematics.hpp"
#include "quadropted_controller_cpp/odometry/odometry.hpp"
#include "quadropted_controller_cpp/states/state_command.hpp"
#include "quadropted_controller_cpp/utils/homogeneous_transforms.hpp"
#include "quadropted_controller_cpp/utils/rotation_matrices.hpp"

using namespace quadropted;

// ── JSON helpers ─────────────────────────────────────────────
static void print_vec(const Eigen::Vector3d& v) {
    printf("[%.17g,%.17g,%.17g]", v.x(), v.y(), v.z());
}
static void print_mat3(const Eigen::Matrix3d& m) {
    printf("[");
    for (int r = 0; r < 3; ++r) {
        if (r) printf(",");
        printf("[%.17g,%.17g,%.17g]", m(r, 0), m(r, 1), m(r, 2));
    }
    printf("]");
}
static void print_mat4(const Eigen::Matrix4d& m) {
    printf("[");
    for (int r = 0; r < 4; ++r) {
        if (r) printf(",");
        printf("[%.17g,%.17g,%.17g,%.17g]", m(r, 0), m(r, 1), m(r, 2), m(r, 3));
    }
    printf("]");
}
static void print_legs(const LegsMatrix& m) {
    printf("[");
    for (int c = 0; c < 4; ++c) {
        if (c) printf(",");
        printf("[%.17g,%.17g,%.17g]", m(0, c), m(1, c), m(2, c));
    }
    printf("]");
}
static void print_arr12(const std::array<double, 12>& a) {
    printf("[");
    for (int i = 0; i < 12; ++i) {
        if (i) printf(",");
        printf("%.17g", a[i]);
    }
    printf("]");
}
static void print_angles3(const std::array<double, 3>& a) {
    printf("[%.17g,%.17g,%.17g]", a[0], a[1], a[2]);
}
static void print_local4x3(const Eigen::Matrix<double, 4, 3>& m) {
    printf("[");
    for (int i = 0; i < 4; ++i) {
        if (i) printf(",");
        printf("[%.17g,%.17g,%.17g]", m(i, 0), m(i, 1), m(i, 2));
    }
    printf("]");
}

// Stance как в активном C++-ноде (RobotControllerNode ctor):
// dx_front = bl*0.5 + 0.02, dx_back = bl*0.5, dy = bw*0.5 + l2
static LegsMatrix node_default_stance() {
    double body[] = {0.3762, 0.0935};
    double legs[] = {0.0, 0.0955, 0.213, 0.213};
    double dx_front = body[0] * 0.5 + 0.02;
    double dx_back = body[0] * 0.5 + 0.0;
    double dy = body[1] * 0.5 + legs[1];
    LegsMatrix s;
    s << dx_front, dx_front, -dx_back, -dx_back, -dy, dy, -dy, dy, 0, 0, 0, 0;
    return s;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <test_name>\n", argv[0]);
        return 1;
    }
    std::string test = argv[1];
    printf("{\"test\":\"%s\",\"data\":", test.c_str());

    // ═══════════════ math: rotations ═══════════════
    if (test == "rotx" || test == "roty" || test == "rotz") {
        std::vector<double> angles = {0.0, 0.5, -0.3, M_PI / 4, M_PI / 2, 1.1};
        printf("[");
        for (size_t i = 0; i < angles.size(); ++i) {
            if (i) printf(",");
            Eigen::Matrix3d m = (test == "rotx") ? rotx(angles[i]) : (test == "roty") ? roty(angles[i]) : rotz(angles[i]);
            print_mat3(m);
        }
        printf("]");
    } else if (test == "rotxyz") {
        std::vector<std::array<double, 3>> cases = {{0, 0, 0}, {0.3, -0.2, 0.5}, {1.0, 0.5, -0.7}, {-0.4, 0.9, 0.1}};
        printf("[");
        for (size_t i = 0; i < cases.size(); ++i) {
            if (i) printf(",");
            print_mat3(rotxyz(cases[i][0], cases[i][1], cases[i][2]));
        }
        printf("]");
    } else if (test == "homog_transxyz" || test == "homog_transform" || test == "homog_inverse") {
        std::vector<std::array<double, 6>> cases = {
            {0, 0, 0, 0, 0, 0}, {0.1, 0.2, 0.3, 0.4, 0.5, 0.6}, {-0.5, 1.2, 0.05, -0.1, 0.3, 0.7}};
        printf("[");
        for (size_t i = 0; i < cases.size(); ++i) {
            if (i) printf(",");
            const auto& c = cases[i];
            Eigen::Matrix4d m;
            if (test == "homog_transxyz") {
                m = homog_transxyz(c[0], c[1], c[2]);
            } else if (test == "homog_transform") {
                m = homog_transform(c[0], c[1], c[2], c[3], c[4], c[5]);
            } else {
                m = homog_transform(c[0], c[1], c[2], c[3], c[4], c[5]);
                m = homog_transform_inverse(m);
            }
            print_mat4(m);
        }
        printf("]");
    }

    // ═══════════════ kinematics ═══════════════
    else if (test == "fk_leg") {
        double bl = 0.3762, bw = 0.0935, l1 = 0.0, l2 = 0.0955, l3 = 0.213, l4 = 0.213;
        std::vector<std::array<double, 3>> angle_cases = {{0, 0, 0}, {0.3, -0.6, 0.5}, {-0.2, 0.8, -0.4}, {0.5, 0.2, -0.9}};
        printf("[");
        for (size_t ci = 0; ci < angle_cases.size(); ++ci) {
            if (ci) printf(",");
            printf("[");
            for (int leg = 0; leg < 4; ++leg) {
                if (leg) printf(",");
                // Leg base positions (как Rust leg_base_positions):
                // FR=(hl,-hw), FL=(hl,hw), RR=(-hl,-hw), RL=(-hl,hw)
                double hl = 0.5 * bl;
                double hw = 0.5 * bw;
                double bx = (leg < 2) ? hl : -hl;
                double by = (leg % 2 == 0) ? -hw : hw;
                Eigen::Matrix4d T_base = homog_transform(bx, by, -l1, 0, 0, 0);
                Eigen::Matrix4d T_thigh_t = homog_transform(l2, 0, 0, 0, 0, 0);
                Eigen::Matrix4d T_calf_t = homog_transform(l3, 0, 0, 0, 0, 0);
                Eigen::Matrix4d T_foot = homog_transform(l4, 0, 0, 0, 0, 0);
                Eigen::Vector3d p = compute_leg_fk_chain(angle_cases[ci][0], angle_cases[ci][1], angle_cases[ci][2],
                                                         T_base, T_thigh_t, T_calf_t, T_foot);
                print_vec(p);
            }
            printf("]");
        }
        printf("]");
    } else if (test == "fk_all_legs") {
        double bl = 0.3762, bw = 0.0935, l1 = 0.0, l2 = 0.0955, l3 = 0.213, l4 = 0.213;
        std::vector<std::array<double, 12>> cases = {
            {0, 0.3, -0.6, 0, 0.3, -0.6, 0, 0.3, -0.6, 0, 0.3, -0.6},
            {0.1, -0.4, 0.3, -0.2, 0.5, -0.7, 0.4, -0.1, 0.2, -0.3, 0.6, -0.5}};
        ForwardKinematics fk(bl, bw, l1, l2, l3, l4);
        printf("[");
        for (size_t ci = 0; ci < cases.size(); ++ci) {
            if (ci) printf(",");
            std::vector<double> j(cases[ci].begin(), cases[ci].end());
            auto feet = fk.forward_kinematics_all_legs(j);
            printf("[");
            for (int leg = 0; leg < 4; ++leg) {
                if (leg) printf(",");
                print_vec(feet[leg]);
            }
            printf("]");
        }
        printf("]");
    } else if (test == "ik_leg") {
        double l1 = 0.0, l2 = 0.0955, l3 = 0.213, l4 = 0.213;
        // x,y,z для 4 ног (как test_ik.cpp + разнообразие)
        std::vector<std::array<double, 3>> targets = {
            {0.2, -0.12, -0.2}, {0.2, 0.12, -0.2}, {-0.2, -0.12, -0.2}, {-0.2, 0.12, -0.2},
            {0.25, -0.15, -0.25}, {0.18, 0.10, -0.3}, {-0.22, -0.13, -0.28}, {-0.19, 0.14, -0.22}};
        printf("[");
        for (size_t i = 0; i < targets.size(); ++i) {
            if (i) printf(",");
            int leg = i % 4;
            print_angles3(compute_joint_angles_for_leg(targets[i][0], targets[i][1], targets[i][2], leg, l1, l2, l3, l4));
        }
        printf("]");
    } else if (test == "local_positions" || test == "ik_all") {
        double bl = 0.3762, bw = 0.0935, l1 = 0.0, l2 = 0.0955, l3 = 0.213, l4 = 0.213;
        LegsMatrix lp;
        lp << 0.2081, 0.2081, -0.1881, -0.1881, -0.14225, 0.14225, -0.14225, 0.14225, -0.25, -0.25, -0.25, -0.25;
        InverseKinematics ik(bl, bw, l1, l2, l3, l4);
        printf("[");
        for (int ci = 0; ci < 3; ++ci) {
            if (ci) printf(",");
            double dx = ci == 1 ? 0.01 : 0.0;
            double dy = ci == 2 ? -0.02 : 0.0;
            double dz = ci == 1 ? 0.005 : 0.0;
            double roll = ci == 2 ? 0.03 : 0.0;
            double pitch = ci == 1 ? -0.02 : 0.0;
            double yaw = ci == 2 ? 0.04 : 0.0;
            if (test == "local_positions") {
                auto local = compute_local_positions(lp, bl, bw, dx, dy, dz, roll, pitch, yaw);
                print_local4x3(local);
            } else {
                print_arr12(ik.inverse_kinematics(lp, dx, dy, dz, roll, pitch, yaw));
            }
        }
        printf("]");
    }

    // ═══════════════ gait / controllers ═══════════════
    else if (test == "trot_gait_phases") {
        TrotGaitController trot(0.04, 0.18, 0.02, false, node_default_stance());
        printf("{\"ticks\":[%d,%d,%d],\"phases\":[", trot.stance_ticks(), trot.swing_ticks(), trot.phase_length());
        for (int t = 0; t < 44; ++t) {
            if (t) printf(",");
            printf("%d", trot.phase_index(t));
        }
        printf("],\"contacts\":[");
        for (int t = 0; t < 44; ++t) {
            if (t) printf(",");
            auto c = trot.contacts(t);
            printf("[%d,%d,%d,%d]", c(0), c(1), c(2), c(3));
        }
        printf("]}");
    } else if (test == "trot_stance_swing") {
        LegsMatrix st = node_default_stance();
        TrotStanceController stance(22, 2, 9, 0.02, 0.02);
        TrotSwingController swing(9, 0.02, 0.14, st, 22, 2);
        Eigen::Vector3d cmd(0.05, 0.02, 0.1);
        printf("{\"stance\":[");
        for (int leg = 0; leg < 4; ++leg) {
            if (leg) printf(",");
            print_vec(stance.next_foot_location(leg, st, cmd, -0.25));
        }
        printf("],\"pos_delta\":[");
        for (int leg = 0; leg < 4; ++leg) {
            if (leg) printf(",");
            print_vec(stance.position_delta(leg, st, cmd, -0.25));
        }
        printf("],\"swing\":[");
        for (int leg = 0; leg < 4; ++leg) {
            if (leg) printf(",");
            print_vec(swing.next_foot_location(0.4, leg, st, cmd, -0.25));
        }
        printf("],\"td\":[");
        for (int leg = 0; leg < 4; ++leg) {
            if (leg) printf(",");
            print_vec(swing.raibert_touchdown_location(leg, cmd));
        }
        printf("],\"h\":[");
        for (double p : {0.0, 0.25, 0.5, 0.75, 1.0}) {
            printf("%.17g,", swing.swing_height(p));
        }
        printf("0]}");
    } else if (test == "trot_gait_step") {
        TrotGaitController trot(0.04, 0.18, 0.02, false, node_default_stance());
        LegsMatrix cur = node_default_stance();
        Eigen::Vector3d cmd(0.05, 0.02, 0.1);
        printf("[");
        for (int t = 1; t <= 44; ++t) {
            if (t > 1) printf(",");
            cur = trot.step(t, cur, cmd, -0.25);
            print_legs(cur);
        }
        printf("]");
    } else if (test == "crawl_gait_phases") {
        CrawlGaitController crawl(0.55, 0.45, 0.02, node_default_stance());
        printf("{\"ticks\":[%d,%d,%d],\"phases\":[", crawl.stance_ticks(), crawl.swing_ticks(), crawl.phase_length());
        for (int t = 0; t < 196; ++t) {
            if (t) printf(",");
            printf("%d", crawl.phase_index(t));
        }
        printf("],\"contacts\":[");
        for (int t = 0; t < 196; ++t) {
            if (t) printf(",");
            auto c = crawl.contacts(t);
            printf("[%d,%d,%d,%d]", c(0), c(1), c(2), c(3));
        }
        printf("]}");
    } else if (test == "crawl_stance_swing") {
        LegsMatrix st = node_default_stance();
        CrawlStanceController stance(196, 27, 22, 0.02, 0.02, 0.06);
        CrawlSwingController swing(22, 0.02, 0.14, st, 196, 27, 0.06);
        Eigen::Vector3d cmd(0.01, 0.005, 0.05);
        printf("{\"stance\":[");
        for (int leg = 0; leg < 4; ++leg) {
            if (leg) printf(",");
            print_vec(stance.next_foot_location(leg, st, cmd, -0.25, true, true, leg == 0));
        }
        printf("],\"swing\":[");
        for (int leg = 0; leg < 4; ++leg) {
            if (leg) printf(",");
            print_vec(swing.next_foot_location(0.4, leg, st, cmd, -0.25));
        }
        printf("],\"td\":[");
        for (int leg = 0; leg < 4; ++leg) {
            if (leg) printf(",");
            print_vec(swing.raibert_touchdown_location(leg, cmd, false));
        }
        printf("],\"h\":[");
        for (double p : {0.0, 0.25, 0.5, 0.75, 1.0}) {
            printf("%.17g,", swing.swing_height(p));
        }
        printf("0]}");
    } else if (test == "crawl_runtime_step") {
        // Активный C++ runtime-путь (RobotControllerNode::step_crawl):
        //  - нулевая команда → lerp к default_stance (alpha = 0.1)
        //  - иначе stance через CrawlStanceController + swing через CrawlSwingController
        //  - first_cycle_ никогда не очищается (нода не вызывает CrawlGaitController::step)
        CrawlGaitController crawl(0.55, 0.45, 0.02, node_default_stance());
        LegsMatrix cur = node_default_stance();
        // Сначала цикл с командой (нога 0 в stance)
        printf("{\"with_cmd\":[");
        Eigen::Vector3d cmd(0.01, 0.0, 0.0);
        for (int t = 1; t <= 88; ++t) {
            if (t > 1) printf(",");
            Eigen::VectorXi contacts = crawl.contacts(t);
            int phase_idx = crawl.phase_index(t);
            LegsMatrix nf;
            for (int leg = 0; leg < 4; ++leg) {
                if (contacts(leg) == 1) {
                    bool move_sideways = (phase_idx == 0 || phase_idx == 4);
                    bool move_left = (phase_idx == 0);
                    nf.col(leg) = crawl.stance().next_foot_location(
                        leg, cur, cmd, -0.25, crawl.is_first_cycle(), move_sideways, move_left);
                } else {
                    int sub = crawl.subphase_ticks(t);
                    double sp = static_cast<double>(sub) / crawl.swing_ticks();
                    nf.col(leg) = crawl.swing().next_foot_location(sp, leg, cur, cmd, -0.25);
                }
            }
            cur = nf;
            print_legs(cur);
        }
        printf("],\"no_cmd\":[");
        for (int t = 1; t <= 10; ++t) {
            if (t > 1) printf(",");
            LegsMatrix result = node_default_stance();
            result.row(2).setConstant(-0.25);
            cur = cur * 0.9 + result * 0.1;
            print_legs(cur);
        }
        printf("]}");
    } else if (test == "rest_stand") {
        LegsMatrix st = node_default_stance();
        RestController rest(st);
        rest.set_use_imu(true);
        StandController stand(st);
        quadropted::State state(0.25);
        quadropted::Command cmd;
        cmd.robot_height = -0.25;
        // два вызова REST с ненулевым IMU (проверка PID-компенсации)
        printf("{\"rest1\":");
        state.imu_roll = 0.1;
        state.imu_pitch = -0.05;
        print_legs(rest.step(state, cmd));
        printf(",\"rest2\":");
        print_legs(rest.step(state, cmd));
        printf(",\"stand0\":");
        quadropted::Command cmd0;
        cmd0.robot_height = -0.25;
        print_legs(stand.run(state, cmd0));
        printf(",\"stand_move\":");
        quadropted::Command cmdm;
        cmdm.robot_height = -0.25;
        cmdm.velocity = {0.05, 0.0, 0.0};
        print_legs(stand.run(state, cmdm));
        printf(",\"body_pos\":[%.17g,%.17g,%.17g]}", state.body_local_position[0], state.body_local_position[1],
               state.body_local_position[2]);
    } else if (test == "pid") {
        PIDController pid(0.15, 0.02, 0.002);
        pid.reset(0.0);
        printf("[");
        double t = 0.02;
        for (int i = 0; i < 10; ++i, t += 0.02) {
            if (i) printf(",");
            // run(roll, pitch, time) — измеренные значения, desired = 0
            auto r = pid.run(0.1, -0.05, t);
            printf("[%.17g,%.17g]", r[0], r[1]);
        }
        printf("]");
    } else if (test == "odometry_update") {
        OdometryState st;
        st.filter_window_size = 14;
        st.linear_velocity_x = 0.1;
        st.linear_velocity_y = 0.0;
        st.foot_contacts[0] = true;
        st.foot_positions[0] = Eigen::Vector3d(0.20, -0.14, -0.25);
        printf("{\"x\":[");
        for (int i = 0; i < 50; ++i) {
            if (i) printf(",");
            st.foot_positions[0] += Eigen::Vector3d(0.002, 0.0, 0.0);
            update_odometry(st, 0.02, 0.65);
            printf("%.17g", st.x);
        }
        printf("],\"y\":[");
        // второй прогон с нулевого состояния для y (theta поворот)
        OdometryState st2;
        st2.filter_window_size = 14;
        st2.theta = 0.5;
        st2.foot_contacts[0] = true;
        st2.foot_positions[0] = Eigen::Vector3d(0.20, -0.14, -0.25);
        for (int i = 0; i < 50; ++i) {
            if (i) printf(",");
            st2.foot_positions[0] += Eigen::Vector3d(0.0, 0.002, 0.0);
            update_odometry(st2, 0.02, 0.65);
            printf("%.17g", st2.y);
        }
        printf("],\"stall\":");
        printf("%s}", st.is_stalled ? "true" : "false");
    } else {
        fprintf(stderr, "Unknown test: %s\n", test.c_str());
        return 1;
    }

    printf("}\n");
    return 0;
}
