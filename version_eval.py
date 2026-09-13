"""
version_eval.py

Runs the evaluation suite against a single, specific version of an agent
and produces a scorecard. This does NOT compare against a baseline -
that's the job of regression_eval.py, which consumes this script's output.

Typical pipeline:
    prep_eval.py  -->  version_eval.py  -->  regression_eval.py

Usage:
    python version_eval.py --agent-version v1.4.2 --dataset test_cases.jsonl --out results/v1.4.2.json
"""

import argparse
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# 1. Data structures
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    id: str
    input: str
    expected: Any
    metadata: dict = field(default_factory=dict)


@dataclass
class CaseResult:
    case_id: str
    input: str
    expected: Any
    actual: Any
    passed: bool
    latency_ms: float
    error: str | None = None


@dataclass
class ScoreCard:
    agent_version: str
    run_id: str
    timestamp: float
    total_cases: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    avg_latency_ms: float
    results: list[CaseResult]


# ---------------------------------------------------------------------------
# 2. Plug in your agent + dataset loading here
# ---------------------------------------------------------------------------

def load_dataset(path: str) -> list[TestCase]:
    """Load test cases from a JSONL file: {"id":..., "input":..., "expected":...}"""
    cases = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            cases.append(TestCase(
                id=obj.get("id", str(uuid.uuid4())),
                input=obj["input"],
                expected=obj.get("expected"),
                metadata=obj.get("metadata", {}),
            ))
    return cases


def load_agent(agent_version: str) -> Callable[[str], Any]:
    """
    Return a callable that runs the agent for a given version.
    Currently wired to the simple rule-based agent in agent.py so the
    pipeline runs end-to-end. Swap this out for real agent-loading logic
    (a specific model checkpoint, a versioned API endpoint, etc.) whenever
    you're ready to evaluate a real agent instead.
    """
    import agent as agent_module

    def run_agent(input_text: str) -> Any:
        return agent_module.run(input_text, version=agent_version)

    return run_agent


def grade(expected: Any, actual: Any) -> bool:
    """
    Replace with your real grading logic:
      - exact match
      - semantic similarity / LLM-as-judge
      - tool-call correctness
      - task completion check
    """
    return expected == actual


# ---------------------------------------------------------------------------
# 3. Core version eval runner
# ---------------------------------------------------------------------------

def run_version_eval(agent_version: str, dataset_path: str) -> ScoreCard:
    cases = load_dataset(dataset_path)
    agent = load_agent(agent_version)

    results: list[CaseResult] = []
    total_latency = 0.0
    passed = failed = errors = 0

    for case in cases:
        start = time.perf_counter()
        error = None
        actual = None
        ok = False

        try:
            actual = agent(case.input)
            ok = grade(case.expected, actual)
        except Exception as e:
            error = str(e)

        latency_ms = (time.perf_counter() - start) * 1000
        total_latency += latency_ms

        if error is not None:
            errors += 1
        elif ok:
            passed += 1
        else:
            failed += 1

        results.append(CaseResult(
            case_id=case.id,
            input=case.input,
            expected=case.expected,
            actual=actual,
            passed=ok and error is None,
            latency_ms=latency_ms,
            error=error,
        ))

    total = len(cases)
    scorecard = ScoreCard(
        agent_version=agent_version,
        run_id=str(uuid.uuid4()),
        timestamp=time.time(),
        total_cases=total,
        passed=passed,
        failed=failed,
        errors=errors,
        pass_rate=passed / total if total else 0.0,
        avg_latency_ms=total_latency / total if total else 0.0,
        results=results,
    )
    return scorecard


def save_scorecard(scorecard: ScoreCard, out_path: str):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(asdict(scorecard), f, indent=2, default=str)


# ---------------------------------------------------------------------------
# 4. CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run a version eval for an agent.")
    parser.add_argument("--agent-version", required=True, help="Version identifier of the agent being evaluated")
    parser.add_argument("--dataset", required=True, help="Path to JSONL test cases")
    parser.add_argument("--out", required=True, help="Where to write the scorecard JSON")
    parser.add_argument("--min-pass-rate", type=float, default=None,
                         help="Optional threshold; exits non-zero if pass rate is below this")
    args = parser.parse_args()

    scorecard = run_version_eval(args.agent_version, args.dataset)
    save_scorecard(scorecard, args.out)

    print(f"Version: {scorecard.agent_version}")
    print(f"Total cases: {scorecard.total_cases}")
    print(f"Passed: {scorecard.passed}  Failed: {scorecard.failed}  Errors: {scorecard.errors}")
    print(f"Pass rate: {scorecard.pass_rate:.2%}")
    print(f"Avg latency: {scorecard.avg_latency_ms:.1f} ms")
    print(f"Scorecard written to: {args.out}")

    if args.min_pass_rate is not None and scorecard.pass_rate < args.min_pass_rate:
        print(f"FAILED: pass rate {scorecard.pass_rate:.2%} is below threshold {args.min_pass_rate:.2%}")
        exit(1)


if __name__ == "__main__":
    main()
