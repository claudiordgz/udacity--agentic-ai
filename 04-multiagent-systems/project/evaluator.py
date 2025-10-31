"""Entry point for running agent evaluators."""

from __future__ import annotations

import argparse
import json
from typing import Callable, Dict, List, Tuple

from evaluator import (
    evaluate_business_orchestrator,
    evaluate_customer_insights_agent,
    evaluate_inventory_agent,
    evaluate_ordering_agent,
    evaluate_quoting_agent,
)
from evaluator.common import get_model


Evaluator = Callable[..., Dict]


EVALUATORS: List[Tuple[str, Evaluator]] = [
    ("inventory", evaluate_inventory_agent),
    ("quoting", evaluate_quoting_agent),
    ("ordering", evaluate_ordering_agent),
    ("customer_insights", evaluate_customer_insights_agent),
    ("orchestrator", evaluate_business_orchestrator),
]


def run_all_evaluators(*, offline: bool = False) -> Dict[str, Dict]:
    """Execute each evaluator and return a structured report."""

    model = get_model(require_api_key=not offline)
    report: Dict[str, Dict] = {}
    for name, evaluator in EVALUATORS:
        try:
            payload = evaluator(model=model, offline=offline)
            report[name] = {"status": "passed", "details": payload}
        except Exception as exc:  # pylint: disable=broad-except
            report[name] = {"status": "failed", "error": str(exc)}
    return report


def summarise(report: Dict[str, Dict]) -> None:
    """Pretty-print evaluator outcomes to stdout."""

    print("===== AGENT EVALUATION RESULTS =====")
    for name, result in report.items():
        status = result.get("status", "unknown").upper()
        print(f"- {name}: {status}")
        if status != "PASSED":
            print(f"  error: {result.get('error')}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run agent evaluators.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results as JSON instead of human-readable output.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run evaluators using deterministic methods without invoking the LLM.",
    )
    args = parser.parse_args()

    report = run_all_evaluators(offline=args.offline)
    failed = any(result.get("status") != "passed" for result in report.values())

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        summarise(report)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

