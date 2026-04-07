#!/usr/bin/env python3
"""
Benchmark производительности — замер времени выполнения Python функций.
Запускается отдельно от C++ бенчмарка.

Запуск:
    cd /home/redalexdad/GitHub/WalkingRobotSim
    python3 src/tests/benchmark_performance.py
    make test-benchmark
"""

import os
import sys
import timeit

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_SCRIPTS = os.path.abspath(
    os.path.join(TESTS_DIR, "..", "quadropted_controller", "scripts")
)

ITERATIONS = 5000


def benchmark_python():
    """Замерить время Python функций."""
    sys.path.insert(0, PYTHON_SCRIPTS)
    from ForwardKinematics.forward_kinematics import ForwardKinematics
    from RoboticsUtilities.rotation_matrices import rotxyz
    from RoboticsUtilities.homogeneous_transforms import (
        homog_transform,
        homog_transform_inverse,
    )
    from InverseKinematics.local_positions import compute_local_positions
    from InverseKinematics.joint_angles import compute_all_joint_angles
    from QuadrupedOdometry.odometry_state import OdometryState
    from QuadrupedOdometry.odometry_update import update_odometry

    import importlib.util

    def _load(rel):
        p = os.path.join(PYTHON_SCRIPTS, rel)
        spec = importlib.util.spec_from_file_location("m", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    GaitController = _load("RobotController/GaitController.py").GaitController
    import numpy as np

    fk = ForwardKinematics([0.3762, 0.0935], [0.0, 0.0955, 0.213, 0.213])
    angles = [0, 0.3, -0.6] * 4
    positions = [
        [0.2, -0.12, -0.2],
        [0.2, 0.12, -0.2],
        [-0.2, -0.12, -0.2],
        [-0.2, 0.12, -0.2],
    ]
    lp = np.array([[0.2, 0.2, -0.2, -0.2], [-0.1, 0.1, -0.1, 0.1], [0, 0, 0, 0]])
    cp = np.array([[1, 1, 1, 0], [1, 0, 1, 1], [1, 0, 1, 1], [1, 1, 1, 0]])
    gc = GaitController(0.04, 0.18, 0.02, cp, np.zeros((3, 4)))

    state = OdometryState()
    state.linear_velocity_x = 0.02
    state.linear_velocity_y = 0.01
    state.theta = 0.1
    state.foot_contacts = [False] * 4

    results = {}

    t = timeit.timeit(lambda: rotxyz(0.1, -0.05, 0.02), number=ITERATIONS)
    results["rotxyz"] = t / ITERATIONS * 1000

    def ht_test():
        m = homog_transform(0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
        return homog_transform_inverse(m.copy())

    t = timeit.timeit(ht_test, number=ITERATIONS)
    results["homog_transform_inverse"] = t / ITERATIONS * 1000

    t = timeit.timeit(lambda: fk.forward_kinematics_all_legs(angles), number=ITERATIONS)
    results["FK"] = t / ITERATIONS * 1000

    t = timeit.timeit(
        lambda: compute_all_joint_angles(positions, 0.0, 0.0955, 0.213, 0.213),
        number=ITERATIONS,
    )
    results["IK"] = t / ITERATIONS * 1000

    t = timeit.timeit(
        lambda: compute_local_positions(lp, 0.3762, 0.0935, 0.01, 0, 0, 0, 0, 0),
        number=ITERATIONS,
    )
    results["local_positions"] = t / ITERATIONS * 1000

    t = timeit.timeit(lambda: gc.phase_ticks, number=ITERATIONS)
    results["GaitController.phase_ticks"] = t / ITERATIONS * 1000

    def odometry_test():
        s = OdometryState()
        s.linear_velocity_x = 0.02
        s.linear_velocity_y = 0.01
        s.theta = 0.1
        s.foot_contacts = [False] * 4
        update_odometry(s, 0.02)

    t = timeit.timeit(odometry_test, number=ITERATIONS)
    results["update_odometry"] = t / ITERATIONS * 1000

    return results


def main():
    print("=" * 70)
    print(f"Python Benchmark ({ITERATIONS} итераций)")
    print("=" * 70)

    results = benchmark_python()

    print()
    print(f"{'Функция':<35} {'Время (мс)':>15}")
    print("-" * 52)

    total = 0
    for func, ms in sorted(results.items(), key=lambda x: x[1]):
        print(f"{func:<35} {ms:>15.4f}")
        total += ms

    print("-" * 52)
    print(f"{'ИТОГО':<35} {total:>15.4f}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
