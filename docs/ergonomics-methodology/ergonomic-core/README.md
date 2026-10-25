# Ergonomic core: analytical model

Implementation of the formal model in `../2026-10-25_formal-model.md`.

The model separates:

- **technical layer** — detector `P_D`, `P_FA`, latency;
- **ergonomic layer** — effective sensitivity `d' = eta_IM * d'_tech`, operator criterion, `P_det`, `P_fa`, `T_det`, `K_load`;
- **decision layer** — deterministic constraints and selection without weights.

## Run

```bash
cd docs/ergonomics-methodology/ergonomic-core
python3 -m unittest -v
```

## Minimal use

```python
from model import evaluate_variant, select_variant

variants = [
    evaluate_variant(
        name="im-a",
        detector_d_prime=2.6,
        im_efficiency=0.8,
        alpha=0.05,
        t_lat=0.2,
        elements=40,
        visual_span=7,
        feature_elements=3,
        fixation=0.2,
        n_alternatives=3,
        decision_intercept=0.3,
        decision_slope=0.2,
        t_act=0.3,
        n_anomalies=10,
        n_false_alarms=5,
        t_check=4.0,
        t_shift=3600.0,
    ),
]
selected = select_variant(variants, alpha=0.05, t_req=2.0, k_req=0.6)
print(selected)
```

The numbers in this example are illustrative only; they are not experimental
results and must not be reported as such.  Real values for `P_D`, `P_FA`,
`eta_IM`, `T_check`, anomaly rates, and thresholds must come from the
benchmark/telemetry or a documented pilot.
