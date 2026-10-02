//! Trot Gait Controller — Orchestrates trot stance and swing
//!
//! Direct translation from C++ `trot_gait.cpp`.

use super::stance::TrotStanceController;
use super::swing::TrotSwingController;
use crate::controllers::gait::GaitController;
use crate::controllers::pid::PIDController;
use nalgebra::{DMatrix, SMatrix};

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

    /// Whether IMU compensation is enabled
    pub fn use_imu(&self) -> bool {
        self.use_imu
    }

    /// Contact mask for current tick in leg order FR, FL, RR, RL.
    pub fn contacts(&self, ticks: i32) -> [i32; 4] {
        let c = self.gait.contacts(ticks);
        [c[0], c[1], c[2], c[3]]
    }

    /// Mutable access to the PID controller (for IMU compensation)
    pub fn pid_controller(&mut self) -> &mut PIDController {
        &mut self.pid_
    }

    /// Mutable access to the gait (for reset)
    pub fn gait_mut(&mut self) -> &mut GaitController {
        &mut self.gait
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_stance() -> SMatrix<f64, 3, 4> {
        let mut m = SMatrix::<f64, 3, 4>::zeros();
        m[(0, 0)] = 0.2081; m[(1, 0)] = -0.14225;
        m[(0, 1)] = 0.2081; m[(1, 1)] = 0.14225;
        m[(0, 2)] = -0.1881; m[(1, 2)] = -0.14225;
        m[(0, 3)] = -0.1881; m[(1, 3)] = 0.14225;
        m
    }

    #[test]
    fn test_trot_accessors() {
        let st = default_stance();
        let mut trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
        assert_eq!(trot.stance_ticks(), 2);
        assert_eq!(trot.swing_ticks(), 9);
        assert_eq!(trot.phase_length(), 22);
        assert!(!trot.use_imu());
        assert_eq!(trot.default_stance(), st);
        let c = trot.contacts(1);
        assert_eq!(c.len(), 4);
        // pid_controller + gait_mut — доступны
        let _ = trot.pid_controller().reset(0.0);
        let _ = trot.gait_mut().phase_index(1);
    }

    #[test]
    fn test_trot_use_imu_true() {
        let st = default_stance();
        let trot = TrotGaitController::new(0.04, 0.18, 0.02, true, st);
        assert!(trot.use_imu());
    }

    #[test]
    fn test_trot_step_keeps_dimensions_and_finite() {
        let st = default_stance();
        let trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
        let cmd_vel = [0.1, 0.0, 0.0];
        // Прогоняем полный цикл (phase_length=22 тика)
        for tick in 0..44 {
            let next = trot.step(tick, &st, &cmd_vel, -0.25);
            assert_eq!(next.nrows(), 3);
            assert_eq!(next.ncols(), 4);
            for r in 0..3 {
                for c in 0..4 {
                    assert!(next[(r, c)].is_finite(), "non-finite at tick {tick} ({r},{c})");
                }
            }
        }
    }

    #[test]
    fn test_trot_step_zero_velocity_returns_near_stance() {
        let st = default_stance();
        let trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
        let cmd_vel = [0.0, 0.0, 0.0];
        // С нулевой командой stance-нога остаётся на месте (z-компенсация малая)
        let next = trot.step(1, &st, &cmd_vel, -0.25);
        for leg in 0..4 {
            assert!(
                (next[(0, leg)] - st[(0, leg)]).abs() < 0.01,
                "stance x drift leg {leg}: {} vs {}",
                next[(0, leg)], st[(0, leg)]
            );
        }
    }

    #[test]
    fn test_trot_step_swing_leg_lifts() {
        let mut st = default_stance();
        // Устанавливаем z = robot_height для всех ног (в стойке лапы на земле)
        for col in 0..4 {
            st[(2, col)] = -0.25;
        }
        let trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
        let cmd_vel = [0.0, 0.0, 0.0];
        // Контактная матрица по столбцам: фаза 0 (tick 0-1) = [1,1,1,1] (двойная опора),
        // фаза 1 (tick 2-10) = [1,0,0,1] → leg 1 (FL) и leg 2 (RR) в swing.
        // Tick 3: subphase=1, swing_prop = 1/9 ≈ 0.111 → нога поднята
        let next = trot.step(3, &st, &cmd_vel, -0.25);
        // Swing-нога (leg 1) должна быть ВЫШЕ земли (z > robot_height)
        assert!(
            next[(2, 1)] > -0.25,
            "swing leg 1 should lift above robot_height: {}",
            next[(2, 1)]
        );
        // Stance-нога (leg 0) остаётся на уровне земли
        assert!(
            (next[(2, 0)] - (-0.25)).abs() < 0.01,
            "stance leg should stay on ground: {}",
            next[(2, 0)]
        );
    }

    #[test]
    fn test_trot_contacts_pattern() {
        let st = default_stance();
        let trot = TrotGaitController::new(0.04, 0.18, 0.02, false, st);
        // Контактная матрица построена по столбцам (from_row_slice + column access):
        // колонка 0 (tick 0-1) = [1,1,1,1] (двойная опора), колонка 1 (tick 2-10) = [1,0,0,1]
        assert_eq!(trot.contacts(0), [1, 1, 1, 1]);
        assert_eq!(trot.contacts(3), [1, 0, 0, 1]);
    }

    #[test]
    fn test_trot_pid_reset_after_step() {
        let st = default_stance();
        let mut trot = TrotGaitController::new(0.04, 0.18, 0.02, true, st);
        // PID начинает с last_time=-1 → первый run возвращает [0,0]
        let out = trot.pid_controller().run(0.1, 0.0, 0.0);
        assert_eq!(out, [0.0, 0.0]);
        let out2 = trot.pid_controller().run(0.1, 0.0, 0.02);
        // kp=0.15, error=-0.1 → P-член -0.015 (плюс I/D малые)
        assert!(out2[0].abs() < 0.05, "PID out {}", out2[0]);
    }
}
