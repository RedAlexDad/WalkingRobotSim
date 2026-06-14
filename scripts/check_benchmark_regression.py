#!/usr/bin/env python3
"""Compare benchmark results against baseline with regression threshold.

Usage:
  python3 scripts/check_benchmark_regression.py <benchmark_output.txt>
  python3 scripts/check_benchmark_regression.py <benchmark_output.txt> --threshold 15.0
  python3 scripts/check_benchmark_regression.py <benchmark_output.txt> --update-baseline
"""

import json
import re
import sys
import os

BASELINE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".benchmark_baseline.json")
DEFAULT_THRESHOLD_PCT = 20.0


def parse_benchmark_output(text: str) -> dict[str, float]:
    """Parse lines between BENCHMARK_JSON_START and BENCHMARK_JSON_END.

    Expected format:  MetricName: value
    """
    results = {}
    in_block = False
    for line in text.splitlines():
        if "BENCHMARK_JSON_START" in line:
            in_block = True
            continue
        if "BENCHMARK_JSON_END" in line:
            in_block = False
            continue
        if not in_block:
            continue
        m = re.match(r"^(\S[^:]+):\s+([\d.]+(?:e[+-]?\d+)?)\s*$", line)
        if m:
            name = m.group(1).strip()
            value = float(m.group(2))
            results[name] = value
    return results


def load_baseline() -> dict:
    with open(BASELINE_PATH) as f:
        return json.load(f)


def save_baseline(results: dict):
    baseline = load_baseline()
    baseline["benchmarks"] = results
    baseline["_meta"]["created"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)
        f.write("\n")
    print(f"Baseline updated: {BASELINE_PATH}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <benchmark_output.txt> [--threshold N] [--update-baseline]")
        sys.exit(1)

    txt_path = sys.argv[1]
    threshold_pct = DEFAULT_THRESHOLD_PCT
    update_baseline = False

    for arg in sys.argv[2:]:
        if arg.startswith("--threshold"):
            try:
                threshold_pct = float(arg.split("=")[1] if "=" in arg else sys.argv[sys.argv.index(arg) + 1])
            except (IndexError, ValueError):
                pass
        elif arg == "--update-baseline":
            update_baseline = True

    with open(txt_path) as f:
        text = f.read()

    results = parse_benchmark_output(text)
    if not results:
        print("ERROR: No benchmark results found in output")
        sys.exit(1)

    print(f"{'Metric':<55} {'Current (us)':<15} {'Baseline (us)':<15} {'Change':<10}  Status")
    print("-" * 105)

    baseline_data = load_baseline()
    baseline = baseline_data.get("benchmarks", {})
    meta_threshold = baseline_data.get("_meta", {}).get("threshold_pct", threshold_pct)
    threshold = threshold_pct if threshold_pct != DEFAULT_THRESHOLD_PCT else meta_threshold

    any_regression = False
    for name in sorted(results.keys(), key=lambda x: results[x], reverse=True):
        cur = results[name]
        bl = baseline.get(name)
        if bl is None:
            status = "  NEW"
            change_str = "N/A"
            pct = 0.0
        else:
            if bl > 0:
                pct = (cur - bl) / bl * 100.0
            else:
                pct = 0.0 if cur == 0 else float("inf")
            change_str = f"{pct:+.1f}%"
            if pct > threshold:
                status = "  FAIL"
                any_regression = True
            elif pct < -threshold:
                status = "  GOOD (faster)"
            else:
                status = "  PASS"

        print(f"{name:<55} {cur:<15.4f} {bl if bl is not None else 0.0:<15.4f} {change_str:<10} {status}")

    print("-" * 105)
    if update_baseline:
        save_baseline(results)
        print("Baseline updated, no regression check performed.")
        sys.exit(0)

    if any_regression:
        print(f"\nFAILURE: Regression detected (threshold: {threshold:.0f}%)")
        sys.exit(1)
    else:
        print(f"\nOK: No significant regression (threshold: {threshold:.0f}%)")
        sys.exit(0)


if __name__ == "__main__":
    main()
