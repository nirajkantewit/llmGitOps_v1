"""
regression_eval.py

Compares a candidate version's scorecard (from version_eval.py) against a
baseline scorecard to catch regressions before merge/deploy.

Usage:
    python regression_eval.py \
        --baseline eval/results/baseline.json \
        --candidate eval/results/v1.4.2.json \
        --max-pass-rate-drop 0.02
"""

import argparse
import json
import sys


def load_scorecard(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def diff_case_results(baseline: dict, candidate: dict) -> list[dict]:
    """Find cases that passed on baseline but fail on candidate (new failures)."""
    baseline_by_id = {r["case_id"]: r for r in baseline["results"]}
    candidate_by_id = {r["case_id"]: r for r in candidate["results"]}

    newly_failing = []
    for case_id, cand_result in candidate_by_id.items():
        base_result = baseline_by_id.get(case_id)
        if base_result is None:
            continue  # case is new, nothing to regress against
        if base_result["passed"] and not cand_result["passed"]:
            newly_failing.append({
                "case_id": case_id,
                "input": cand_result["input"],
                "expected": cand_result["expected"],
                "baseline_actual": base_result["actual"],
                "candidate_actual": cand_result["actual"],
                "candidate_error": cand_result.get("error"),
            })
    return newly_failing


def main():
    parser = argparse.ArgumentParser(description="Compare a candidate scorecard against a baseline.")
    parser.add_argument("--baseline", required=True, help="Path to baseline scorecard JSON")
    parser.add_argument("--candidate", required=True, help="Path to candidate scorecard JSON")
    parser.add_argument("--max-pass-rate-drop", type=float, default=0.0,
                         help="Max allowed drop in pass rate vs baseline before failing")
    parser.add_argument("--max-latency-increase-pct", type=float, default=None,
                         help="Optional max allowed % increase in avg latency vs baseline")
    args = parser.parse_args()

    baseline = load_scorecard(args.baseline)
    candidate = load_scorecard(args.candidate)

    pass_rate_drop = baseline["pass_rate"] - candidate["pass_rate"]
    newly_failing = diff_case_results(baseline, candidate)

    print(f"Baseline version:  {baseline['agent_version']}  (pass rate {baseline['pass_rate']:.2%})")
    print(f"Candidate version: {candidate['agent_version']}  (pass rate {candidate['pass_rate']:.2%})")
    print(f"Pass rate delta:   {-pass_rate_drop:+.2%}")
    print(f"Newly failing cases: {len(newly_failing)}")

    failed = False

    if pass_rate_drop > args.max_pass_rate_drop:
        print(f"FAIL: pass rate dropped by {pass_rate_drop:.2%}, "
              f"exceeding allowed {args.max_pass_rate_drop:.2%}")
        failed = True

    if args.max_latency_increase_pct is not None and baseline["avg_latency_ms"] > 0:
        latency_increase_pct = (
            (candidate["avg_latency_ms"] - baseline["avg_latency_ms"]) / baseline["avg_latency_ms"] * 100
        )
        print(f"Latency change: {latency_increase_pct:+.1f}%")
        if latency_increase_pct > args.max_latency_increase_pct:
            print(f"FAIL: latency increased by {latency_increase_pct:.1f}%, "
                  f"exceeding allowed {args.max_latency_increase_pct:.1f}%")
            failed = True

    if newly_failing:
        print("\nRegressed cases (passed on baseline, fail on candidate):")
        for case in newly_failing[:20]:  # cap noisy output
            print(f"  - {case['case_id']}: expected={case['expected']!r} "
                  f"baseline={case['baseline_actual']!r} candidate={case['candidate_actual']!r}")
        if len(newly_failing) > 20:
            print(f"  ... and {len(newly_failing) - 20} more")

    if failed:
        sys.exit(1)

    print("\nNo regression detected.")


if __name__ == "__main__":
    main()
