//! Траектория стопы по логике A1-trot (порт `cartesian_traj.py` +
//! `state_machine.py` из `unitree_a1_trot_mujoco`).
//!
//! Каждая нога чередует фазы stance/swing длительностью `t_step`. В stance
//! стопа едет назад (`+0.5·v·T → −0.5·v·T`), в swing возвращается вперёд и
//! поднимается на `hcl` (по квинтику). Позиция в системе ноги:
//! `lx` (вперёд), `ly` (латераль), `lz` (вниз, отрицательно).

use crate::math::quintic::Quintic;

/// Фаза ноги.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Phase {
    Stance,
    Swing,
}

/// Генератор траектории одной стопы.
#[derive(Debug, Clone, Copy)]
pub struct FootTraj {
    pub t_step: f64,
    pub lz0: f64,
    pub hcl: f64,
    pub phase: Phase,
    t: f64,
    // Границы текущей фазы
    lx_i: f64,
    lx_f: f64,
}

impl FootTraj {
    /// `vx` — продольная скорость команды, `start_swing` — начинать ли с маха.
    pub fn new(t_step: f64, lz0: f64, hcl: f64, vx: f64, start_swing: bool) -> Self {
        let half = 0.5 * vx * t_step;
        let (phase, lx_i, lx_f) = if start_swing {
            (Phase::Swing, -half, half)
        } else {
            (Phase::Stance, half, -half)
        };
        Self {
            t_step,
            lz0,
            hcl,
            phase,
            t: 0.0,
            lx_i,
            lx_f,
        }
    }

    /// Шаг на `dt`, возвращает `(lx, ly, lz)`.
    pub fn step(&mut self, dt: f64, vx: f64) -> (f64, f64, f64) {
        self.t += dt;
        if self.t >= self.t_step {
            self.t -= self.t_step;
            let half = 0.5 * vx * self.t_step;
            match self.phase {
                Phase::Stance => {
                    self.phase = Phase::Swing;
                    self.lx_i = -half;
                    self.lx_f = half;
                }
                Phase::Swing => {
                    self.phase = Phase::Stance;
                    self.lx_i = half;
                    self.lx_f = -half;
                }
            }
        }

        let lx = Quintic::new(0.0, self.t_step, self.lx_i, self.lx_f).eval(self.t).0;
        let ly = 0.0;
        let lz = match self.phase {
            Phase::Stance => self.lz0,
            Phase::Swing => {
                // Подъём: квинтик вверх за первую половину, вниз за вторую.
                let half = self.t_step / 2.0;
                if self.t <= half {
                    Quintic::new(0.0, half, self.lz0, self.lz0 + self.hcl).eval(self.t).0
                } else {
                    Quintic::new(half, self.t_step, self.lz0 + self.hcl, self.lz0).eval(self.t).0
                }
            }
        };
        (lx, ly, lz)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stance_travels_back() {
        let mut f = FootTraj::new(0.15, -0.249, 0.075, 0.3, false);
        let a = f.step(0.01, 0.3).0;
        let mut last = a;
        for _ in 0..14 {
            last = f.step(0.01, 0.3).0;
        }
        assert!(a > last, "в стойке стопа должна ехать назад: {a} -> {last}");
    }

    #[test]
    fn swing_lifts() {
        let mut f = FootTraj::new(0.15, -0.249, 0.075, 0.3, true);
        let mut max_z = f64::MIN;
        for _ in 0..15 {
            let (_, _, z) = f.step(0.01, 0.3);
            max_z = max_z.max(z);
        }
        assert!(max_z > -0.249 + 0.05, "swing должен поднимать: {max_z}");
    }
}
