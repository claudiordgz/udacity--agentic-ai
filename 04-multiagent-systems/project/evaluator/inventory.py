"""Evaluator for the inventory agent."""

from __future__ import annotations

from typing import Dict, Optional

from agents import InventoryAgent
from evaluator.common import assert_tool_called, ensure_seed, get_model
from utils.text import ParsedItem


def evaluate_inventory_agent(*, model: Optional[object] = None, offline: bool = False) -> Dict:
    """Validate core behaviours for the `InventoryAgent`."""

    ensure_seed()
    inventory_agent = InventoryAgent(get_model(model, require_api_key=not offline))
    as_of_date = "2025-04-01"

    if not offline:
        task = (
            "You are the inventory specialist. Use get_inventory_overview_tool to provide"
            " the stock summary for 2025-04-01. Respond with a short acknowledgement."
        )
        result = inventory_agent.run(task)
        assert_tool_called(inventory_agent, result, "get_inventory_overview_tool")

    summary = inventory_agent.summarize_inventory(as_of_date)
    if not summary.get("success"):
        raise AssertionError("Inventory summary did not succeed")
    items = summary.get("items", [])
    if not items:
        raise AssertionError("Inventory summary returned no items")

    first_item = items[0]
    restock_test_item = ParsedItem(
        name=first_item["item_name"],
        quantity=int(first_item["stock"]) + 5,
        unit_price=float(first_item["unit_price"]),
    )
    restock_plan = inventory_agent.restock_plan([restock_test_item], as_of_date)
    if not restock_plan.get("restock_required"):
        raise AssertionError("Restock plan should have detected a deficit")

    suggestions = inventory_agent.suggest_alternatives([restock_test_item], restock_plan, as_of_date)
    if not suggestions.get("success"):
        raise AssertionError("Inventory agent did not surface substitution options for deficit items")
    if not suggestions.get("suggestions"):
        raise AssertionError("Substitution payload missing alternatives")

    return {
        "inventory_items": len(items),
        "restock_entries": len(restock_plan.get("items", [])),
        "alternative_suggestions": len(suggestions.get("suggestions", [])),
    }

