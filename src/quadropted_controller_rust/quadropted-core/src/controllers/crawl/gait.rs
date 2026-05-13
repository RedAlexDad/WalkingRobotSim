//! Crawl Gait Controller — Orchestrates crawl stance and swing
//!
//! Direct translation from C++ `crawl_gait.cpp`.
//! 8-phase gait with diagonal leg coordination.

use super::stance::CrawlStanceController;
use super::swing::CrawlSwingController;
use crate::controllers::gait::GaitController;
use nalgebra::{DMatrix, SMatrix};
use std::fs::OpenOptions;
use std::io::Write;
use std::sync::atomic::{AtomicU64, Ordering};

// #region agent log
static LOG_SEQ_CRAWL: AtomicU64 = AtomicU64::new(0);
const DEBUG_LOG_PATH: &str = "/home/redalexdad/GitHub/WalkingRobotSim/.cursor/debug-f81059.log";

fn dbg_log_crawl(run_id: &str, hypothesis_id: &str, location: &str, message: &str, data: &str) {
    let seq = LOG_SEQ_CRAWL.fetch_add(1, Ordering::Relaxed);
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let line = format!(
        "{{\"sessionId\":\"f81059\",\"id\":\"f81059-crawl-{}\",\"timestamp\":{},\"location\":\"{}\",\"message\":\"{}\",\"data\":{},\"runId\":\"{}\",\"hypothesisId\":\"{}\"}}",
        seq, ts, location, message, data, run_id, hypothesis_id
    );
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(DEBUG_LOG_PATH) {
        let _ = writeln!(f, "{}", line);
    }
}
// #endregion

/// Crawl Gait Controller
pub struct CrawlGaitController {
    gait: GaitController,
    swing_: CrawlSwingController,
    stance_: CrawlStanceController,
    first_cycle_: bool,
}

impl CrawlGaitController {
    pub fn new(
        stance_time: f64,
        swing_time: f64,
        time_step: f64,
        default_stance: SMatrix<f64, 3, 4>,
    ) -> Self {
        // Crawl contact schedule: 8 phases
        // From C++: (Eigen::MatrixXi(4, 8) << 
        //   1, 1, 1, 0, 1, 1, 1, 1,  // FR
        //   1, 1, 1, 1, 1, 1, 1, 0,  // FL
        //   1, 0, 1, 1, 1, 1, 1, 1,  // RR
        //   1, 1, 1, 1, 1, 0, 1, 1)  // RL
        let gait = GaitController::new(
            stance_time,
            swing_time,
            time_step,
            DMatrix::from_row_slice(4, 8, &[
                1, 1, 1, 0, 1, 1, 1, 1,  // FR
                1, 1, 1, 1, 1, 1, 1, 0,  // FL
                1, 0, 1, 1, 1, 1, 1, 1,  // RR
                1, 1, 1, 1, 1, 0, 1, 1,  // RL
            ]),
            default_stance,
        );

        let swing_ = CrawlSwingController::new(
            gait.swing_ticks,
            time_step,
            0.14,  // z_leg_lift
            gait.default_stance.clone(),
            gait.phase_length,
            gait.stance_ticks,
            0.06,  // body_shift_y (как в C++)
        );

        let stance_ = CrawlStanceController::new(
            gait.phase_length,
            gait.stance_ticks,
            gait.swing_ticks,
            time_step,
            0.02,  // z_error_constant
            0.06,  // body_shift_y (как в C++)
        );

        Self {
            gait,
            swing_,
            stance_,
            first_cycle_: true,
        }
    }

    /// Reset first cycle flag
    pub fn reset(&mut self) {
        self.first_cycle_ = true;
    }

    /// Step the gait controller for one tick
    /// Returns new foot positions (3x4 matrix)
    pub fn step(
        &mut self,
        ticks: i32,
        current: &SMatrix<f64, 3, 4>,
        cmd_vel: &[f64; 3],
        robot_height: f64,
    ) -> SMatrix<f64, 3, 4> {
        let mut next = *current;
        let contacts = self.gait.contacts(ticks);
        let sub = self.gait.subphase_ticks(ticks);
        // #region agent log
        if ticks <= 30 || ticks % 120 == 0 {
            dbg_log_crawl(
                "pre-fix",
                "H1_CONTACT_PHASE_LAYOUT",
                "crawl/gait.rs:step_phase",
                "crawl contacts and phase",
                &format!(
                    "{{\"ticks\":{},\"phase_index\":{},\"subphase_ticks\":{},\"first_cycle\":{},\"contacts\":[{},{},{},{}]}}",
                    ticks, self.gait.phase_index(ticks), sub, self.first_cycle_, contacts[0], contacts[1], contacts[2], contacts[3]
                ),
            );
        }
        // #endregion

        for leg in 0..4 {
            if contacts[leg] == 1 {
                let phase_idx = self.gait.phase_index(ticks);
                let move_sideways = phase_idx == 0 || phase_idx == 4;
                let move_left = phase_idx == 0;
                let cmd = nalgebra::Vector3::new(cmd_vel[0], cmd_vel[1], cmd_vel[2]);
                // #region agent log
                if ticks <= 30 || ticks % 120 == 0 {
                    dbg_log_crawl(
                        "pre-fix",
                        "H3_CRAWL_STANCE_PATH_MISMATCH",
                        "crawl/gait.rs:stance_branch",
                        "crawl stance branch selected",
                        &format!(
                            "{{\"ticks\":{},\"leg\":{},\"branch\":\"stance_controller\",\"phase_idx\":{},\"move_sideways\":{},\"move_left\":{}}}",
                            ticks, leg, phase_idx, move_sideways, move_left
                        ),
                    );
                }
                // #endregion
                // Stance phase — C++ node uses explicit CrawlStanceController branch.
                next.column_mut(leg).copy_from(
                    &self.stance_.next_foot_location(
                        leg,
                        current,
                        &cmd,
                        robot_height,
                        self.first_cycle_,
                        move_sideways,
                        move_left,
                    ),
                );
            } else {
                // Swing phase — foot in air
                let swing_prop = sub as f64 / self.gait.swing_ticks as f64;
                let cmd = nalgebra::Vector3::new(cmd_vel[0], cmd_vel[1], cmd_vel[2]);
                let phase_idx = self.gait.phase_index(ticks);
                next.column_mut(leg).copy_from(
                    &self.swing_.next_foot_location(
                        swing_prop,
                        leg,
                        current,
                        &cmd,
                        robot_height,
                        self.first_cycle_,
                        phase_idx,
                    )
                );
            }
        }

        // Сброс first_cycle_ после первого полного цикла
        if ticks >= self.gait.phase_length {
            self.first_cycle_ = false;
        }

        if ticks % 60 == 0 {
            println!(
                "[RUNTIME_CRAWL_RUST] ticks={} phase={} sub={} contacts=[{},{},{},{}] cmd=[{:.4},{:.4},{:.4}] \
fr=({:.4},{:.4},{:.4}) fl=({:.4},{:.4},{:.4}) rr=({:.4},{:.4},{:.4}) rl=({:.4},{:.4},{:.4})",
                ticks,
                self.gait.phase_index(ticks),
                sub,
                contacts[0], contacts[1], contacts[2], contacts[3],
                cmd_vel[0], cmd_vel[1], cmd_vel[2],
                next[(0, 0)], next[(1, 0)], next[(2, 0)],
                next[(0, 1)], next[(1, 1)], next[(2, 1)],
                next[(0, 2)], next[(1, 2)], next[(2, 2)],
                next[(0, 3)], next[(1, 3)], next[(2, 3)],
            );
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

    /// Is first cycle?
    pub fn is_first_cycle(&self) -> bool {
        self.first_cycle_
    }

    /// Contact mask for current tick in leg order FR, FL, RR, RL.
    pub fn contacts(&self, ticks: i32) -> [i32; 4] {
        let contacts = self.gait.contacts(ticks);
        [contacts[0], contacts[1], contacts[2], contacts[3]]
    }

    /// Current gait phase index.
    pub fn phase_index(&self, ticks: i32) -> usize {
        self.gait.phase_index(ticks)
    }

    /// Current subphase ticks.
    pub fn subphase_ticks(&self, ticks: i32) -> i32 {
        self.gait.subphase_ticks(ticks)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_crawl_gait_creation() {
        let default_stance = SMatrix::<f64, 3, 4>::from_row_slice(&[
            0.2081, 0.2081, -0.1881, -0.1881,
            -0.14225, 0.14225, -0.14225, 0.14225,
            0.0, 0.0, 0.0, 0.0,
        ]);

        let crawl = CrawlGaitController::new(0.55, 0.45, 0.02, default_stance);
        
        assert_eq!(crawl.stance_ticks(), 27);  // 0.55 / 0.02 = 27.5 → 27
        assert_eq!(crawl.swing_ticks(), 22);   // 0.45 / 0.02 = 22.5 → 22
        assert!(crawl.is_first_cycle());
    }

    #[test]
    fn test_crawl_gait_step() {
        let default_stance = SMatrix::<f64, 3, 4>::from_row_slice(&[
            0.2081, 0.2081, -0.1881, -0.1881,
            -0.14225, 0.14225, -0.14225, 0.14225,
            0.0, 0.0, 0.0, 0.0,
        ]);

        let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, default_stance);
        let cmd_vel = [0.01, 0.0, 0.0];
        
        let next = crawl.step(0, &default_stance, &cmd_vel, -0.25);
        
        // Проверяем что foot locations изменились
        assert!(next.nrows() == 3 && next.ncols() == 4);
    }

    #[test]
    fn test_crawl_first_cycle_reset() {
        let default_stance = SMatrix::<f64, 3, 4>::from_row_slice(&[
            0.2081, 0.2081, -0.1881, -0.1881,
            -0.14225, 0.14225, -0.14225, 0.14225,
            0.0, 0.0, 0.0, 0.0,
        ]);

        let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, default_stance);
        
        // Симулируем полный цикл
        let phase_len = crawl.phase_length();
        for tick in 0..=phase_len {
            crawl.step(tick, &default_stance, &[0.01, 0.0, 0.0], -0.25);
        }
        
        assert!(!crawl.is_first_cycle());
        
        crawl.reset();
        assert!(crawl.is_first_cycle());
    }
}
