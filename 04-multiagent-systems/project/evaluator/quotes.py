"""Evaluator for the quoting agent."""

from __future__ import annotations

from typing import Dict, Optional

from agents import QuotingAgent
from data import database_service
from evaluator.common import assert_tool_called, ensure_seed, get_model
from utils.text import ParsedItem


def evaluate_quoting_agent(*, model: Optional[object] = None, offline: bool = False) -> Dict:
    """Validate price calculation and discounting behaviour."""

    ensure_seed()
    quoting_agent = QuotingAgent(get_model(model, require_api_key=not offline))

    if not offline:
        task = (
            "Use prepare_quote_tool to create a quote for 600 units of Glossy paper"
            " priced at $0.20 with context terms ['glossy', 'bulk'] and reply briefly."
        )
        result = quoting_agent.run(task)
        assert_tool_called(quoting_agent, result, "prepare_quote_tool")

    reference = database_service.get_inventory_reference()
    if reference.empty:
        raise AssertionError("Inventory reference is empty")
    row = reference.iloc[0]

    quantity = 600
    unit_price = float(row["unit_price"])
    items = [ParsedItem(name=row["item_name"], quantity=quantity, unit_price=unit_price)]
    terms = [row["item_name"].split()[0].lower(), "bulk"]

    quote = quoting_agent.build_quote(items, terms)
    if not quote.get("success"):
        raise AssertionError("Quote generation failed")

    base_total = quantity * unit_price
    expected_total = round(base_total * 0.95, 2)
    actual_total = round(quote.get("total", 0.0), 2)
    if actual_total != expected_total:
        raise AssertionError(
            f"Expected discounted total {expected_total}, received {actual_total}"
        )

    return {
        "quote_total": actual_total,
        "itemised_count": len(quote.get("itemised", [])),
    }

