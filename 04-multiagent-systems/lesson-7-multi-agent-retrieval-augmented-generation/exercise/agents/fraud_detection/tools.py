"""Tools for the fraud detection orchestrator agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from smolagents import tool

from agents.retrieval_coordinator.retrieval_coordinator import RetrievalCoordinator
from agents.synthesis.synthesis_agent import SynthesisAgent
from core import AccessControl, PrivacyLevel
from utils.results import ToolError, ToolSuccess
from utils.tooling import safe_tool_call


@dataclass
class FraudDetectionPayload(ToolSuccess):
    transaction: Dict
    fraud_analysis: Dict
    report: Dict
    customer_info: Optional[Dict] = None
    claim_info: Optional[Dict] = None


def _check_transaction_for_fraud(
    transaction_id: str,
    access_level: str = PrivacyLevel.AGENT,
) -> ToolSuccess | ToolError:
    if not transaction_id:
        return ToolError(
            error="transaction_id is required",
            error_type="ValidationError",
        )
    if not AccessControl.can_access(access_level, PrivacyLevel.AGENT):
        return ToolError(
            error="Access denied for fraud assessment.",
            error_type="AccessDeniedError",
        )

    coordinator = RetrievalCoordinator()
    context = coordinator.run(transaction_id)

    synthesis_agent = SynthesisAgent()
    report = synthesis_agent.synthesize_report(context)

    return FraudDetectionPayload(
        transaction=context["transaction"],
        customer_info=context.get("customer_info"),
        claim_info=context.get("claim_info"),
        fraud_analysis=context.get("fraud_analysis", {}),
        report=report,
    )


@tool
def check_transaction_for_fraud(
    transaction_id: str,
    access_level: str = PrivacyLevel.AGENT,
) -> Dict:
    """Run the full fraud detection workflow for a transaction.

    Args:
        transaction_id: Identifier of the transaction to analyse for potential fraud.
        access_level: Privacy level of the caller, used for access control validation.

    Returns:
        Dictionary containing the fraud assessment report or an error message.
    """

    return safe_tool_call(_check_transaction_for_fraud, transaction_id, access_level)


