from __future__ import annotations

from agents.fraud_pattern.tools import (
    FraudPatternAnalysis,
    _analyze_fraud_patterns,
    analyze_fraud_patterns,
)


def test_analyze_fraud_patterns_success(demo_data: None) -> None:
    transaction = {
        "id": "TXN-FD-001",
        "amount": 2450.0,
        "metadata": {"procedure_code": "97110"},
    }

    result = _analyze_fraud_patterns(transaction, claim_id="CLM-FD-001")
    assert isinstance(result, FraudPatternAnalysis)
    assert result.risk_level in {"high", "medium", "low"}

    payload = analyze_fraud_patterns(transaction, claim_id="CLM-FD-001")
    assert payload["success"] is True
    assert "risk_level" in payload


def test_analyze_fraud_patterns_invalid_transaction() -> None:
    result = _analyze_fraud_patterns(None)
    assert result.to_dict()["success"] is False

    payload = analyze_fraud_patterns(None)
    assert payload["success"] is False
    assert payload["error_type"] == "ValidationError"

