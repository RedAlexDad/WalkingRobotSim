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

## Status

All known issues fixed. Ready for integration test:

```bash
docker compose up -d simulator    # start sim
docker compose --profile elevation up -d elevation_mapping   # start elevation + bridge
```

## Docs

- Full analysis: `reports/elevation-mapping/odometry-mismatch-analysis.md`
