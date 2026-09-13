"""
prep_eval.py

Sanity-checks that everything is ready before running version_eval.py:
  - the dataset file exists, is valid JSONL, and every case has required fields
  - there are no duplicate case IDs
  - the agent for the target version can actually be loaded/reached
  - (optional) a lightweight smoke-test call succeeds

Fails fast (non-zero exit) so you don't burn a full eval run on a broken
dataset or an unreachable agent/API.

Usage:
    python prep_eval.py --dataset eval/data/test_cases.jsonl --agent-version v1.4.2
"""

import argparse
import json
import sys
from pathlib import Path


def check_dataset(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        print(f"FAIL: dataset not found at {path}")
        sys.exit(1)

    cases = []
    seen_ids = set()
    errors = []

    with open(p, "r") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"  line {line_no}: invalid JSON ({e})")
                continue

            if "input" not in obj:
                errors.append(f"  line {line_no}: missing required field 'input'")
            if "expected" not in obj:
                errors.append(f"  line {line_no}: missing required field 'expected'")

            case_id = obj.get("id")
            if case_id is not None:
                if case_id in seen_ids:
                    errors.append(f"  line {line_no}: duplicate case id '{case_id}'")
                seen_ids.add(case_id)

            cases.append(obj)

    if not cases:
        errors.append("  dataset is empty")

    if errors:
        print(f"FAIL: dataset validation failed ({len(errors)} issue(s)):")
        for e in errors:
            print(e)
        sys.exit(1)

    print(f"OK: dataset valid - {len(cases)} test case(s), {len(seen_ids)} unique id(s)")
    return cases


def check_agent(agent_version: str, smoke_test: bool):
    """
    Checks that the agent is ready to be evaluated. Currently checks that
    agent.py (the simple rule-based agent) can be imported and called.
    When you swap in a real agent, replace this with real checks for your
    setup, e.g.: required env vars / API keys, a model registry lookup, or
    an endpoint health check.
    """
    try:
        import agent as agent_module
    except ImportError as e:
        print(f"FAIL: could not import agent.py: {e}")
        sys.exit(1)

    print(f"OK: agent module importable for version '{agent_version}'")

    if smoke_test:
        try:
            result = agent_module.run("What is 2 + 2?", version=agent_version)
            print(f"OK: smoke test call succeeded (returned {result!r})")
        except Exception as e:
            print(f"FAIL: smoke test call failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Prep checks before running a version eval.")
    parser.add_argument("--dataset", required=True, help="Path to JSONL test cases")
    parser.add_argument("--agent-version", required=True, help="Version identifier to prep-check")
    parser.add_argument("--smoke-test", action="store_true",
                         help="Also make a live smoke-test call to the agent")
    args = parser.parse_args()

    check_dataset(args.dataset)
    check_agent(args.agent_version, smoke_test=args.smoke_test)

    print("Prep eval passed - ready for version eval.")


if __name__ == "__main__":
    main()
