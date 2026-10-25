"""Analytical core for operator anomaly detection in a walking-robot control loop.

The module implements the formal model from
``docs/ergonomics-methodology/2026-10-25_formal-model.md``.

All functions are pure and use only the Python standard library.  The model is
analytical: it calculates ergonomic characteristics from detector and
information-model parameters; it does not replace them with measured metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, log2, sqrt
from statistics import NormalDist
from typing import Iterable, Sequence


_STANDARD_NORMAL = NormalDist()


def normal_cdf(x: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def normal_ppf(p: float) -> float:
    """Standard normal inverse CDF; ``0 < p < 1``."""
    if not 0.0 < p < 1.0:
        raise ValueError(f"probability must be in (0, 1), got {p!r}")
    return _STANDARD_NORMAL.inv_cdf(p)


def d_prime(p_det: float, p_fa: float) -> float:
    """Detector sensitivity from hit and false-alarm probabilities.

    Equal-variance Gaussian signal-detection model:
    ``d' = z(P_D) - z(P_FA)``.
    """
    return normal_ppf(p_det) - normal_ppf(p_fa)


def detection_probability(d: float, criterion: float) -> float:
    """``P_det = Phi(d'/2 - c)``."""
    return normal_cdf(d / 2.0 - criterion)


def false_alarm_probability(d: float, criterion: float) -> float:
    """``P_fa = Phi(-d'/2 - c)``."""
    return normal_cdf(-d / 2.0 - criterion)


def neyman_pearson(d: float, alpha: float) -> tuple[float, float, float]:
    """Return ``(P_det, P_fa, c*)`` for ``P_fa <= alpha``.

    The optimal criterion is ``c* = -d'/2 - z(alpha)``.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha!r}")
    if d < 0.0:
        raise ValueError(f"d' must be non-negative, got {d!r}")
    criterion = -d / 2.0 - normal_ppf(alpha)
    return detection_probability(d, criterion), false_alarm_probability(d, criterion), criterion


def effective_sensitivity(detector_d_prime: float, im_efficiency: float) -> float:
    """Effective sensitivity ``d' = eta_IM * d'_tech``.

    ``im_efficiency`` is the information-model efficiency in ``(0, 1]``; it is
    an estimated or measured parameter, not a subjective weight.
    """
    if not 0.0 < im_efficiency <= 1.0:
        raise ValueError(f"im_efficiency must be in (0, 1], got {im_efficiency!r}")
    if detector_d_prime < 0.0:
        raise ValueError(f"detector_d_prime must be non-negative, got {detector_d_prime!r}")
    return im_efficiency * detector_d_prime


def search_time(elements: float, visual_span: float, feature_elements: float, fixation: float) -> float:
    """Information-search time from the ergonomics lecture.

    ``t_search = ((E + a) / a * (1 + H_alpha)) * t_fix``.
    """
    if visual_span <= 0.0:
        raise ValueError("visual_span must be positive")
    if elements < 0.0 or feature_elements < 0.0 or fixation < 0.0:
        raise ValueError("elements, feature_elements and fixation must be non-negative")
    return ((elements + visual_span) / visual_span) * (1.0 + feature_elements) * fixation


def decision_time(n_alternatives: int, intercept: float, slope: float) -> float:
    """Hick's law: ``T_dec = a + b * log2(N)``."""
    if n_alternatives < 1:
        raise ValueError("n_alternatives must be >= 1")
    return intercept + slope * log2(n_alternatives)


def detection_time(
    t_lat: float,
    t_search: float,
    t_dec: float,
    t_act: float,
) -> float:
    """Total detection/response time."""
    if min(t_lat, t_search, t_dec, t_act) < 0.0:
        raise ValueError("time components must be non-negative")
    return t_lat + t_search + t_dec + t_act


def workload(
    n_anomalies: float,
    t_detect: float,
    n_false_alarms: float,
    t_check: float,
    t_shift: float,
) -> float:
    """Operator workload as occupied fraction of a shift."""
    if t_shift <= 0.0:
        raise ValueError("t_shift must be positive")
    if min(n_anomalies, n_false_alarms, t_detect, t_check) < 0.0:
        raise ValueError("workload inputs must be non-negative")
    return (n_anomalies * t_detect + n_false_alarms * t_check) / t_shift


@dataclass(frozen=True)
class Variant:
    """One information-model/alarm variant to evaluate."""

    name: str
    d_eff: float
    p_det: float
    p_fa: float
    t_detect: float
    workload: float

    def admissible(self, alpha: float, t_req: float, k_req: float) -> bool:
        return self.p_fa <= alpha and self.t_detect <= t_req and self.workload <= k_req


def select_variant(
    variants: Iterable[Variant],
    alpha: float,
    t_req: float,
    k_req: float,
) -> Variant | None:
    """Deterministic selection without weights or Pareto.

    Constraints: ``P_fa <= alpha``, ``T_det <= t_req``, ``K_load <= k_req``.
    Among admissible variants: max ``P_det``, then min ``T_det``, then min
    ``P_fa``.
    """
    admissible = [v for v in variants if v.admissible(alpha, t_req, k_req)]
    if not admissible:
        return None
    return min(
        admissible,
        key=lambda v: (-v.p_det, v.t_detect, v.p_fa, v.name),
    )


def evaluate_variant(
    name: str,
    detector_d_prime: float,
    im_efficiency: float,
    alpha: float,
    t_lat: float,
    elements: float,
    visual_span: float,
    feature_elements: float,
    fixation: float,
    n_alternatives: int,
    decision_intercept: float,
    decision_slope: float,
    t_act: float,
    n_anomalies: float,
    n_false_alarms: float,
    t_check: float,
    t_shift: float,
) -> Variant:
    """Evaluate one variant using the analytical model."""
    d_eff = effective_sensitivity(detector_d_prime, im_efficiency)
    p_det, p_fa, _ = neyman_pearson(d_eff, alpha)
    t_search = search_time(elements, visual_span, feature_elements, fixation)
    t_dec = decision_time(n_alternatives, decision_intercept, decision_slope)
    t_det = detection_time(t_lat, t_search, t_dec, t_act)
    k_load = workload(n_anomalies, t_det, n_false_alarms, t_check, t_shift)
    return Variant(name, d_eff, p_det, p_fa, t_det, k_load)
