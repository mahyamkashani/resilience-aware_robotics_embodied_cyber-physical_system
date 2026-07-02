#!/usr/bin/env python3
"""
Usage:
    python3 sample_size.py exp13.csv --confidence 0.99 --margin 0.05
"""

import sys
import math
import argparse
import csv
from pathlib import Path


def t_critical(df: int, confidence: float) -> float:
    try:
        from scipy.stats import t
        alpha = 1 - confidence
        return t.ppf(1 - alpha / 2, df)
    except Exception:
        # z approximation (accurate for df >= 30; slightly conservative for small n)
        z = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
        return z.get(confidence, 1.960)


def ci_continuous(values: list[float], confidence: float):
    n = len(values)
    if n < 2:
        return None, None, None
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    t = t_critical(n - 1, confidence)
    margin = t * std / math.sqrt(n)
    return mean, std, margin


def ci_proportion(successes: int, n: int, confidence: float):
    if n == 0:
        return None, None
    p = successes / n
    z = t_critical(n - 1, confidence)
    margin = z * math.sqrt(p * (1 - p) / n) if n > 0 else 0
    return p, margin


def required_n(std: float, margin: float, confidence: float) -> int:
    z = t_critical(999, confidence)  # large df ≈ z
    return math.ceil((z * std / margin) ** 2)


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="Path to result CSV")
    parser.add_argument("--confidence", type=float, default=0.95,
                        help="Confidence level (default 0.95)")
    parser.add_argument("--margin", type=float, default=0.05,
                        help="Target margin of error for sample-size calc (default 0.05)")
    args = parser.parse_args()

    path = Path(args.csv)
    if not path.is_absolute():
        here = Path(__file__).parent
        candidates = [
            here / path,
            here / "framework_correctness" / path,
            here / "task1" / path,
            Path(path),  # relative to cwd
        ]
        for candidate in candidates:
            if candidate.exists():
                path = candidate
                break
        else:
            print(f"Error: could not find '{args.csv}'")
            print("Searched:")
            for c in candidates:
                print(f"  {c}")
            sys.exit(1)

    rows = load_csv(path)
    n = len(rows)
    conf = args.confidence
    target_margin = args.margin

    print(f"\nFile   : {path.name}")
    print(f"Runs   : {n}")
    print(f"CI     : {int(conf*100)}%")
    print(f"Target margin of error: ±{target_margin}")
    print("=" * 60)

    # ── Continuous metrics ──────────────────────────────────────────
    continuous_cols = ["psi", "degradation", "time"]
    for col in continuous_cols:
        vals = []
        for row in rows:
            try:
                vals.append(float(row[col]))
            except (KeyError, ValueError):
                pass
        if not vals:
            continue

        mean, std, margin = ci_continuous(vals, conf)
        n_needed = required_n(std, target_margin, conf) if std > 0 else n

        print(f"\n[{col}]")
        print(f"  mean  = {mean:.4f}")
        print(f"  std   = {std:.4f}")
        print(f"  CI    = [{mean-margin:.4f}, {mean+margin:.4f}]  (±{margin:.4f})")
        if n_needed > n:
            print(f"  → need {n_needed} runs for ±{target_margin} margin  ({n_needed - n} more)")
        else:
            print(f"  → current {n} runs already sufficient for ±{target_margin} margin ✓")

    # ── Binary outcomes ─────────────────────────────────────────────
    print()
    binary = {
        "RESILIENT rate":    [r for r in rows if r.get("resilient") == "RESILIENT"],
        "DONE rate":         [r for r in rows if r.get("result") == "DONE"],
        "NOT RESILIENT rate":[r for r in rows if r.get("resilient") == "NOT RESILIENT"],
        "HALTED rate":       [r for r in rows if r.get("result") == "HALTED"],
    }
    for label, subset in binary.items():
        p, margin = ci_proportion(len(subset), n, conf)
        if p is None:
            continue
        z = t_critical(999, conf)
        # Wilson sample-size for proportions
        p_est = max(p, 0.5)  # conservative: worst case variance at p=0.5
        n_needed = math.ceil(z**2 * p_est * (1 - p_est) / target_margin**2)
        print(f"[{label}]")
        print(f"  p̂ = {p:.3f}  CI = [{max(0,p-margin):.3f}, {min(1,p+margin):.3f}]  (±{margin:.3f})")
        if n_needed > n:
            print(f"  → need {n_needed} runs for ±{target_margin} margin  ({n_needed - n} more)")
        else:
            print(f"  → current {n} runs already sufficient for ±{target_margin} margin ✓")
        print()


if __name__ == "__main__":
    main()
