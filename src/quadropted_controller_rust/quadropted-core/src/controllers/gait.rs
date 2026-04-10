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
