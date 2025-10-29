"""Evaluator for the lesson 7 fraud detection exercise using LLM demos."""

from __future__ import annotations

import sys
from typing import Dict, List

from demos import demo_complaint_resolution, demo_fraud_assessment
from core import reset_database
from data.fraud_data import seed_demo_records


class FraudDetectionEvaluator:
    """Runs LLM-backed integration tests for the fraud detection workflow."""

    def __init__(self) -> None:
        self.results: List[Dict] = []

    def _record(self, name: str, passed: bool, issues: List[str], details: Dict) -> None:
        self.results.append(
            {
                "name": name,
                "passed": passed,
                "issues": issues,
                "details": details,
            }
        )

    def test_transaction(self, transaction_id: str, expected_risk: str) -> None:
        result = demo_fraud_assessment(transaction_id)
        issues: List[str] = []

        deterministic = result.get("deterministic") or {}
        report = deterministic.get("report", {}) if isinstance(deterministic, dict) else {}
        risk_level = report.get("risk_level")
        if not risk_level:
            issues.append("Risk level missing from deterministic evaluation")
        elif str(risk_level).lower() != expected_risk.lower():
            issues.append(f"Expected risk level '{expected_risk}', received '{risk_level}'")

        self._record(
            name=f"Fraud Assessment for {transaction_id}",
            passed=len(issues) == 0,
            issues=issues,
            details={
                "transaction_id": transaction_id,
                "deterministic": deterministic,
            },
        )

    def test_error_responses(self) -> None:
        from agents.transaction_data.tools import get_transaction_details
        from agents.customer_data.tools import get_customer_details
        from tools.common_tools import get_claim_details

        tests = [
            ("Unknown Transaction", get_transaction_details, {"transaction_id": "UNKNOWN"}),
            ("Unknown Customer", get_customer_details, {"customer_id": 999999}),
            ("Unknown Claim", get_claim_details, {"claim_id": "CLM-UNKNOWN", "access_level": "agent"}),
        ]

        for name, func, kwargs in tests:
            result = func(**kwargs)
            issues: List[str] = []
            if result.get("success", True):
                issues.append("Expected failure response but received success=True")
            if "error" not in result:
                issues.append("Error message missing from failure response")
            if "error_type" not in result:
                issues.append("Error type missing from failure response")

            self._record(
                name=f"Error Handling - {name}",
                passed=len(issues) == 0,
                issues=issues,
                details=result,
            )

    def test_complaint_resolution(self) -> None:
        result = demo_complaint_resolution(
            patient_id=880001,
            claim_id="CLM-FD-001",
            complaint_text="I think this duplicate billing denial is incorrect.",
        )
        issues: List[str] = []

        deterministic = result.get("deterministic") or {}
        if not deterministic.get("success"):
            issues.append(f"Complaint workflow failed: {deterministic}")
        elif not deterministic.get("resolution"):
            issues.append("Resolution text missing from complaint workflow result")

        self._record(
            name="Complaint Resolution Workflow",
            passed=len(issues) == 0,
            issues=issues,
            details={
                "deterministic": deterministic,
            },
        )

    def run(self) -> bool:
        print("\n=== Fraud Detection LLM Evaluation ===\n")
        reset_database()
        seed_demo_records()

        # Transactions seeded in fraud_data.py
        self.test_transaction("TXN-FD-001", expected_risk="high")
        self.test_transaction("TXN-FD-002", expected_risk="medium")
        self.test_transaction("TXN-FD-003", expected_risk="low")
        self.test_complaint_resolution()
        self.test_error_responses()

        passed = sum(1 for r in self.results if r["passed"])  # type: ignore[index]
        failed = len(self.results) - passed

        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")

        if failed:
            print("\nFailed Tests Details:")
            for record in self.results:
                if not record["passed"]:
                    print(f"- {record['name']}")
                    for issue in record["issues"]:
                        print(f"  * {issue}")

        return failed == 0


def run_evaluation() -> None:
    evaluator = FraudDetectionEvaluator()
    success = evaluator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    run_evaluation()


