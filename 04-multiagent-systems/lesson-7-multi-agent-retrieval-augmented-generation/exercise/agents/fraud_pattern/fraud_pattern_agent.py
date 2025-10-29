"""Agent for checking transactions against the fraud knowledge base."""

from __future__ import annotations

from typing import Dict, Optional

from smolagents import ToolCallingAgent

from config import model
from agents.fraud_pattern.tools import (
    _analyze_fraud_patterns,
    FraudPatternAnalysis,
    analyze_fraud_patterns,
)
from utils.results import ToolError


class FraudPatternAgent(ToolCallingAgent):
    """Check transactions against known fraud patterns using smolagents tools."""

    def __init__(self) -> None:
        super().__init__(
            tools=[analyze_fraud_patterns],
            model=model,
            name="fraud_pattern_agent",
            description="Analyse transactions for similarities to known fraud patterns.",
        )

    def check_fraud_patterns(
        self,
        transaction: Dict,
        customer_info: Optional[Dict] = None,
        claim_id: Optional[str] = None,
    ) -> Dict:
        """Convenience wrapper for the analyze_fraud_patterns tool."""

        result = _analyze_fraud_patterns(
            transaction=transaction,
            customer_info=customer_info,
            claim_id=claim_id,
        )

        if isinstance(result, FraudPatternAnalysis):
            return result.to_dict()

        if isinstance(result, ToolError):
            return result.to_dict()

        if isinstance(result, dict):
            return result

        return {}


