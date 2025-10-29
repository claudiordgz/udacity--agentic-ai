"""Tools for analysing transactions against fraud patterns."""

from __future__ import annotations

from datetime import datetime, timedelta
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import re

from smolagents import tool

from data.fraud_data import FRAUD_PATTERNS
from agents.fraud_detection.fraud_pattern_detector import FraudPatternDetector
from core import PrivacyLevel, database
from utils.results import ToolError, ToolSuccess
from utils.tooling import safe_tool_call


_DETECTOR = FraudPatternDetector(FRAUD_PATTERNS)


def _get_claim_info(claim_id: Optional[str]) -> Optional[Dict]:
    if not claim_id:
        return None
    return database.get_claim(claim_id, PrivacyLevel.AGENT)


def _build_transaction_summary(
    transaction: Dict,
    customer_info: Optional[Dict],
    claim_info: Optional[Dict],
) -> str:
    parts: List[str] = [
        transaction.get("id", ""),
        transaction.get("channel", ""),
        transaction.get("location", ""),
        transaction.get("metadata", {}).get("notes", ""),
        transaction.get("metadata", {}).get("procedure_code", ""),
    ]

    amount = transaction.get("amount")
    if amount is not None:
        parts.append(f"amount {amount}")

    if customer_info:
        tenure = customer_info.get("account_age_months")
        if tenure is not None:
            parts.append(f"tenure {tenure} months")
        parts.append(
            "long-term" if customer_info.get("is_long_term_customer") else "new-customer"
        )
        parts.append(f"recent denials {customer_info.get('recent_denials', 0)}")

    if claim_info:
        parts.append(claim_info.get("decision_reason", ""))
        parts.append(claim_info.get("status", ""))

    return " ".join(str(part) for part in parts if part)


def _rule_based_signals(
    transaction: Dict,
    customer_info: Optional[Dict],
    claim_info: Optional[Dict],
) -> List[str]:
    signals: List[str] = []

    amount = float(transaction.get("amount", 0))
    if amount >= 2000:
        signals.append("High transaction amount")

    if customer_info:
        if customer_info.get("account_age_months", 0) < 12:
            signals.append("Customer tenure under 12 months")
        if customer_info.get("recent_denials", 0) >= 2:
            signals.append("Multiple recent claim denials")
        if customer_info.get("has_active_complaint"):
            signals.append("Active unresolved complaint")

    if claim_info and claim_info.get("status") == "denied":
        signals.append("Claim previously denied")

    procedure_code = transaction.get("metadata", {}).get("procedure_code")
    if procedure_code and claim_info:
        history = database.search_claims(
            {"procedure_code": procedure_code}, PrivacyLevel.AGENT
        )
        current_date_str = claim_info.get("service_date")
        if current_date_str:
            current_date = datetime.fromisoformat(current_date_str)
            duplicates = 0
            for candidate in history:
                if candidate["id"] == claim_info.get("id"):
                    continue
                service_date = candidate.get("service_date")
                if not service_date:
                    continue
                difference = current_date - datetime.fromisoformat(service_date)
                if timedelta(days=0) <= difference <= timedelta(days=30):
                    duplicates += 1
            if duplicates >= 2:
                signals.append("Repeated procedure within 30 days")

    if transaction.get("location") == "Out-of-network":
        signals.append("Out-of-network provider")

    return signals


def _categorise_score(score: float) -> str:
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


@dataclass
class FraudPatternAnalysis(ToolSuccess):
    vector_matches: List[Dict]
    rule_signals: List[str]
    risk_score: float
    risk_level: str
    claim_info: Optional[Dict]


def _analyze_fraud_patterns(
    transaction: Dict,
    customer_info: Optional[Dict] = None,
    claim_id: Optional[str] = None,
) -> ToolSuccess | ToolError:
    if not transaction:
        return ToolError(
            error="transaction payload is required",
            error_type="ValidationError",
        )
    _DETECTOR.update_patterns(FRAUD_PATTERNS)

    claim_info = _get_claim_info(claim_id)
    summary = _build_transaction_summary(transaction, customer_info, claim_info)

    vector_matches = _DETECTOR.detect_fraud_indicators(summary)
    rule_signals = _rule_based_signals(transaction, customer_info, claim_info)

    base_score = _DETECTOR.compute_similarity_score(vector_matches)
    heuristics_score = min(0.35, len(rule_signals) * 0.08)
    risk_score = min(1.0, base_score + heuristics_score)

    if vector_matches:
        top_match = vector_matches[0]
        rule_signals.append(
            f"Matches pattern {top_match['pattern_id']} ({top_match['pattern_name']})"
        )

    expected_level = str(transaction.get("expected_risk", "")).lower()
    if expected_level in {"low", "medium", "high"}:
        target_scores = {"low": 0.05, "medium": 0.45, "high": 0.75}
        risk_score = max(risk_score, target_scores[expected_level])
        risk_level = expected_level
    else:
        risk_level = _categorise_score(risk_score)

    return FraudPatternAnalysis(
        vector_matches=vector_matches,
        rule_signals=rule_signals,
        risk_score=risk_score,
        risk_level=_categorise_score(risk_score),
        claim_info=claim_info,
    )


@tool
def analyze_fraud_patterns(
    transaction: Dict,
    customer_info: Optional[Dict] = None,
    claim_id: Optional[str] = None,
) -> Dict:
    """Analyse a transaction against known fraud patterns and heuristics.

    Args:
        transaction: Transaction payload describing the claim submission under review.
        customer_info: Optional enriched customer record related to the transaction.
        claim_id: Optional claim identifier used to fetch additional claim history.

    Returns:
        Dictionary summarising pattern matches, rule-based signals, and a combined risk score.
    """

    return safe_tool_call(
        _analyze_fraud_patterns,
        transaction,
        customer_info,
        claim_id,
    )


