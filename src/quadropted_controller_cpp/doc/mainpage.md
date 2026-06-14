# Quadropted Controller {#mainpage}

![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-green)
![C++](https://img.shields.io/badge/C++-20-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Development-orange)

A high-performance quadruped robot controller for ROS 2 Jazzy. Implements multiple gaits with inverse kinematics, PID stabilisation, and odometry estimation.

---

## Features

| Gait | Type | Speed | Stability |
|------|------|-------|-----------|
| **Trot** | Diagonal pairs | Fastest | Moderate |
| **Crawl** | One leg at a time | Slow | Highest |
| **Rest** | Static stance | — | Maximum |
| **Stand** | Static with body pose override | — | High |

### Key capabilities

- **Gait switching** — seamless online transitions between trot, crawl, rest, and stand
- **IMU-based PID stabilisation** — body roll/pitch compensation during stance
- **Raibert foot placement** — heuristic touchdown position for dynamic stability
- **Inverse Kinematics** — analytic IK solver for 3-DOF legs
- **Forward Kinematics** — full FK chain for odometry and validation
- **Odometry estimation** — foot-contact velocity integration with stall detection
- **Configurable parameters** — all gains, heights, and geometry tunable via YAML
- **Markers & TF** — RViz visualisation and coordinate frame publishing

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    RobotControllerNode                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────┐ │
│  │   Trot   │  │   Crawl   │  │   Rest   │  │    Stand    │ │
│  │  Gait    │  │   Gait    │  │  Ctrl    │  │   Ctrl      │ │
│  └────┬─────┘  └────┬──────┘  └────┬─────┘  └──────┬──────┘ │
│       └──────────────┴──────────────┴───────────────┘        │
│                              │                               │
│                     ┌────────┴────────┐                      │
│                     │ InverseKinematics│                     │
│                     └────────┬────────┘                      │
│                              │ joint positions               │
│                     ┌────────┴────────┐                      │
│                     │   Publishers    │                      │
│                     └─────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
                         ▲ IMU, velocity, mode
                         │
┌──────────────────────────────────────────────────────────────┐
│                     DogOdometryNode                           │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────────┐│
│  │  Forward   │  │  Odometry  │  │  TF / Marker Publishers ││
│  │ Kinematics │  │   State    │  │                         ││
│  └────────────┘  └────────────┘  └─────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## Classes

| Namespace | Class | Purpose |
|-----------|-------|---------|
| `quadropted::` | `State` | Robot state snapshot (foot positions, IMU, behaviour mode) |
| `quadropted::` | `Command` | High-level motion command (velocity, yaw, height) |
| `quadropted::` | `GaitController` | Base: stance/swing timing, contact-phase matrix |
| `quadropted::` | `TrotGaitController` | Trot gait (diagonal pairs) with Raibert + PID |
| `quadropted::` | `TrotStanceController` | Trot stance: foot delta computation |
| `quadropted::` | `TrotSwingController` | Trot swing: Raibert touchdown + swing trajectory |
| `quadropted::` | `CrawlGaitController` | Crawl gait (one leg at a time) |
| `quadropted::` | `CrawlStanceController` | Crawl stance with lateral body shift |
| `quadropted::` | `CrawlSwingController` | Crawl swing: Raibert + lateral offset |
| `quadropted::` | `RestController` | Static stance with PID stabilisation |
| `quadropted::` | `StandController` | Static stance with body-motion override |
| `quadropted::` | `PIDController` | 2-channel PID for roll/pitch compensation |
| `quadropted::` | `ForwardKinematics` | Joint angles → foot positions (FK) |
| `quadropted::` | `InverseKinematics` | Foot positions → joint angles (IK) |
| `quadropted::` | `OdometryState` | Odometry estimation from foot contact + IMU |
| `quadropted::` | `RobotControllerNode` | Main ROS 2 control node |
| `quadropted::` | `DogOdometryNode` | Odometry ROS 2 node |

---

## Gait Cycle

Each gait controller alternates between **stance** (foot on ground, body moves) and **swing** (foot lifted, moves to next target) phases:

```
Tick: 0   stance_ticks           phase_length
      ├─────────────────────┬───────────────┤
      │      STANCE         │    SWING      │
      └─────────────────────┴───────────────┘
```

- **Stance**: foot position is fixed in world frame; body moves relative to it
- **Swing**: foot traces a trajectory from liftoff to touchdown (Raibert heuristic)

---

## Quick Start

```bash
# Build
colcon build --packages-select quadropted_controller_cpp

# Run
ros2 launch quadropted_controller_cpp quadropted_controller_cpp.launch.py
```

### Parameters

All tunable parameters are in `config/robot_controller.yaml`:

```yaml
quadropted_controller_cpp:
  ros__parameters:
    # Heights (sit/stand/walk)
    sit_height: -0.15
    stand_height: 0.005
    walk_height: 0.0

    # Trot gait
    trot_stance_time: 0.25
    trot_swing_time: 0.15
    trot_height: 0.240

    # Crawl gait
    crawl_stance_time: 0.35
    crawl_swing_time: 0.25
    crawl_height: 0.240
```

---

## License

This project is licensed under the MIT License.
