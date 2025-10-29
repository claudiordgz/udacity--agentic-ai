from __future__ import annotations

from agents.fraud_detection.tools import (
    FraudDetectionPayload,
    _check_transaction_for_fraud,
    check_transaction_for_fraud,
)


def test_check_transaction_for_fraud_success(demo_data: None) -> None:
    result = _check_transaction_for_fraud("TXN-FD-001")
    assert isinstance(result, FraudDetectionPayload)
    assert result.transaction["id"] == "TXN-FD-001"

    payload = check_transaction_for_fraud("TXN-FD-001")
    assert payload["success"] is True
    assert payload["transaction"]["id"] == "TXN-FD-001"


def test_check_transaction_for_fraud_validation_error() -> None:
    payload = check_transaction_for_fraud("")
    assert payload["success"] is False
    assert payload["error_type"] == "ValidationError"

