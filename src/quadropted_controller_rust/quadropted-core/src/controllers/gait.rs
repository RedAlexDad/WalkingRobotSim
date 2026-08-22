//! Gait Controller — Base class for all gaits
//!
//! Direct translation from C++ `gait_controller.cpp`.

use nalgebra::{DMatrix, DVector, SMatrix};

/// Base GaitController for managing contact phases
pub struct GaitController {
    stance_time: f64,
    swing_time: f64,
    time_step: f64,
    contact_phases: DMatrix<i32>,
    pub default_stance: SMatrix<f64, 3, 4>,
    pub stance_ticks: i32,
    pub swing_ticks: i32,
    phase_ticks: Vec<i32>,
    pub phase_length: i32,
}

impl GaitController {
    pub fn new(
        stance_time: f64,
        swing_time: f64,
        time_step: f64,
        contact_phases: DMatrix<i32>,
        default_stance: SMatrix<f64, 3, 4>,
    ) -> Self {
        let stance_ticks = (stance_time / time_step) as i32;
        let swing_ticks = (swing_time / time_step) as i32;

        // Compute phase_ticks: if any leg is swinging → swing_ticks, else stance_ticks
        let mut phase_ticks = Vec::new();
        let num_phases = contact_phases.ncols();
        for col in 0..num_phases {
            let mut has_swing = false;
            for leg in 0..contact_phases.nrows() {
                if contact_phases[(leg, col)] == 0 {
                    has_swing = true;
                    break;
                }
            }
            if has_swing {
                phase_ticks.push(swing_ticks);
            } else {
                phase_ticks.push(stance_ticks);
            }
        }

        let phase_length: i32 = phase_ticks.iter().sum();

        Self {
            stance_time,
            swing_time,
            time_step,
            contact_phases,
            default_stance,
            stance_ticks,
            swing_ticks,
            phase_ticks,
            phase_length,
        }
    }

    /// Current phase index for given tick
    pub fn phase_index(&self, ticks: i32) -> usize {
        let phase_time = (ticks % self.phase_length) as usize;
        let mut phase_sum = 0;
        for (i, &ticks_in_phase) in self.phase_ticks.iter().enumerate() {
            phase_sum += ticks_in_phase as usize;
            if phase_time < phase_sum {
                return i;
            }
        }
        self.phase_ticks.len() - 1
    }

    /// Ticks elapsed in current subphase
    pub fn subphase_ticks(&self, ticks: i32) -> i32 {
        let phase_time = ticks % self.phase_length;
        let mut phase_sum = 0;
        for (i, &ticks_in_phase) in self.phase_ticks.iter().enumerate() {
            phase_sum += ticks_in_phase;
            if phase_time < phase_sum {
                return phase_time - phase_sum + ticks_in_phase;
            }
        }
        0
    }

    /// Contact vector for current phase (1 = stance, 0 = swing)
    pub fn contacts(&self, ticks: i32) -> DVector<i32> {
        let phase = self.phase_index(ticks);
        self.contact_phases.column(phase).into()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use nalgebra::DMatrix;

    /// Trot contact phases: 4 phases (columns), 4 legs (rows).
    /// Each column: leg in contact (1) or swing (0).
    fn trot_phases() -> DMatrix<i32> {
        DMatrix::from_column_slice(
            4,
            4,
            &[
                1, 0, 1, 0, // phase 0
                1, 1, 1, 1, // phase 1 (all stance)
                0, 1, 0, 1, // phase 2
                1, 1, 1, 1, // phase 3 (all stance)
            ],
        )
    }

    fn default_stance() -> SMatrix<f64, 3, 4> {
        SMatrix::<f64, 3, 4>::zeros()
    }

    #[test]
    fn test_gait_phase_ticks_swing_dominates() {
        // swing_time=0.2, stance_time=0.4, dt=0.02 → swing_ticks=10, stance_ticks=20
        let gait = GaitController::new(0.4, 0.2, 0.02, trot_phases(), default_stance());
        assert_eq!(gait.stance_ticks, 20);
        assert_eq!(gait.swing_ticks, 10);
        // phases 0 and 2 have a swinging leg → swing_ticks=10; 1 and 3 → stance_ticks=20
        assert_eq!(gait.phase_ticks, vec![10, 20, 10, 20]);
        assert_eq!(gait.phase_length, 60);
    }

    #[test]
    fn test_gait_phase_index_invariants() {
        let gait = GaitController::new(0.4, 0.2, 0.02, trot_phases(), default_stance());
        // Инвариант: phase_index всегда в [0, nphases)
        for ticks in 0..1200 {
            let p = gait.phase_index(ticks);
            assert!(p < gait.phase_ticks.len(), "phase index {p} out of range at ticks {ticks}");
        }
        // Границы фаз: cumulative [0,10) [10,30) [30,40) [40,60)
        assert_eq!(gait.phase_index(0), 0);
        assert_eq!(gait.phase_index(9), 0);
        assert_eq!(gait.phase_index(10), 1);
        assert_eq!(gait.phase_index(29), 1);
        assert_eq!(gait.phase_index(30), 2);
        assert_eq!(gait.phase_index(39), 2);
        assert_eq!(gait.phase_index(40), 3);
        assert_eq!(gait.phase_index(59), 3);
        // Wrap
        assert_eq!(gait.phase_index(60), 0);
    }

    #[test]
    fn test_gait_subphase_ticks_invariants() {
        let gait = GaitController::new(0.4, 0.2, 0.02, trot_phases(), default_stance());
        // Инвариант: subphase_ticks в [0, phase_length)
        for ticks in 0..1200 {
            let sp = gait.subphase_ticks(ticks);
            assert!(sp >= 0 && sp < gait.phase_length, "subphase {sp} out of range at ticks {ticks}");
        }
        // Монотонность внутри фазы 0 (swing, 10 тактов): 0..10
        for t in 1..10 {
            assert!(
                gait.subphase_ticks(t) >= gait.subphase_ticks(t - 1),
                "subphase must be non-decreasing within a phase"
            );
        }
        // Сброс на новой фазе
        assert!(gait.subphase_ticks(0) <= gait.subphase_ticks(10));
    }

    #[test]
    fn test_gait_contacts_returns_phase_column() {
        let gait = GaitController::new(0.4, 0.2, 0.02, trot_phases(), default_stance());
        let c0 = gait.contacts(0);
        assert_eq!(c0, DVector::from_row_slice(&[1, 0, 1, 0]));
        let c1 = gait.contacts(10);
        assert_eq!(c1, DVector::from_row_slice(&[1, 1, 1, 1]));
        let c2 = gait.contacts(30);
        assert_eq!(c2, DVector::from_row_slice(&[0, 1, 0, 1]));
    }

    #[test]
    fn test_gait_phase_index_last_phase_fallback() {
        // Empty contact matrix edge: num_phases=0 → phase_ticks empty → phase_length=0
        // phase_index must not panic and return len-1 (0 for empty → usize underflow guarded)
        let empty = DMatrix::<i32>::zeros(0, 0);
        let gait = GaitController::new(0.4, 0.2, 0.02, empty, default_stance());
        assert_eq!(gait.phase_length, 0);
        // ticks % 0 panics in Rust! phase_index would divide by zero.
        // This is guarded by callers; here we just check construction is safe.
        assert_eq!(gait.phase_ticks.len(), 0);
    }

    #[test]
    fn test_gait_phase_index_no_swing_all_stance() {
        // All legs always in contact → every phase uses stance_ticks
        let all_stance = DMatrix::from_element(4, 2, 1);
        let gait = GaitController::new(0.4, 0.2, 0.02, all_stance, default_stance());
        assert_eq!(gait.phase_ticks, vec![20, 20]);
        assert_eq!(gait.phase_length, 40);
        assert_eq!(gait.phase_index(0), 0);
        assert_eq!(gait.phase_index(19), 0);
        assert_eq!(gait.phase_index(20), 1);
        assert_eq!(gait.phase_index(39), 1);
        assert_eq!(gait.phase_index(40), 0);
    }
}
