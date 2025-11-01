"""Inventory-focused agent for the project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from smolagents import ToolCallingAgent, tool

from data import database_service, get_all_inventory, get_stock_level
from utils.text import ParsedItem, category_peers, get_supply_entry


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


def _suggest_alternative_items(
    order_items: List[ParsedItem],
    restock_entries: List[Dict],
    as_of_date: str,
    *,
    max_per_item: int = 3,
) -> List[Dict]:
    if not restock_entries:
        return []

    stock_snapshot = get_all_inventory(as_of_date)
    item_lookup = {item.name: item for item in order_items}
    suggestions: List[Dict] = []

    for entry in restock_entries:
        item_name = entry.get("item_name")
        if not item_name:
            continue

        source_item = item_lookup.get(item_name)
        metadata = get_supply_entry(item_name)
        if source_item is None or metadata is None:
            continue

        requested_qty = int(entry.get("requested", source_item.quantity))
        peers = category_peers(item_name)
        candidates: List[Dict] = []

        for peer in peers:
            peer_name = peer.get("item_name")
            if not peer_name:
                continue
            available = int(stock_snapshot.get(peer_name, 0))
            if available <= 0:
                continue
            unit_price = float(peer.get("unit_price", source_item.unit_price))
            price_delta = round(unit_price - source_item.unit_price, 4)
            candidates.append(
                {
                    "item_name": peer_name,
                    "available_stock": available,
                    "unit_price": unit_price,
                    "covers_full_quantity": available >= requested_qty,
                    "price_delta": price_delta,
                    "reason": f"Same category ({peer.get('category', 'unknown')}) with available stock",
                }
            )

        if not candidates:
            continue

        candidates.sort(
            key=lambda candidate: (
                not candidate["covers_full_quantity"],
                candidate["price_delta"],
                -candidate["available_stock"],
            )
        )

        suggestions.append(
            {
                "item_name": item_name,
                "requested": requested_qty,
                "current_stock": int(entry.get("current_stock", 0)),
                "deficit": int(entry.get("deficit", max(requested_qty - int(entry.get("current_stock", 0)), 0))),
                "alternatives": candidates[:max_per_item],
            }
        )

    return suggestions


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


@tool
def suggest_substitute_items_tool(items: List[Dict], restock_items: List[Dict], as_of_date: str) -> Dict:
    """Recommend catalogue substitutions for items that triggered restock.

    Args:
        items: List of requested items with ``name``, ``quantity``, and ``unit_price`` keys.
        restock_items: Entries produced by ``evaluate_restock_needs_tool`` describing shortages.
        as_of_date: ISO formatted date string used to look up current stock snapshots.

    Returns:
        Dictionary containing ``success`` and a ``suggestions`` payload with alternative options.
    """

    parsed_items = [ParsedItem(name=item["name"], quantity=item["quantity"], unit_price=item["unit_price"]) for item in items]
    suggestions = _suggest_alternative_items(parsed_items, restock_items, as_of_date)
    return {"success": bool(suggestions), "suggestions": suggestions}


class InventoryAgent(ToolCallingAgent):
    """Agent responsible for presenting inventory signals."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[get_inventory_overview_tool, evaluate_restock_needs_tool, suggest_substitute_items_tool],
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

    def suggest_alternatives(self, items: List[ParsedItem], restock_plan: Dict, as_of_date: str) -> Dict:
        restock_items = restock_plan.get("items", []) if restock_plan else []
        suggestions = _suggest_alternative_items(items, restock_items, as_of_date)
        return {"success": bool(suggestions), "suggestions": suggestions}

