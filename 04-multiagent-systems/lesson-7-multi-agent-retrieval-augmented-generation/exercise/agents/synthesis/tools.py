"""Tools for synthesising fraud detection reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from smolagents import tool

from utils.results import ToolError, ToolSuccess
from utils.tooling import safe_tool_call


def _categorise(score: float) -> str:
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


@dataclass
class SynthesisReport(ToolSuccess):
    transaction_id: str | None
    risk_level: str
    risk_score: float
    reasons: List[str]
    text: str


def _synthesize_fraud_report(context: Dict) -> ToolSuccess | ToolError:
    if not context:
        return ToolError("context is required", error_type="ValidationError")
    transaction = context.get("transaction", {})
    customer_info = context.get("customer_info")
    fraud_analysis = context.get("fraud_analysis", {})

    risk_score = float(fraud_analysis.get("risk_score", 0.0))
    risk_level = fraud_analysis.get("risk_level") or _categorise(risk_score)
    reasons: List[str] = list(fraud_analysis.get("rule_signals", []))

    if customer_info:
        if (
            transaction.get("amount", 0) > 1500
            and not customer_info.get("is_long_term_customer", False)
        ):
            risk_score = min(1.0, risk_score + 0.1)
            reasons.append("Large amount from new customer")

        avg = customer_info.get("average_claim_amount")
        current = transaction.get("amount")
        if avg and current and current > avg * 2.5:
            risk_score = min(1.0, risk_score + 0.08)
            reasons.append("Amount significantly exceeds customer average")

    if fraud_analysis.get("vector_matches"):
        top_match = fraud_analysis["vector_matches"][0]
        reasons.append(
            f"Closest pattern: {top_match['pattern_id']} ({top_match['pattern_name']})"
        )

    risk_level = _categorise(risk_score)

    report_lines = [
        f"Fraud Check Report for Transaction {transaction.get('id', 'unknown')}",
        f"Risk Level: {risk_level.title()} ({risk_score:.2f})",
    ]

    if customer_info:
        tenure = customer_info.get("account_age_months", 0)
        report_lines.append(
            f"Customer Tenure: {tenure} months | Recent Denials: {customer_info.get('recent_denials', 0)}"
        )

    amount = transaction.get("amount")
    channel = transaction.get("channel", "unknown")
    report_lines.append(f"Amount: ${amount:.2f} | Channel: {channel}" if amount else f"Channel: {channel}")

    if reasons:
        report_lines.append("Key Signals:")
        for reason in reasons:
            report_lines.append(f" - {reason}")

    return SynthesisReport(
        transaction_id=transaction.get("id"),
        risk_level=risk_level,
        risk_score=risk_score,
        reasons=reasons,
        text="\n".join(report_lines),
    )


@tool
def synthesize_fraud_report(context: Dict) -> Dict:
    """Generate a textual fraud report from aggregated context.

    Args:
        context: Dictionary containing transaction, customer, and fraud analysis artefacts.

    Returns:
        Dictionary with the report text, risk level, score, and contributing reasons.
    """

    return safe_tool_call(_synthesize_fraud_report, context)


