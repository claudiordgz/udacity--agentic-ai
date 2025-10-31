"""Agent responsible for restocking actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from smolagents import ToolCallingAgent, tool

from data import create_transaction, get_cash_balance, get_supplier_delivery_date
from utils.text import ParsedItem


@dataclass
class RestockOutcome:
    success: bool
    orders: List[Dict]
    total_cost: float
    cash_balance: float
    reason: str | None = None


def _schedule_restock(items: List[ParsedItem], as_of_date: str) -> RestockOutcome:
    restock_items = [item for item in items if item.quantity > 0]
    if not restock_items:
        return RestockOutcome(
            success=True,
            orders=[],
            total_cost=0.0,
            cash_balance=get_cash_balance(as_of_date),
        )

    total_cost = sum(item.quantity * item.unit_price for item in restock_items)
    available_cash = get_cash_balance(as_of_date)

    if total_cost > available_cash:
        return RestockOutcome(
            success=False,
            orders=[],
            total_cost=total_cost,
            cash_balance=available_cash,
            reason="Insufficient cash to cover restock cost.",
        )

    orders = []
    for item in restock_items:
        cost = item.quantity * item.unit_price
        create_transaction(
            item_name=item.name,
            transaction_type="stock_orders",
            quantity=item.quantity,
            price=cost,
            date=as_of_date,
        )
        orders.append(
            {
                "item_name": item.name,
                "quantity": item.quantity,
                "cost": cost,
                "estimated_delivery": get_supplier_delivery_date(as_of_date, item.quantity),
            }
        )

    return RestockOutcome(
        success=True,
        orders=orders,
        total_cost=total_cost,
        cash_balance=get_cash_balance(as_of_date),
    )


@tool
def place_restock_order_tool(items: List[Dict], as_of_date: str) -> Dict:
    """Place restock orders for the specified items.

    Args:
        items: List of dictionaries containing ``name``, ``quantity``, and ``unit_price``.
        as_of_date: ISO formatted date string marking when the order is placed.

    Returns:
        Dictionary describing success, order details, total cost, cash balance, and failure reason if any.
    """

    parsed = [ParsedItem(**item) for item in items]
    outcome = _schedule_restock(parsed, as_of_date)
    payload = {
        "success": outcome.success,
        "orders": outcome.orders,
        "total_cost": outcome.total_cost,
        "cash_balance": outcome.cash_balance,
    }
    if outcome.reason:
        payload["reason"] = outcome.reason
    return payload


class OrderingAgent(ToolCallingAgent):
    """Agent that executes purchase orders."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[place_restock_order_tool],
            model=model,
            name="ordering_agent",
            description="Execute restock transactions and update cash balance.",
        )

    def restock(self, items: List[ParsedItem], as_of_date: str) -> Dict:
        outcome = _schedule_restock(items, as_of_date)
        payload = {
            "success": outcome.success,
            "orders": outcome.orders,
            "total_cost": outcome.total_cost,
            "cash_balance": outcome.cash_balance,
        }
        if outcome.reason:
            payload["reason"] = outcome.reason
        return payload

