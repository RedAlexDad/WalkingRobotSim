# Odometry Drift — Session 27 May 2026

## Problem

Go2 robot base_link drifts ~2.82 m in X and ~-4.09 m in Y during TROT at standing start
(Gazebo simulation). Three root causes identified.

## Changes

### Phase A — map→odom static transform removed

**File:** `compose.yml:54`  
Deleted `static_transform_publisher 0 0 0 0 0 0 map odom`. AMCL now dynamically corrects
map→odom instead of it being locked to zero.

### Phase B — nav2 StaticLayer QoS verified

`map_subscribe_transient_local: true` → subscriber uses `RELIABLE + TRANSIENT_LOCAL`.
Bridge publishes `/map` with same profile. No mismatch.

### Phase C — Stall detection (C++ only)

Already present in `quadruped_controller_cpp` (Phase 2 in full report). Detects stuck via
`delta_mag > 0.0001 AND |imu_angular_vel| < 0.05 → freeze odometry integration`.
Only works for TROT, not REST (delta ≈ 0).

### Phase D — Foot friction increased

**File:** `src/go2_description/xacro/gazebo.xacro`  
All 4 foot links: `mu1=0.6→1.0, mu2=0.6→1.0`. Ground plane has mu=50. Limiting factor was
foot coefficient — rubber-on-concrete equivalent is ~1.0.

### Phase E — Bridge subscriber QoS made explicit

**File:** `elevation_mapping_cupy/.../scripts/elevation_to_costmap_node.py`

- Subscriber QoS set explicitly to `RELIABLE + VOLATILE` (was implicit via integer `10`)
- Added 5 s watchdog timer: warns if no elevation map data received
- Added first-message diagnostic log (frame, layers, shape)

### Phase F — Cost layer inverted (steep slopes blue = free)

**Problem:** Elevation costmap showed steep slopes as traversable (blue) because the cost
layer from `elevation_mapping` is a _traversability_ cost (higher = more traversable), but
the bridge treated it as _obstacle_ cost (higher = obstacle).

Flat ground (cost ≈ 1.0) → occupied (red). Steep slope (cost ≈ 0.2) → free (blue).

**Fix:** Added `invert_cost=True` parameter (default `true`) to bridge node. Logic flipped:

```
cost ≥ 0.7 → FREE   (flat ground, gentle slopes)
cost ≤ 0.5 → OCCUPIED (steep slopes, rough terrain)
```

**File:** `elevation_mapping_cupy/.../scripts/elevation_to_costmap_node.py`

- New ROS2 parameter `invert_cost` (default `true`)
- When enabled, thresholds are mirrored via `1.0 - threshold`
- Flat ground (cost ~1.0) now correctly maps to FREE
- Steep slopes + roughness (cost ≤ 0.5) map to OCCUPIED

## Status

All known issues fixed. Ready for integration test.

## Smart Deploy

`make deploy` now calls `scripts/smart-deploy.sh` in `auto` mode. It checks `git diff` against `.last_build_commit` and classifies changes:

| Changed files | Action |
|---|---|
| `src/*.cpp .hpp .h CMakeLists.txt package.xml` | **rebuild** main image |
| `elevation_mapping_cupy/*` | **rebuild** elevation image |
| `compose.yml Dockerfile` | **rebuild** main image |
| `src/*.py .yaml .launch.py .rviz` | **skip** (bind-mount `project_src`) |
| Everything else | **rebuild** (conservative) |

Usage: `make deploy` (auto), `make deploy --build` (force), `make deploy --check` (diagnostic only). `.last_build_commit` is updated after a successful build. `make build` and `make up` remain as separate commands for manual use.

Remaining tuning:

- `max_slope` (0.8 → ~0.35) and `max_roughness` (0.1 → ~0.05) may need reduction for more aggressive obstacle detection
- Frame shift fix (7.4) still open — elevation map may need republishing in `map` frame

```bash
docker compose up -d simulator    # start sim
docker compose --profile elevation up -d elevation_mapping   # start elevation + bridge
```

## Docs

- Full analysis: `reports/elevation-mapping/odometry-mismatch-analysis.md`
