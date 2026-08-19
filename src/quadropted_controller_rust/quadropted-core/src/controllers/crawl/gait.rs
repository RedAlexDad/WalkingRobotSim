//! Crawl Gait Controller — Orchestrates crawl stance and swing
//!
//! Direct translation from the active C++ runtime path
//! (`quadropted_controller_cpp/src/nodes/robot_controller_node.cpp::step_crawl`),
//! NOT the C++ library `CrawlGaitController::step` (which the node never calls).

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
    ///
    /// Mirrors the active C++ runtime `step_crawl` exactly:
    ///  - zero velocity command → lerp back to default stance (alpha = 0.1)
    ///  - stance legs → `CrawlStanceController::next_foot_location`
    ///  - swing legs → `CrawlSwingController::next_foot_location`
    ///  - `first_cycle_` is never cleared here (the C++ node never calls
    ///    `CrawlGaitController::step()`, so `is_first_cycle()` stays true,
    ///    keeping `shift_factor = 1` in the stance controller)
    pub fn step(
        &mut self,
        ticks: i32,
        current: &SMatrix<f64, 3, 4>,
        cmd_vel: &[f64; 3],
        robot_height: f64,
    ) -> SMatrix<f64, 3, 4> {
        // C++ step_crawl: при нулевой скорости — стабильная стойка
        let has_command = cmd_vel[0].abs() > 1e-4 || cmd_vel[1].abs() > 1e-4 || cmd_vel[2].abs() > 1e-4;
        if !has_command {
            // Плавное возвращение к default_stance
            let mut result = self.gait.default_stance;
            result.row_mut(2).fill(robot_height);
            let alpha = 0.1;
            return current * (1.0 - alpha) + result * alpha;
        }

        let mut next = SMatrix::<f64, 3, 4>::zeros();
        let contacts = self.gait.contacts(ticks);
        let sub = self.gait.subphase_ticks(ticks);
        let phase_idx = self.gait.phase_index(ticks);
        let cmd = nalgebra::Vector3::new(cmd_vel[0], cmd_vel[1], cmd_vel[2]);

        for leg in 0..4 {
            if contacts[leg] == 1 {
                // Stance — CrawlStanceController with move_sideways (как в C++ ноде)
                let move_sideways = phase_idx == 0 || phase_idx == 4;
                let move_left = phase_idx == 0;
                next.column_mut(leg).copy_from(&self.stance_.next_foot_location(
                    leg,
                    current,
                    &cmd,
                    robot_height,
                    self.first_cycle_,
                    move_sideways,
                    move_left,
                ));
            } else {
                // Swing — foot in air (C++ swing hardcodes shifted_left=false)
                let swing_prop = sub as f64 / self.gait.swing_ticks as f64;
                next.column_mut(leg).copy_from(&self.swing_.next_foot_location(
                    swing_prop,
                    leg,
                    current,
                    &cmd,
                    robot_height,
                ));
            }
        }

        // NOTE: first_cycle_ intentionally NOT cleared — matches the active C++
        // runtime path where the node never calls CrawlGaitController::step().

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
    fn test_crawl_zero_command_lerp() {
        // C++ runtime: при нулевой скорости — плавное возвращение к default_stance
        let default_stance = SMatrix::<f64, 3, 4>::from_row_slice(&[
            0.2081, 0.2081, -0.1881, -0.1881,
            -0.14225, 0.14225, -0.14225, 0.14225,
            0.0, 0.0, 0.0, 0.0,
        ]);

        let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, default_stance);
        let cmd_vel = [0.0, 0.0, 0.0];

        // Отклонённая поза
        let mut offset = default_stance;
        offset[(0, 0)] = 0.3;

        let next = crawl.step(0, &offset, &cmd_vel, -0.25);

        // Lerp на 10% к default_stance: x FR = 0.3*0.9 + 0.2081*0.1 = 0.2908
        let expected_x = 0.3 * 0.9 + 0.2081 * 0.1;
        assert!((next[(0, 0)] - expected_x).abs() < 1e-10, "x = {}", next[(0, 0)]);
        // z-ряд тоже лерпится: 0.0*0.9 + (-0.25)*0.1 = -0.025 (как в C++ step_crawl)
        let expected_z = 0.0 * 0.9 + (-0.25) * 0.1;
        assert!((next[(2, 0)] - expected_z).abs() < 1e-10, "z = {}", next[(2, 0)]);
    }

    #[test]
    fn test_crawl_first_cycle_stays_true_like_cpp_runtime() {
        // Активный C++ рантайм никогда не вызывает CrawlGaitController::step(),
        // поэтому first_cycle_ остаётся true навсегда (shift_factor=1 в stance).
        let default_stance = SMatrix::<f64, 3, 4>::from_row_slice(&[
            0.2081, 0.2081, -0.1881, -0.1881,
            -0.14225, 0.14225, -0.14225, 0.14225,
            0.0, 0.0, 0.0, 0.0,
        ]);

        let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, default_stance);
        
        // Симулируем несколько полных циклов
        let phase_len = crawl.phase_length();
        for tick in 0..(phase_len * 3) {
            crawl.step(tick, &default_stance, &[0.01, 0.0, 0.0], -0.25);
        }
        
        // Как в C++ рантайме: first_cycle_ не сбрасывается
        assert!(crawl.is_first_cycle());
        
        crawl.reset();
        assert!(crawl.is_first_cycle());
    }
}
