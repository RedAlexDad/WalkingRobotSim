# Rust Controllers Migration Debug Report

## Context
- Project: `WalkingRobotSim`
- Scope: post-migration mismatch between C++ and Rust controller pipeline
- Main user symptom:
  - robot joints become rigid/saturated in Rust
  - robot does not walk in Rust
  - teleop-like control ineffective in Rust
  - mode switching appeared broken from user perspective
- Debug session: `f81059`

## Test Environment and Launch Notes
- `make deploy` used for rebuild/redeploy.
- `make gazebo-rust` / `make gazebo-cpp` fail in this execution environment due to `docker exec -it` without interactive TTY.
- Equivalent runtime launch used for both stacks:
  - Rust: `ros2 launch gazebo_sim launch_rust.launch.py`
  - C++: `ros2 launch gazebo_sim launch_cpp.launch.py`
  - executed via `docker exec ... bash -lc` (without `-it`), same container `walking_robot_sim`.

## Reproduction Matrix
### Rust stack (`launch_rust`)
- Published mode and velocity to namespaced topics:
  - `/robot1/robot_mode`
  - `/robot1/robot_velocity`
- Observed:
  - mode switching logs are present (`TROT -> CRAWL -> STAND -> REST`)
  - in `CRAWL`, joint angles frequently collapse to limits:
    - hip: `-0.300000`
    - upper: `0.500000`
    - lower: `-2.800000`
  - even with non-zero `vx`, CRAWL quickly converges to saturated posture.

### C++ stack (`launch_cpp`)
- Published mode and teleop-equivalent velocity:
  - `/robot1/robot_mode` with `CRAWL`
  - `/robot1/cmd_vel` with forward `linear.x`
- Observed:
  - mode switching works
  - CRAWL phase advances with expected contact changes (`[1,0,1,1]`, `[1,1,0,1]`, etc.)
  - joint angles remain dynamic (no hard lock to limits)
  - velocity command reaches controller (`vx=0.0110` logged in C++).

## Hypotheses and Status
1. **H1_CONTACT_PHASE_LAYOUT**  
   **Status:** INCONCLUSIVE (partially aligned, needs deeper per-tick parity dump).  
   **Evidence:** contacts/subphase are produced and logged; gross phase progression exists.

2. **H2_VELOCITY_MAPPING_LOSS**  
   **Status:** PARTIALLY CONFIRMED then PARTIALLY FIXED.  
   **Root issue:** Rust node compressed command into 3-vector with loss of components for non-gait states.  
   **Action taken:** split into `cmd_linear[3]` + `cmd_angular[3]`; use `[lin.x, lin.y, ang.z]` only for gait APIs.

3. **H3_CRAWL_STANCE_PATH_MISMATCH**  
   **Status:** CONFIRMED.  
   **Root issue:** Rust crawl stance branch used simplified behavior (`copy_current`) instead of controller-driven stance update used by active C++ node path.  
   **Action taken:** switched Rust stance branch to `CrawlStanceController::next_foot_location(...)` with phase-dependent sideways logic.

4. **H4_STATE_TRANSITION_RESET**  
   **Status:** REJECTED as primary blocker.  
   **Evidence:** mode transitions and reset events are visible in runtime logs; transitions do occur.

5. **H5_IK_INPUT_DRIFT**  
   **Status:** CONFIRMED as major downstream symptom.  
   **Evidence:** in Rust CRAWL, IK output repeatedly reaches same hard limits across legs; in C++ under comparable commands this does not happen.

## Code Changes Applied During Debug
### `src/quadropted_controller_rust/quadropted-nodes/src/bin/robot_controller_node.rs`
- Improved `robot_mode` parsing robustness (trim + NUL-safe handling).
- Added explicit handling/logging for unknown mode strings.
- Reworked velocity representation:
  - from single compressed vector to
    - `cmd_linear = [x, y, z]`
    - `cmd_angular = [x, y, z]`
- Gait commands now explicitly map to `[linear.x, linear.y, angular.z]`.
- `STAND` path now receives full linear/angular vectors.

### `src/quadropted_controller_rust/quadropted-core/src/controllers/crawl/swing.rs`
- Added `robot_height` parameter into swing computation.
- Corrected swing Z composition to include robot height offset (`swing_h + robot_height`), preventing foot-Z drift toward unrealistic IK inputs.

### `src/quadropted_controller_rust/quadropted-core/src/controllers/crawl/gait.rs`
- `step(...)` signature extended with `robot_height`.
- Swing call updated to pass `robot_height`.
- Stance path replaced with active stance controller call (phase-aware sideways behavior), instead of static copy.

## What Is Fixed vs Not Fixed
### Fixed / Verified
- Mode transitions are not fundamentally broken in Rust runtime.
- Velocity mapping in node is improved and closer to C++ semantics.
- CRAWL pipeline no longer uses trivial stance copy.

### Still Failing
- Rust CRAWL still reaches repeated IK saturation pattern under motion (`-0.3 / 0.5 / -2.8`), unlike C++.
- Primary unresolved issue remains in Rust CRAWL trajectory parity vs C++ runtime path.

## Most Likely Remaining Root Causes
1. Residual mismatch in CRAWL stance/swing trajectory details vs active C++ node implementation (not only library-level `crawl_gait.cpp`).
2. Phase-conditioned lateral shift semantics still not fully aligned end-to-end.
3. Potential remaining mismatch in pre-IK foot frame construction during CRAWL transitions.

## Next Debug Actions (Recommended)
1. Add side-by-side runtime dump (`per tick`) of:
   - phase index
   - contacts
   - foot locations per leg before IK
   - resulting first leg joint triple
   for both C++ and Rust under identical injected commands.
2. Build deterministic replay scenario:
   - force fixed mode (`CRAWL`)
   - fixed command (`vx`, `vy`, `yaw`)
   - fixed initial stance
   - compare first 300 ticks.
3. Align Rust CRAWL implementation strictly to active C++ node path (not only shared library assumptions), then re-run Gazebo validation.

## Current Conclusion
- Infrastructure (Gazebo/container/nav stack) is not the blocker.
- C++ stack remains healthy and demonstrates expected walking behavior with mode changes and teleop-equivalent commands.
- Rust stack has a narrowed, reproducible CRAWL control-path defect leading to IK saturation and apparent “rigid joints”.
- Further work should focus on exact CRAWL foot-trajectory parity against C++ runtime outputs.
