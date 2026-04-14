//! Trot Gait Controller — Orchestrates trot stance and swing
//!
//! Direct translation from C++ `trot_gait.cpp`.

use super::stance::TrotStanceController;
use super::swing::TrotSwingController;
use crate::controllers::gait::GaitController;
use crate::controllers::pid::PIDController;
use nalgebra::{DMatrix, SMatrix};
use std::fs::OpenOptions;
use std::io::Write;
use std::sync::atomic::{AtomicU64, Ordering};

// #region agent log
static LOG_SEQ_TROT: AtomicU64 = AtomicU64::new(0);
const DEBUG_LOG_PATH: &str = "/home/redalexdad/GitHub/WalkingRobotSim/.cursor/debug-f81059.log";

fn dbg_log_trot(run_id: &str, hypothesis_id: &str, location: &str, message: &str, data: &str) {
    let seq = LOG_SEQ_TROT.fetch_add(1, Ordering::Relaxed);
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let line = format!(
        "{{\"sessionId\":\"f81059\",\"id\":\"f81059-trot-{}\",\"timestamp\":{},\"location\":\"{}\",\"message\":\"{}\",\"data\":{},\"runId\":\"{}\",\"hypothesisId\":\"{}\"}}",
        seq, ts, location, message, data, run_id, hypothesis_id
    );
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(DEBUG_LOG_PATH) {
        let _ = writeln!(f, "{}", line);
    }
}
// #endregion

/// Trot Gait Controller
pub struct TrotGaitController {
    gait: GaitController,
    use_imu: bool,
    swing_: TrotSwingController,
    stance_: TrotStanceController,
    pid_: PIDController,
}

impl TrotGaitController {
    pub fn new(
        stance_time: f64,
        swing_time: f64,
        time_step: f64,
        use_imu: bool,
        default_stance: SMatrix<f64, 3, 4>,
    ) -> Self {
        let gait = GaitController::new(
            stance_time,
            swing_time,
            time_step,
            // Trot contact schedule: [1,0,0,1] for diagonal pairs
            // Phase 0: FR,RL stance (FL,RR swing)
            // Phase 1: double support
            // Phase 2: FL,RR stance (FR,RL swing)
            // Phase 3: double support
            DMatrix::from_row_slice(4, 4, &[
                1, 1, 1, 0,  // FR
                1, 0, 1, 1,  // FL
                1, 0, 1, 1,  // RR
                1, 1, 1, 0,  // RL
            ]),
            default_stance,
        );

        let swing_ = TrotSwingController::new(
            gait.swing_ticks,
            time_step,
            0.14,  // z_leg_lift
            gait.default_stance.clone(),
            gait.phase_length,
            gait.stance_ticks,
        );

        let stance_ = TrotStanceController::new(
            gait.phase_length,
            gait.stance_ticks,
            gait.swing_ticks,
            time_step,
            0.02,  // z_error_constant
        );

        let pid_ = PIDController::new(0.15, 0.02, 0.002);

        Self { gait, use_imu, swing_, stance_, pid_ }
    }

    /// Step the gait controller for one tick
    /// Returns new foot positions (3x4 matrix)
    pub fn step(
        &self,
        ticks: i32,
        current: &SMatrix<f64, 3, 4>,
        cmd_vel: &[f64; 3],
        robot_height: f64,
    ) -> SMatrix<f64, 3, 4> {
        let mut next = *current;
        let contacts = self.gait.contacts(ticks);
        let sub = self.gait.subphase_ticks(ticks);
        // #region agent log
        if ticks <= 24 || ticks % 120 == 0 {
            dbg_log_trot(
                "pre-fix",
                "H1_CONTACT_PHASE_LAYOUT",
                "trot/gait.rs:step_phase",
                "trot contacts and phase",
                &format!(
                    "{{\"ticks\":{},\"phase_index\":{},\"subphase_ticks\":{},\"contacts\":[{},{},{},{}]}}",
                    ticks, self.gait.phase_index(ticks), sub, contacts[0], contacts[1], contacts[2], contacts[3]
                ),
            );
        }
        // #endregion

        for leg in 0..4 {
            if contacts[leg] == 1 {
                // Stance phase — foot on ground
                let cmd = nalgebra::Vector3::new(cmd_vel[0], cmd_vel[1], cmd_vel[2]);
                next.column_mut(leg).copy_from(
                    &self.stance_.next_foot_location(leg, current, &cmd, robot_height)
                );
            } else {
                // Swing phase — foot in air
                let swing_prop = sub as f64 / self.gait.swing_ticks as f64;
                let cmd = nalgebra::Vector3::new(cmd_vel[0], cmd_vel[1], cmd_vel[2]);
                next.column_mut(leg).copy_from(
                    &self.swing_.next_foot_location(swing_prop, leg, current, &cmd, robot_height)
                );
            }
        }

        next
    }

    /// Default stance matrix (public accessor)
    pub fn default_stance(&self) -> SMatrix<f64, 3, 4> {
        self.gait.default_stance
    }

    /// Phase length in ticks
    pub fn phase_length(&self) -> i32 {
        self.gait.phase_length
    }

    /// Stance ticks
    pub fn stance_ticks(&self) -> i32 {
        self.gait.stance_ticks
    }

    /// Swing ticks
    pub fn swing_ticks(&self) -> i32 {
        self.gait.swing_ticks
    }
}
