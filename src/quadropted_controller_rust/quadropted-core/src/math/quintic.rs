//! Quintic-полином (порт из `unitree_a1_trot_mujoco/quintic_poly.py`).
//!
//! Гладкая интерполяция `q(t)` между `q0` и `qf` за время `[t0, tf]` с
//! нулевыми скоростью и ускорением на концах (6 граничных условий → 6 коэф.).

/// Коэффициенты квинтика `q(t) = a0 + a1 t + … + a5 t^5`.
#[derive(Debug, Clone, Copy)]
pub struct Quintic {
    a: [f64; 6],
    t0: f64,
    tf: f64,
}

impl Quintic {
    /// Построить квинтик по граничным условиям `q(t0)=q0`, `q(tf)=qf`,
    /// `q'(t0)=q'(tf)=q''(t0)=q''(tf)=0`.
    pub fn new(t0: f64, tf: f64, q0: f64, qf: f64) -> Self {
        let d = tf - t0;
        // Аналитическое решение для нулевых краевых условий (стандартный квинтик).
        let a0 = q0;
        let a1 = 0.0;
        let a2 = 0.0;
        let a3 = 10.0 * (qf - q0) / d.powi(3);
        let a4 = -15.0 * (qf - q0) / d.powi(4);
        let a5 = 6.0 * (qf - q0) / d.powi(5);
        Self {
            a: [a0, a1, a2, a3, a4, a5],
            t0,
            tf,
        }
    }

    /// `(q, qdot, qddot)` в момент `t` (с насыщением `t` в `[t0, tf]`).
    pub fn eval(&self, t: f64) -> (f64, f64, f64) {
        let t = t.clamp(self.t0, self.tf) - self.t0;
        let a = &self.a;
        let q = a[0] + a[1] * t + a[2] * t.powi(2) + a[3] * t.powi(3) + a[4] * t.powi(4) + a[5] * t.powi(5);
        let qd = a[1] + 2.0 * a[2] * t + 3.0 * a[3] * t.powi(2) + 4.0 * a[4] * t.powi(3) + 5.0 * a[5] * t.powi(4);
        let qdd = 2.0 * a[2] + 6.0 * a[3] * t + 12.0 * a[4] * t.powi(2) + 20.0 * a[5] * t.powi(3);
        (q, qd, qdd)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn endpoints_match() {
        let q = Quintic::new(0.0, 0.15, -0.25, -0.18);
        let (q0, v0, a0) = q.eval(0.0);
        let (qf, vf, af) = q.eval(0.15);
        assert!((q0 - (-0.25)).abs() < 1e-12);
        assert!((qf - (-0.18)).abs() < 1e-12);
        assert!(v0.abs() < 1e-12 && vf.abs() < 1e-12);
        assert!(a0.abs() < 1e-12 && af.abs() < 1e-12);
    }

    #[test]
    fn monotonic_rise() {
        let q = Quintic::new(0.0, 0.15, 0.0, 1.0);
        let mid = q.eval(0.075).0;
        assert!((mid - 0.5).abs() < 1e-9);
    }
}
