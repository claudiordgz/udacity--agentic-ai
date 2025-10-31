"""Inventory-focused agent for the project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from smolagents import ToolCallingAgent, tool

from data import database_service, get_all_inventory, get_stock_level
from utils.text import ParsedItem


@dataclass
class InventoryOverview:
    items: List[Dict]


@dataclass
class RestockPlan:
    restock_required: bool
    items: List[Dict]


def _get_inventory_summary(as_of_date: str) -> InventoryOverview:
    reference = database_service.get_inventory_reference()
    snapshot = get_all_inventory(as_of_date)
    items = []
    for _, row in reference.iterrows():
        items.append(
            {
                "item_name": row["item_name"],
                "stock": snapshot.get(row["item_name"], 0),
                "unit_price": row["unit_price"],
                "min_stock_level": row["min_stock_level"],
            }
        )
    return InventoryOverview(items=items)


def _evaluate_restock_needs(order_items: List[ParsedItem], as_of_date: str) -> RestockPlan:
    restock_plan = []
    for item in order_items:
        current_stock = get_stock_level(item.name, as_of_date)
        if current_stock >= item.quantity:
            continue
        deficit = item.quantity - current_stock
        restock_plan.append(
            {
                "item_name": item.name,
                "current_stock": current_stock,
                "requested": item.quantity,
                "deficit": deficit,
                "estimated_cost": deficit * item.unit_price,
            }
        )
    return RestockPlan(restock_required=bool(restock_plan), items=restock_plan)


@tool
def get_inventory_overview_tool(as_of_date: str) -> Dict:
    """Return stock levels and thresholds for the supplied date.

    Args:
        as_of_date: ISO formatted date string (YYYY-MM-DD).

    Returns:
        Dictionary with ``success`` flag and a list of inventory entries.
    """

    overview = _get_inventory_summary(as_of_date)
    return {"success": True, "items": overview.items}


@tool
def evaluate_restock_needs_tool(items: List[Dict], as_of_date: str) -> Dict:
    """Determine which requested items require restocking.

    Args:
        items: List of dictionaries with keys ``name``, ``quantity``, ``unit_price``.
        as_of_date: ISO formatted date string indicating evaluation cutoff.

    Returns:
        Dictionary containing ``success``, ``restock_required``, and plan details.
    """

    parsed_items = [ParsedItem(name=item["name"], quantity=item["quantity"], unit_price=item["unit_price"]) for item in items]
    plan = _evaluate_restock_needs(parsed_items, as_of_date)
    return {"success": True, "restock_required": plan.restock_required, "items": plan.items}


class InventoryAgent(ToolCallingAgent):
    """Agent responsible for presenting inventory signals."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[get_inventory_overview_tool, evaluate_restock_needs_tool],
            model=model,
            name="inventory_agent",
            description="Provide inventory availability and restock recommendations.",
        )

    def summarize_inventory(self, as_of_date: str) -> Dict:
        overview = _get_inventory_summary(as_of_date)
        return {"success": True, "items": overview.items}

    def restock_plan(self, items: List[ParsedItem], as_of_date: str) -> Dict:
        plan = _evaluate_restock_needs(items, as_of_date)
        return {"success": True, "restock_required": plan.restock_required, "items": plan.items}

