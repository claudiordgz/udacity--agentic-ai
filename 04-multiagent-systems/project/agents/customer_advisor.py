"""Agent that represents the customer and provides business recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, Iterable, List, Set

from smolagents import ToolCallingAgent, tool

from utils.text import ParsedItem, build_request_text
from data import generate_financial_report


BUDGET_BY_NEED = {
    "small": 150.0,
    "medium": 300.0,
    "large": 600.0,
}


@dataclass
class NegotiationOutcome:
    accepted: bool
    message: str
    revised_request: str | None = None
    adjustment_factor: float | None = None


def _convert_items(items: Iterable[Dict]) -> List[ParsedItem]:
    converted: List[ParsedItem] = []
    for entry in items:
        converted.append(
            ParsedItem(
                name=entry["name"],
                quantity=int(entry["quantity"]),
                unit_price=float(entry.get("unit_price", 0.0)),
            )
        )
    return converted


def _scale_items(items: List[ParsedItem], targeted: Set[str], *, factor: float) -> List[ParsedItem]:
    adjusted: List[ParsedItem] = []
    for item in items:
        if item.name in targeted or not targeted:
            new_quantity = max(1, int(item.quantity * factor))
        else:
            new_quantity = item.quantity
        adjusted.append(
            ParsedItem(name=item.name, quantity=new_quantity, unit_price=item.unit_price)
        )
    return adjusted


def _choose_factor(over_budget: bool, restock_pressure: bool) -> float:
    if restock_pressure and over_budget:
        return 0.7
    if restock_pressure:
        return 0.75
    if over_budget:
        return 0.85
    return 0.9


@tool
def get_financial_report_tool(as_of_date: str) -> Dict:
    """Return the financial report for the specified date.

    Args:
        as_of_date: ISO formatted date string (YYYY-MM-DD) used to scope the report.

    Returns:
        Dictionary containing a success flag and the financial report payload.
    """

    report = generate_financial_report(as_of_date)
    return {"success": True, "report": report}


@tool
def review_quote_tool(
    persona: str,
    need_size: str,
    event: str,
    items: List[Dict],
    restock_items: List[Dict],
    quote_total: float,
    fulfilled: bool,
) -> Dict:
    """Evaluate an internal quote and decide whether to accept or counter-offer.

    Args:
        persona: Role or persona of the customer submitting the request.
        need_size: Size marker from the dataset (e.g., small, medium, large).
        event: Description of the event that requires supplies.
        items: Structured representation of requested items.
        restock_items: Items that triggered restock activity in the workflow.
        quote_total: Total quoted price from the internal agents.
        fulfilled: Whether the request can be fulfilled without adjustments.

    Returns:
        Dictionary describing the negotiation outcome, including whether the
        quote is accepted and a revised request if a counter-offer is proposed.
    """

    parsed_items = _convert_items(items)
    restock_targets = {entry["item_name"] for entry in restock_items if entry.get("item_name")}
    budget = BUDGET_BY_NEED.get(need_size.lower(), 300.0)

    over_budget = quote_total > budget
    restock_pressure = bool(restock_targets)

    if fulfilled and not over_budget and not restock_pressure:
        return {
            "accepted": True,
            "message": "Quote accepted as proposed.",
            "revised_request": None,
            "adjustment_factor": None,
        }

    factor = _choose_factor(over_budget, restock_pressure)
    adjusted = _scale_items(parsed_items, restock_targets, factor=factor)
    revised_request = build_request_text(adjusted, persona=persona, event=event)
    message_parts = []
    if over_budget:
        message_parts.append("Requested a reduced order to keep the quote within budget.")
    if restock_pressure or not fulfilled:
        message_parts.append("Adjusted pressure items to avoid supplier delays.")
    if not message_parts:
        message_parts.append("Suggested smaller quantities to secure faster fulfilment.")

    return {
        "accepted": False,
        "message": " ".join(message_parts),
        "revised_request": revised_request,
        "adjustment_factor": factor,
    }


def _percentage(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round(part / whole * 100, 2)


@tool
def generate_business_recommendations_tool(
    request_summaries: List[Dict],
    final_financials: Dict,
) -> Dict:
    """Analyse operations and return recommendations for the business team.

    Args:
        request_summaries: List of per-request dictionaries containing quote totals,
            fulfilment status, restock details, and cash deltas.
        final_financials: Financial snapshot captured after all scenarios are processed.

    Returns:
        Dictionary with aggregated metrics and prioritised business suggestions.
    """

    total_requests = len(request_summaries)
    fulfilled = sum(1 for entry in request_summaries if entry.get("fulfilled"))
    restock_events = [entry for entry in request_summaries if entry.get("restock_required")]
    restock_count = len(restock_events)
    unfulfilled = total_requests - fulfilled
    cash_deltas = [entry.get("cash_delta", 0.0) for entry in request_summaries]
    positive_cash = sum(1 for delta in cash_deltas if delta > 0)
    avg_quote = mean([entry.get("quote_total", 0.0) for entry in request_summaries]) if request_summaries else 0.0

    suggestions: List[str] = []

    if restock_count:
        top_restock_items: Dict[str, int] = {}
        for entry in restock_events:
            for item in entry.get("restock_items", []):
                name = item.get("item_name")
                if not name:
                    continue
                top_restock_items[name] = top_restock_items.get(name, 0) + int(item.get("deficit", 0))
        if top_restock_items:
            sorted_items = sorted(top_restock_items.items(), key=lambda pair: pair[1], reverse=True)
            top_names = ", ".join(name for name, _ in sorted_items[:3])
            suggestions.append(f"Increase safety stock for high-demand items: {top_names}.")
    if unfulfilled:
        suggestions.append("Investigate unfulfilled requests to expand supplier coverage or offer alternatives.")
    if positive_cash < total_requests:
        suggestions.append("Consider promotional bundles to convert more requests into revenue-positive outcomes.")
    if avg_quote > 400:
        suggestions.append("Introduce tiered pricing or loyalty discounts for large orders to stay competitive.")
    suggestions.append("Review cash reserves and reinvest part of the current balance into fast-moving inventory.")

    metrics = {
        "total_requests": total_requests,
        "fulfilled_percent": _percentage(fulfilled, total_requests),
        "restock_percent": _percentage(restock_count, total_requests),
        "positive_cash_percent": _percentage(positive_cash, total_requests),
        "final_cash": round(final_financials.get("cash_balance", 0.0), 2),
        "final_inventory_value": round(final_financials.get("inventory_value", 0.0), 2),
    }

    return {"success": True, "metrics": metrics, "suggestions": suggestions}


class CustomerInsightsAgent(ToolCallingAgent):
    """Agent that negotiates on behalf of the customer and advises the business."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[get_financial_report_tool, review_quote_tool, generate_business_recommendations_tool],
            model=model,
            name="customer_insights_agent",
            description="Negotiate customer quotes and generate strategic business insights.",
        )

    def financial_report(self, as_of_date: str) -> Dict:
        return generate_financial_report(as_of_date)

    def negotiate(
        self,
        persona: str,
        need_size: str,
        event: str,
        items: List[Dict],
        restock_items: List[Dict],
        quote_total: float,
        fulfilled: bool,
    ) -> NegotiationOutcome:
        result = review_quote_tool(
            persona=persona,
            need_size=need_size,
            event=event,
            items=items,
            restock_items=restock_items,
            quote_total=quote_total,
            fulfilled=fulfilled,
        )
        return NegotiationOutcome(
            accepted=bool(result["accepted"]),
            message=str(result["message"]),
            revised_request=result.get("revised_request"),
            adjustment_factor=result.get("adjustment_factor"),
        )

    def advise(self, request_summaries: List[Dict], final_financials: Dict) -> Dict:
        return generate_business_recommendations_tool(
            request_summaries=request_summaries,
            final_financials=final_financials,
        )

