"""Quote generation agent."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, Iterable, List

from smolagents import ToolCallingAgent, tool

from data import search_quote_history
from utils.text import ParsedItem


@dataclass
class QuoteBreakdown:
    total: float
    explanation: str
    itemised: List[Dict]


def _historical_average(terms: Iterable[str]) -> float:
    records = search_quote_history(terms, limit=5)
    if not records:
        return 0.0
    return mean(record["total_amount"] for record in records)


def _price_items(items: List[ParsedItem]) -> Dict:
    base_total = sum(item.quantity * item.unit_price for item in items)
    quantity = sum(item.quantity for item in items)
    if quantity >= 5000:
        discount = 0.12
    elif quantity >= 1000:
        discount = 0.08
    elif quantity >= 500:
        discount = 0.05
    else:
        discount = 0.0

    discounted_total = base_total * (1 - discount)
    return {
        "base_total": base_total,
        "discount": discount,
        "final_total": discounted_total,
    }


def _generate_quote(items: List[ParsedItem], context_terms: Iterable[str]) -> QuoteBreakdown:
    price_info = _price_items(items)
    historical_average = _historical_average(context_terms)
    explanation_parts = [
        f"Base cost computed from unit pricing: ${price_info['base_total']:.2f}",
        f"Bulk discount applied: {price_info['discount'] * 100:.0f}%",
    ]
    if historical_average:
        explanation_parts.append(
            f"Historical reference for similar jobs: ${historical_average:.2f}"
        )

    itemised = [
        {
            "item_name": item.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "line_total": item.quantity * item.unit_price,
        }
        for item in items
    ]

    suggested_total = price_info["final_total"]
    return QuoteBreakdown(
        total=suggested_total,
        explanation="; ".join(explanation_parts),
        itemised=itemised,
    )


@tool
def prepare_quote_tool(items: List[Dict], context_terms: List[str]) -> Dict:
    """Prepare a quote for requested items.

    Args:
        items: List of dictionaries containing ``name``, ``quantity``, and ``unit_price``.
        context_terms: Tokenised context extracted from the customer request.

    Returns:
        Dictionary with ``success`` flag, total price, narrative explanation, and itemised lines.
    """

    parsed = [ParsedItem(**item) for item in items]
    quote = _generate_quote(parsed, context_terms)
    return {
        "success": True,
        "total": quote.total,
        "explanation": quote.explanation,
        "itemised": quote.itemised,
    }


class QuotingAgent(ToolCallingAgent):
    """Agent that prepares customer quotes."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[prepare_quote_tool],
            model=model,
            name="quoting_agent",
            description="Generate quotes using historical data and pricing heuristics.",
        )

    def build_quote(self, items: List[ParsedItem], terms: Iterable[str]) -> Dict:
        quote = _generate_quote(items, terms)
        return {
            "success": True,
            "total": quote.total,
            "explanation": quote.explanation,
            "itemised": quote.itemised,
        }

