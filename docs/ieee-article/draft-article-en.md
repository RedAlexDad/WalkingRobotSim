# Comparing a Learned Policy and a Model-Based IK/TROT Controller for Quadruped Locomotion in Isaac Sim

**Authors:** A. V. Papin, *et al.*
**Affiliation:** Bauman Moscow State Technical University, Moscow, Russia

---

## Abstract

Quadruped robots are increasingly used in inspection, logistics, and
search-and-rescue, and their development relies heavily on physics
simulation. We compare two fundamentally different locomotion-control
paradigms for the Unitree Go2 quadruped: a pre-trained
reinforcement-learning (RL) policy distributed with NVIDIA Isaac Sim, and a
classical model-based controller that implements a TROT gait generator with
analytic inverse kinematics (IK), written in Rust and integrated through
ROS 2. Both controllers drive the robot through the same low-level
joint-position interface, emulating the robot's native low-level mode.
Experiments in Isaac Sim 6.0 with IsaacLab 3.0, with three runs per
controller at a commanded speed of 0.3 m/s, show that both paradigms walk
at comparable speed (model-based 0.215 m/s, RL 0.231 m/s) and comparable
cost of transport (2.83 vs 2.84). The RL policy is markedly more stable
(maximum roll 2.3° vs 27.8°, lateral drift 0.37 m vs 1.09 m) and tracks
the commanded velocity over the full range 0.1–0.4 m/s, whereas the
model-based controller is stable only near 0.3 m/s. Conversely, the
model-based controller holds body height more tightly (standard deviation
0.025 m vs 0.040 m) and is fully deterministic, requiring no GPU training
and no learned weights. We also report five concrete integration defects
found and fixed in the model-based controller, and show that it was
unpredictably coupled to real time, while the RL policy is not. The
model-based controller is therefore a transparent baseline and a reliable
fallback.

**Index Terms** — quadruped robot, Isaac Sim, inverse kinematics, TROT
gait, reinforcement learning, locomotion control, ROS 2.

---

## 1. Introduction

Legged robots are attractive where wheeled platforms are ineffective:
inspection of unstructured environments, search and rescue, logistics, and
operation on rough or discontinuous terrain. Among commercially available
quadrupeds, the Unitree Go2 is widely used in research because of its open
low-level control interface, its SDK, and the availability of simulation
assets. Developing and validating locomotion controllers requires physics
simulation; NVIDIA Isaac Sim and IsaacLab have become a de-facto standard
for GPU-accelerated training and testing of legged robots.

Two fundamentally different paradigms are used to control walking. The
first is **learned policies**: a neural network maps observations to joint
commands. Such policies are flexible and can handle complex terrain, but
they require GPU training, behave as a black box, generalize poorly outside
the training distribution, and do not always recover after a fall. The
second is **model-based control**: deterministic algorithms that combine a
gait generator with inverse kinematics, often with an inertial
attitude-compensation loop. Model-based controllers are transparent,
interpretable, and can run on a CPU, but they are less adaptive to
unexpected disturbances.

Despite the practical importance of choosing between these paradigms,
direct comparisons in a single simulator, on a single robot, and through a
single interface remain rare. The closest work compares model-predictive
control (MPC) and RL in MuJoCo on the Unitree Go1. Our work differs in
three ways: the model-based controller is an analytic IK/TROT controller
(not MPC), the environment is Isaac Sim / IsaacLab (not MuJoCo), and the
robot is the Unitree Go2 with the official NVIDIA RL policy.

The contributions of this paper are:
1. the implementation of a model-based IK/TROT controller in Rust and its
   integration with Isaac Sim through IsaacLab and ROS 2;
2. a direct comparison against the official NVIDIA RL policy on a single
   asset and through one low-level joint interface;
3. a set of practical integration patterns (joint re-mapping, angle
   convention calibration, amplitude limiting, and time-base correction);
4. a quantitative evaluation of stability, body height, speed, lateral
   drift, energy, and the operating range of both paradigms;
5. a reproducible finding that the model-based controller was coupled to
   real time, whereas the learned policy was not.

## 2. Related Work

**RL for quadrupeds in Isaac.** Isaac Gym provides GPU-accelerated physics
and training, running tens of thousands of environments in parallel and
accelerating training by two to three orders of magnitude compared with
CPU simulators. Policies for Ant, ANYmal, and humanoid robots have been
trained on this stack. For the Go2, NVIDIA distributes a pre-trained policy
used here as the RL baseline.

**Comparison of RL and model-based control.** Prior work compares MPC and
RL on the Unitree Go1 in MuJoCo. RL achieves a shorter settling time and a
lower cost of transport, but generalizes worse and does not recover after a
fall, while MPC distributes effort across joints and recovers. That study
leaves open the comparison of RL with an analytic IK/TROT controller in
Isaac Sim — the subject of this paper.

**Sim-to-real RL for quadrupeds.** Another line of work trains an RL policy
for the Go1 in Isaac Sim / IsaacLab with domain randomization and transfers
it to hardware. The comparison there is against the built-in controller of
the Go1; we compare against the official NVIDIA policy on the Go2.

**Data and platform.** Kine2Go provides a kinematic dataset for the Go2
(800 trajectories, 40 RL policies, Genesis engine) for policy training. It
confirms the popularity of the Go2 as a research platform but does not
compare against a model-based controller.

**Positioning.** In contrast to the above, we use a deterministic IK/TROT
controller in Rust (not MPC and not a built-in controller), compare it with
the official NVIDIA RL policy for the Go2, and do so in a single
environment (Isaac Sim 6.0 / IsaacLab 3.0) on a single asset, through the
same low-level joint interface.

## 3. System Architecture

The system consists of a Rust controller running in a container, a ROS 2
bridge, and the IsaacLab environment:

```mermaid
graph LR
    RC["Rust controller<br/>(container, ROS 2)"] --> ROS["ROS 2 Jazzy<br/>/robot1/joint_group_controller/commands"]
    ROS --> IS["IsaacLab 3.0<br/>ManagerBasedEnv"]
    IS --> SIM["Isaac Sim 6.0<br/>PhysX (GPU)"]
    SIM --> GO2["Unitree Go2"]
```

The controller publishes twelve joint-position targets as a
`std_msgs/Float64MultiArray`. IsaacLab applies them through position
actuators with a proportional–derivative law, emulating the low-level mode
of the real robot. The RL path uses the same asset and the same
joint-position interface; the policy is a TorchScript model executed inside
the simulator.

## 4. Method

### 4.1. Robot and actuation

The Unitree Go2 has twelve actuated joints: four legs (front-right,
front-left, rear-right, rear-left), each with a hip (ab/adduction), a
thigh, and a calf joint. Control is performed through target joint
positions and a PD law; the model-based controller uses stiffness 75 and
damping 0.5, while the NVIDIA policy uses stiffness 25 and damping 0.5, as
specified by its environment configuration. The asset and physics
parameters are identical for both controllers except for these gains.

### 4.2. Model-based IK/TROT controller

The controller is a finite-state machine with REST, STAND, and TROT
states. The TROT generator drives two diagonal pairs in antiphase
(FR–RL and FL–RR) with stance and swing phases and a double-support phase.
Foot trajectories are generated in the body frame: during stance the foot
is fixed in the world and therefore moves backwards in the body frame at
the commanded velocity; during swing a Raibert-style heuristic places the
foot at the neutral point shifted by the velocity. The foot positions are
converted to joint angles by an analytic inverse-kinematics solution using
the Go2 link lengths (thigh and calf 0.213 m).

An attitude-compensation loop uses the IMU orientation to keep the feet
level: the pitch error is compensated by rotating the feet about the
lateral axis, and the roll error by a differential leg-length adjustment,
which avoids driving the hip joints into saturation. A proportional
yaw-stabilization term keeps the heading fixed.

### 4.3. Learned RL policy

The RL baseline is the pre-trained NVIDIA policy distributed with Isaac
Sim. Its observation is a 48-dimensional vector (base linear and angular
velocity in the body frame, gravity direction, commanded velocities, joint
position error from the default, joint velocities, and the previous
action). The policy outputs twelve actions at a decimated rate, which are
converted to joint-position targets. The policy is executed step-by-step,
so its behavior does not depend on wall-clock time.

### 4.4. Integration and calibration

Several practical steps were required for integration: re-mapping the joint
order between the controller and the asset, calibrating the angle
convention against a reference stance, limiting joint amplitudes for
stability, and launching a long-lived process with a stable ROS 2 spin.

### 4.5. Practical problems and their solutions

Five concrete defects were found and fixed, each confirmed by telemetry
(125 columns: pose, angles, velocities, torques, foot positions and
contacts):

1. **Stance foot drift.** The stance foot velocity was computed as
   `-(step_dist/4)/(dt·stance_ticks)`, where `stance_ticks` is the length
   of one stance phase, whereas the leg is on the ground for several phases
   in a row. The foot drifted backwards (up to −1.2 m) and the IK saturated
   (`calf = 0`). It was replaced by the physically correct
   `velocity = -cmd_vel` (the foot is fixed in the world).
2. **IMU compensation accumulation.** The compensation was applied
   incrementally to the gait state, so the tilt accumulated. It is now
   applied only to the copy used for IK.
3. **Inverted IMU sign.** The compensation used `R(-comp)` instead of
   `R(comp)`, amplifying the tilt. After correction, roll dropped from a
   full flip (180°) to about 8°.
4. **Inverted yaw sign.** The yaw stabilization used `-0.5·yaw_err`, which
   spun the robot up (yaw oscillating over ±180°). With `+0.5·yaw_err` the
   heading is maintained.
5. **Wall-clock PID.** After switching the controller to a simulation-time
   step, the PID still used wall-clock `dt`, causing a mismatch in the
   integral and derivative terms.

In addition, a structural defect was identified: compensating the roll by
rotating the feet created a positive feedback loop through the hip joints
(fig. 1a). The roll is now compensated by a differential leg length, which
does not actuate the hip; the roll dropped from 50° to about 8° (fig. 1b).

## 5. Experiments and Results

### 5.1. Setup

The simulator is Isaac Sim 6.0.1 with IsaacLab 3.0 on an Ubuntu 26.04
workstation with an NVIDIA RTX 5070 Ti GPU. The terrain is a flat plane
with a friction coefficient of 1.0. The robot is the Unitree Go2 with the
IsaacLab asset. The commanded velocity is 0.3 m/s (with a speed sweep from
0.1 to 0.4 m/s). Each controller was run three times; telemetry was
recorded at the physics rate.

### 5.2. Metrics

We report the distance travelled, mean speed, mean and standard deviation
of body height, maximum roll and pitch, lateral drift, cost of transport
(CoT), and the time to reach a steady gait.

### 5.3. Results

**Table 1. Forward walking (vx = 0.3 m/s, mean ± std, n = 3).**

| Metric | RL policy (NVIDIA) | IK/TROT (ours) |
|---|---|---|
| Mean body height (m) | 0.159 ± 0.000 | 0.235 ± 0.001 |
| Std of height (m) | 0.040 ± 0.000 | 0.025 ± 0.001 |
| Mean speed (m/s) | 0.231 ± 0.000 | 0.215 ± 0.012 |
| Distance (m) | 3.34 ± 0.00 (15 s) | 2.75 ± 0.12 (19.3 s) |
| Lateral drift (m) | 0.37 ± 0.00 | 1.09 ± 0.16 |
| Max roll (deg) | 2.3 ± 0.0 | 27.8 ± 3.7 |
| Max pitch (deg) | 4.1 ± 0.0 | 35.6 ± 0.0 * |
| Falls | none | none |
| CoT | 2.84 | 2.83 ± 0.41 |

\* the IK pitch maximum is a startup transient as the robot settles from
the spawn height; the steady-state pitch is about 2°.

The RL policy is deterministic across runs (standard deviation zero),
because the simulator is deterministic. The model-based controller is
also deterministic in principle, but its behavior was sensitive to the
simulation rate before the time-base correction.

**Operating range (Table 2).** The RL policy tracks the commanded velocity
over the whole range 0.1–0.4 m/s with a small roll (2–4°). The model-based
controller is stable only near 0.3 m/s; at 0.1, 0.2, and 0.4 m/s the roll
reaches 47–69° and the robot falls.

| vx (m/s) | RL: speed / roll / drift | IK: speed / roll / drift |
|---|---|---|
| 0.1 | 0.026 / 2.6° / 0.09 m | 0.001 / 69° / 0.28 m |
| 0.2 | 0.116 / 3.6° / 0.21 m | 0.024 / 47° / 0.23 m |
| 0.3 | 0.222 / 2.3° / 0.37 m | 0.141 / 25° / 0.77 m |
| 0.4 | 0.344 / 3.0° / 0.80 m | 0.066 / 31° / 0.60 m |

## 6. Discussion

The two paradigms trade off differently. The learned policy is markedly
more stable, keeps the course, and works over a wide speed range; it is
the natural choice when a trained policy is available and a GPU is present.
The model-based controller is fully deterministic, transparent, requires no
GPU or training, and holds the body height more tightly, but it is stable
only in a narrow regime and has a residual roll and drift.

A key observation concerns **time-base coupling**. Before correction, the
model-based controller ran its 60 Hz loop on wall-clock time while the
simulation advanced by fixed steps; when the simulation slowed down (for
example, because of heavier logging), the number of physics steps per
control command changed, and the robot's behavior changed with it. After
switching the controller to simulation time, the behavior became
deterministic. The learned policy, being step-based, never had this
problem. This is a practical argument in favor of step-based interfaces for
model-based controllers.

A second observation concerns the **limit of a simple attitude
stabilizer**. The residual roll of the model-based controller is not an
implementation defect but a reproducible limit: increasing the gain,
relaxing the hip limit, or inverting the compensation sign all degrade
stability, and only a differential leg-length compensation (which avoids
the hip) reduced the roll substantially. Full elimination requires a
capture-point or turning controller that plans foot placement with respect
to the body velocity and yaw error.

**Limitations.** The study is simulation-only; sim-to-real was not
verified. The two controllers use different assets and PD gains, so part
of the difference may be attributable to these rather than to the control
paradigm; the qualitative conclusions (roll, drift, determinism) do not
depend on this. The model-based controller's operating range is narrow. The
RL policy is a ready-made NVIDIA model and was not trained by us.

## 7. Conclusion

We implemented and compared a model-based IK/TROT controller (Rust, ROS 2)
with the pre-trained NVIDIA RL policy for the Unitree Go2 in Isaac Sim
through a single low-level joint interface. At comparable speed (0.215 vs
0.231 m/s) and comparable cost of transport (2.83 vs 2.84), the learned
policy is more stable (roll 2.3° vs 27.8°, drift 0.37 vs 1.09 m) and works
over the full range 0.1–0.4 m/s, whereas the model-based controller is
stable only near 0.3 m/s.

The key conclusion is that the residual roll of the model-based controller
is not an implementation defect but a reproducible limit of a simple
proportional attitude stabilizer: increasing the gain, relaxing the hip
limit, and inverting the compensation sign all degrade stability, and only
a differential leg-length compensation reduces the roll. This turns a
limitation into a result about the applicability of the model-based
approach and points to the next step (a capture-point / turning
controller). The model-based controller remains a transparent,
deterministic, training-free baseline and a reliable fallback for hybrid
policy-plus-fallback architectures.

---

## References

1. M. H. Raibert, *Legged Robots That Balance*. Cambridge, MA, USA: MIT Press, 1986.
2. B. Katz, J. Di Carlo, and S. Kim, "Mini Cheetah: A platform for pushing the limits of dynamic quadruped control," in *Proc. IEEE Int. Conf. Robotics and Automation (ICRA)*, 2019, pp. 6295–6301.
3. J. Hwangbo et al., "Learning agile and dynamic motor skills for legged robots," *Science Robotics*, vol. 4, no. 26, 2019.
4. J. Lee, J. Hwangbo, L. Sentis, V. Kim, and P. Fankhauser, "Learning quadrupedal locomotion over challenging terrain," *Science Robotics*, vol. 5, no. 47, 2020.
5. T. Miki et al., "Learning robust perceptive locomotion for quadrupedal robots in the wild," *Science Robotics*, vol. 7, no. 62, 2022.
6. N. Rudin, D. Hoeller, P. Reist, and M. Hutter, "Learning to walk in minutes using massively parallel deep reinforcement learning," in *Proc. Conf. Robot Learning (CoRL)*, 2021.
7. J. M. Jimeno, "CHAMP: Controller for highly agile multi-legged platforms," GitHub repository, 2021.
8. NVIDIA, "Isaac Gym: High performance GPU-based physics simulation for robot learning," arXiv:2108.10470, 2021.
9. NVIDIA, "Isaac Lab: A unified and modular framework for robot learning," documentation, 2024.
10. NVIDIA, "Isaac Sim," documentation, 2026.
11. Unitree Robotics, "Unitree Go2 — quadruped robot and SDK," documentation, 2024.
12. *Benchmarking MPC and RL for legged robot locomotion in MuJoCo*, arXiv:2501.16590, 2025.
13. *Kine2Go: A kinematic dataset for the Unitree Go2*, arXiv:2606.14433, 2026.
14. *Isaac Sim-to-real: RL-based locomotion for quadrupeds*, arXiv:2607.18135, 2026.
15. G. Bledt et al., "MIT Cheetah 3: Design and control of a robust, dynamic quadruped robot," in *Proc. IEEE/RSJ Int. Conf. Intelligent Robots and Systems (IROS)*, 2018, pp. 2245–2252.
