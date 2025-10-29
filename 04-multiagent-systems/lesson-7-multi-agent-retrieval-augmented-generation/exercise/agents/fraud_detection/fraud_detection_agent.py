"""Fraud detection agent combining retrieval and synthesis capabilities."""

from __future__ import annotations

from typing import Dict

from smolagents import ToolCallingAgent

from agents.fraud_detection.tools import (
    _check_transaction_for_fraud,
    FraudDetectionPayload,
    check_transaction_for_fraud,
)
from core import PrivacyLevel
from utils.results import ToolError


class FraudDetectionAgent(ToolCallingAgent):
    """Agent for detecting potential fraud in insurance claims."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[check_transaction_for_fraud],
            model=model,
            name="fraud_detection",
            description="Assess insurance transactions for potential fraud risk.",
        )

    def evaluate_transaction(self, transaction_id: str) -> Dict:
        result = _check_transaction_for_fraud(
            transaction_id,
            PrivacyLevel.AGENT,
        )

        if isinstance(result, FraudDetectionPayload):
            return result.to_dict()

        if isinstance(result, ToolError):
            return result.to_dict()

        if isinstance(result, dict):
            return result

        return {
            "success": False,
            "error": "Unexpected result from fraud detection pipeline",
            "error_type": "TypeError",
        }


