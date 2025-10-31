"""Evaluator for the ordering agent."""

from __future__ import annotations

from typing import Dict, Optional

from agents import InventoryAgent, OrderingAgent
from data import database_service
from evaluator.common import assert_tool_called, ensure_seed, get_model
from utils.text import ParsedItem


def evaluate_ordering_agent(*, model: Optional[object] = None, offline: bool = False) -> Dict:
    """Ensure the ordering agent records restocks and updates cash balance."""

    ensure_seed()
    model_instance = get_model(model, require_api_key=not offline)
    ordering_agent = OrderingAgent(model_instance)
    inventory_agent = InventoryAgent(model_instance)

    as_of_date = "2025-04-01"
    summary = inventory_agent.summarize_inventory(as_of_date)
    first_item = summary["items"][0]
    deficit_quantity = int(first_item["stock"]) + 20
    restock_item = ParsedItem(
        name=first_item["item_name"],
        quantity=deficit_quantity,
        unit_price=float(first_item["unit_price"]),
    )

    if not offline:
        task = (
            f"Using place_restock_order_tool, schedule a restock of {deficit_quantity} units of"
            f" {restock_item.name} on {as_of_date}. Reply with a brief summary."
        )
        result = ordering_agent.run(task)
        assert_tool_called(ordering_agent, result, "place_restock_order_tool")

    cash_before = database_service.get_cash_balance(as_of_date)
    outcome = ordering_agent.restock([restock_item], as_of_date)
    cash_after = database_service.get_cash_balance(as_of_date)

    if not outcome.get("success"):
        raise AssertionError("Ordering agent did not report success")
    if not outcome.get("orders"):
        raise AssertionError("Ordering agent produced no restock orders")

    expected_cash = round(cash_before - outcome.get("total_cost", 0.0), 2)
    actual_cash = round(cash_after, 2)
    if expected_cash != actual_cash:
        raise AssertionError(
            f"Cash balance mismatch after restock: expected {expected_cash}, observed {actual_cash}"
        )

    return {
        "orders_created": len(outcome["orders"]),
        "total_cost": round(outcome.get("total_cost", 0.0), 2),
    }

