"""Evaluator for the business orchestrator agent."""

from __future__ import annotations

from typing import Dict, Optional

from agents import BusinessOrchestrator, OrchestratorConfig
from evaluator.common import assert_tool_called, ensure_seed, get_model


REQUEST_TEXT = (
    "I would like to request the following paper supplies for the ceremony:\n\n"
    "- 200 sheets of A4 glossy paper\n"
    "- 100 sheets of heavy cardstock (white)\n"
    "- 100 sheets of colored paper (assorted colors)\n"
    "\nPlease deliver by April 15, 2025."
)


def evaluate_business_orchestrator(
    *, model: Optional[object] = None, offline: bool = False
) -> Dict:
    """Ensure the orchestrator coordinates agents and returns a rich response."""

    ensure_seed()
    model_instance = get_model(model, require_api_key=not offline)
    orchestrator = BusinessOrchestrator(model_instance, OrchestratorConfig(enable_llm=not offline))

    if not offline:
        task = (
            "Process the following customer request and respond concisely:"
            f"\n\n{REQUEST_TEXT}\n\nUse your tools to gather details and note restock needs."
        )
        result = orchestrator.run(task)
        assert_tool_called(orchestrator, result, "process_customer_request_tool")

    result = orchestrator.handle_request(REQUEST_TEXT, "2025-04-01")

    required_keys = {"items", "quote", "restock", "orders", "financial_report", "response_text"}
    missing = required_keys - result.keys()
    if missing:
        raise AssertionError(f"Orchestrator response missing keys: {missing}")
    if result["quote"]["total"] <= 0:
        raise AssertionError("Quote total should be positive")
    if "Glossy paper" not in result["response_text"]:
        raise AssertionError("Response text should reference requested items")

    return {
        "quote_total": round(result["quote"]["total"], 2),
        "restock_required": result["restock"]["restock_required"],
    }

