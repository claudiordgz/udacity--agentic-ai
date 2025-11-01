"""Quote generation agent."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, Iterable, List, Set

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


def _generate_alternative_quotes(
    items: List[ParsedItem],
    suggestions: List[Dict],
    context_terms: Iterable[str],
) -> List[Dict]:
    alternatives: List[Dict] = []
    seen_labels: Set[str] = set()

    for suggestion in suggestions or []:
        base_item = suggestion.get("item_name")
        requested_qty = int(suggestion.get("requested", 0)) if suggestion.get("requested") is not None else 0
        if not base_item or requested_qty <= 0:
            continue

        for candidate in suggestion.get("alternatives", []):
            replacement = candidate.get("item_name")
            if not replacement:
                continue
            if not candidate.get("covers_full_quantity", False):
                continue

            label = f"{base_item} → {replacement}"
            if label in seen_labels:
                continue
            seen_labels.add(label)

            replacement_items: List[ParsedItem] = []
            for entry in items:
                if entry.name == base_item:
                    replacement_items.append(
                        ParsedItem(
                            name=replacement,
                            quantity=requested_qty,
                            unit_price=float(candidate.get("unit_price", entry.unit_price)),
                        )
                    )
                else:
                    replacement_items.append(
                        ParsedItem(name=entry.name, quantity=entry.quantity, unit_price=entry.unit_price)
                    )

            quote = _generate_quote(replacement_items, context_terms)
            items_payload = [
                {"name": entry.name, "quantity": entry.quantity, "unit_price": entry.unit_price}
                for entry in replacement_items
            ]

            alternatives.append(
                {
                    "label": label,
                    "replaced_item": base_item,
                    "replacement": replacement,
                    "restock_avoided": True,
                    "total": quote.total,
                    "explanation": quote.explanation,
                    "itemised": quote.itemised,
                    "items": items_payload,
                    "reason": candidate.get("reason"),
                    "price_delta": candidate.get("price_delta"),
                }
            )

    return alternatives


@tool
def prepare_quote_tool(
    items: List[Dict],
    context_terms: List[str],
    alternative_suggestions: List[Dict] | None = None,
) -> Dict:
    """Prepare a quote for requested items.

    Args:
        items: List of dictionaries containing ``name``, ``quantity``, and ``unit_price``.
        context_terms: Tokenised context extracted from the customer request.
        alternative_suggestions: Optional substitution suggestions supplied by the inventory agent.

    Returns:
        Dictionary with ``success`` flag, total price, narrative explanation, itemised lines,
        and alternative quote options when substitutions are available.
    """

    parsed = [ParsedItem(**item) for item in items]
    quote = _generate_quote(parsed, context_terms)
    payload = {
        "success": True,
        "total": quote.total,
        "explanation": quote.explanation,
        "itemised": quote.itemised,
    }

    alternatives = _generate_alternative_quotes(parsed, alternative_suggestions or [], context_terms)
    if alternatives:
        for option in alternatives:
            option["savings_vs_primary"] = round(payload["total"] - option["total"], 2)
        payload["alternatives"] = alternatives

    return payload


class QuotingAgent(ToolCallingAgent):
    """Agent that prepares customer quotes."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[prepare_quote_tool],
            model=model,
            name="quoting_agent",
            description="Generate quotes using historical data and pricing heuristics.",
        )

    def build_quote(
        self,
        items: List[ParsedItem],
        terms: Iterable[str],
        alternative_suggestions: List[Dict] | None = None,
    ) -> Dict:
        quote = _generate_quote(items, terms)
        payload = {
            "success": True,
            "total": quote.total,
            "explanation": quote.explanation,
            "itemised": quote.itemised,
        }

        alternatives = _generate_alternative_quotes(items, alternative_suggestions or [], terms)
        if alternatives:
            for option in alternatives:
                option["savings_vs_primary"] = round(payload["total"] - option["total"], 2)
            payload["alternatives"] = alternatives

        return payload

