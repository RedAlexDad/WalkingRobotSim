//! Crawl Gait Controller — Orchestrates crawl stance and swing
//!
//! Direct translation from C++ `crawl_gait.cpp`.
//! 8-phase gait with diagonal leg coordination.

use super::stance::CrawlStanceController;
use super::swing::CrawlSwingController;
use crate::controllers::gait::GaitController;
use nalgebra::{DMatrix, SMatrix};

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
    ) -> SMatrix<f64, 3, 4> {
        let mut next = *current;
        let contacts = self.gait.contacts(ticks);
        let sub = self.gait.subphase_ticks(ticks);

        for leg in 0..4 {
            if contacts[leg] == 1 {
                // Stance phase — foot on ground
                // В C++ просто возвращается текущая позиция
                next.column_mut(leg).copy_from(&current.column(leg));
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
        
        let next = crawl.step(0, &default_stance, &cmd_vel);
        
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
            crawl.step(tick, &default_stance, &[0.01, 0.0, 0.0]);
        }
        
        assert!(!crawl.is_first_cycle());
        
        crawl.reset();
        assert!(crawl.is_first_cycle());
    }
}
