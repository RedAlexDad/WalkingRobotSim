from __future__ import annotations

import unittest

from model import (
    Variant,
    d_prime,
    decision_time,
    detection_time,
    effective_sensitivity,
    false_alarm_probability,
    neyman_pearson,
    normal_cdf,
    normal_ppf,
    search_time,
    select_variant,
    workload,
)


class NormalDistributionTest(unittest.TestCase):
    def test_cdf_ppf_roundtrip(self) -> None:
        for p in (0.01, 0.1, 0.5, 0.9, 0.99):
            self.assertAlmostEqual(normal_cdf(normal_ppf(p)), p, places=12)

    def test_cdf_median(self) -> None:
        self.assertAlmostEqual(normal_cdf(0.0), 0.5, places=12)


class SignalDetectionTest(unittest.TestCase):
    def test_d_prime_roundtrip(self) -> None:
        d = 2.0
        criterion = 0.3
        p_det = normal_cdf(d / 2.0 - criterion)
        p_fa = normal_cdf(-d / 2.0 - criterion)
        self.assertAlmostEqual(d_prime(p_det, p_fa), d, places=12)

    def test_neyman_pearson_meets_alpha(self) -> None:
        for d in (0.5, 1.0, 2.0, 3.0):
            for alpha in (0.01, 0.05, 0.1):
                _, p_fa, _ = neyman_pearson(d, alpha)
                self.assertAlmostEqual(p_fa, alpha, places=12)

    def test_detection_probability_increases_with_d(self) -> None:
        alpha = 0.05
        previous = -1.0
        for d in (0.0, 0.5, 1.0, 2.0, 3.0):
            p_det, _, _ = neyman_pearson(d, alpha)
            self.assertGreaterEqual(p_det, previous)
            previous = p_det

    def test_false_alarm_decreases_with_criterion(self) -> None:
        self.assertGreater(
            false_alarm_probability(2.0, -0.5),
            false_alarm_probability(2.0, 0.5),
        )


class TimeTest(unittest.TestCase):
    def test_search_time(self) -> None:
        # ((10 + 2) / 2) * (1 + 3) * 0.2 = 4.8
        self.assertAlmostEqual(search_time(10, 2, 3, 0.2), 4.8, places=12)

    def test_decision_time(self) -> None:
        self.assertAlmostEqual(decision_time(2, 0.3, 0.2), 0.5, places=12)

    def test_detection_time_is_sum(self) -> None:
        self.assertAlmostEqual(detection_time(0.2, 1.0, 0.5, 0.1), 1.8, places=12)


class WorkloadTest(unittest.TestCase):
    def test_workload_fraction(self) -> None:
        # (2 * 10 + 4 * 5) / 100 = 0.4
        self.assertAlmostEqual(workload(2, 10, 4, 5, 100), 0.4, places=12)


class SelectionTest(unittest.TestCase):
    def test_selects_max_detection_then_time(self) -> None:
        variants = [
            Variant("a", 2.0, 0.80, 0.04, 2.0, 0.3),
            Variant("b", 2.2, 0.85, 0.04, 1.5, 0.4),
            Variant("c", 2.2, 0.85, 0.04, 1.2, 0.5),
        ]
        selected = select_variant(variants, alpha=0.05, t_req=2.0, k_req=0.6)
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.name, "c")

    def test_rejects_inadmissible(self) -> None:
        variants = [
            Variant("fast_but_noisy", 2.0, 0.9, 0.2, 1.0, 0.2),
            Variant("slow", 2.0, 0.9, 0.01, 5.0, 0.2),
        ]
        self.assertIsNone(select_variant(variants, alpha=0.05, t_req=2.0, k_req=0.6))

    def test_no_variants(self) -> None:
        self.assertIsNone(select_variant([], alpha=0.05, t_req=2.0, k_req=0.6))


if __name__ == "__main__":
    unittest.main()
