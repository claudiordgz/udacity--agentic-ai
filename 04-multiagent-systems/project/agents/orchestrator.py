"""Business orchestrator coordinating specialised agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from smolagents import ToolCallingAgent, tool

from agents.inventory import InventoryAgent
from agents.ordering import OrderingAgent
from agents.quotes import QuotingAgent
from agents.customer_advisor import CustomerInsightsAgent
from utils import ParsedItem, parse_request_items


@dataclass
class OrchestratorConfig:
    enable_llm: bool = False


class BusinessOrchestrator(ToolCallingAgent):
    """Coordinates domain agents to service quote requests."""

    def __init__(self, model, config: OrchestratorConfig | None = None) -> None:
        self.config = config or OrchestratorConfig()
        self.inventory_agent = InventoryAgent(model)
        self.quoting_agent = QuotingAgent(model)
        self.ordering_agent = OrderingAgent(model)
        self.customer_agent = CustomerInsightsAgent(model)

        @tool
        def process_customer_request_tool(request_text: str, request_date: str) -> Dict:
            """Process an incoming customer request.

            Args:
                request_text: Free-form description of the customer's needs.
                request_date: ISO formatted request date (YYYY-MM-DD).

            Returns:
                Dict containing success flag and the orchestrated response payload.
            """

            result = self.handle_request(request_text, request_date)
            return {"success": True, "result": result}

        super().__init__(
            tools=[process_customer_request_tool],
            model=model,
            name="business_orchestrator",
            description="Handle customer quote requests by coordinating inventory, pricing, ordering, and finance agents.",
        )

    def handle_request(self, request_text: str, request_date: str) -> Dict:
        parsed_items = parse_request_items(request_text)
        if not parsed_items:
            inventory_overview = self.inventory_agent.summarize_inventory(request_date)
            report = self.customer_agent.financial_report(request_date)
            response_text = (
                "Could not parse item list from request. No quote generated; escalate to a sales representative."
            )
            return {
                "items": [],
                "quote": {
                    "success": False,
                    "total": 0.0,
                    "explanation": "Unable to parse items from customer request.",
                    "itemised": [],
                },
                "restock": {"restock_required": False, "items": []},
                "orders": {
                    "success": False,
                    "orders": [],
                    "total_cost": 0.0,
                    "cash_balance": report["cash_balance"],
                    "reason": "Unable to parse items from customer request.",
                },
                "financial_report": report,
                "inventory_overview": inventory_overview,
                "fulfilled": False,
                "response_text": response_text,
                "note": "Could not parse item list from request.",
            }

        items_payload = [
            {"name": item.name, "quantity": item.quantity, "unit_price": item.unit_price}
            for item in parsed_items
        ]

        inventory_overview = self.inventory_agent.summarize_inventory(request_date)
        restock_plan = self.inventory_agent.restock_plan(parsed_items, request_date)
        alternative_candidates = self.inventory_agent.suggest_alternatives(parsed_items, restock_plan, request_date)
        alternative_suggestions = alternative_candidates.get("suggestions", [])
        quote = self.quoting_agent.build_quote(
            parsed_items,
            _context_terms_from_request(request_text),
            alternative_suggestions=alternative_suggestions,
        )

        orders = {
            "success": True,
            "orders": [],
            "total_cost": 0.0,
            "cash_balance": inventory_overview.get("cash_balance") if isinstance(inventory_overview, dict) else None,
        }
        if restock_plan["restock_required"]:
            price_lookup = {item.name: item.unit_price for item in parsed_items}
            deficit_items = [
                ParsedItem(
                    name=entry["item_name"],
                    quantity=entry["deficit"],
                    unit_price=price_lookup.get(entry["item_name"], entry["estimated_cost"] / entry["deficit"]),
                )
                for entry in restock_plan["items"]
            ]
            orders = self.ordering_agent.restock(deficit_items, request_date)

        report = self.customer_agent.financial_report(request_date)

        fulfilled = not restock_plan["restock_required"] or orders.get("success", False)

        alternative_quotes = quote.get("alternatives", [])
        response_text = _summarise_response(
            parsed_items,
            quote,
            restock_plan,
            orders,
            report,
            fulfilled,
            alternative_quotes=alternative_quotes,
        )
        return {
            "items": items_payload,
            "quote": quote,
            "restock": restock_plan,
            "orders": orders,
            "financial_report": report,
            "inventory_overview": inventory_overview,
            "fulfilled": fulfilled,
            "response_text": response_text,
            "inventory_alternatives": alternative_suggestions,
        }


def _context_terms_from_request(request_text: str) -> List[str]:
    terms = []
    for token in request_text.replace("\n", " ").split():
        cleaned = token.strip(".,-:").lower()
        if cleaned:
            terms.append(cleaned)
    return terms[:15]


def _summarise_response(
    items: List[ParsedItem],
    quote: Dict,
    restock_plan: Dict,
    orders: Dict | None,
    report: Dict,
    fulfilled: bool,
    alternative_quotes: List[Dict] | None = None,
) -> str:
    lines = [
        "Quote prepared for requested items:",
    ]
    for item in items:
        lines.append(f"- {item.quantity} units of {item.name} @ ${item.unit_price:.2f}")
    lines.append(f"Proposed total: ${quote['total']:.2f} (discount applied: {quote['explanation']})")

    if restock_plan["restock_required"]:
        lines.append("Restock required for the following items:")
        for entry in restock_plan["items"]:
            lines.append(
                f"  * {entry['item_name']}: deficit {entry['deficit']} units (current stock {entry['current_stock']})"
            )
        if orders and orders.get("success"):
            lines.append(f"Restock orders placed, total cost ${orders['total_cost']:.2f}.")
        else:
            reason = orders.get("reason", "Unable to execute restock.") if orders else "Unable to execute restock."
            lines.append(f"Restock could not be completed: {reason}")
    else:
        lines.append("Existing inventory covers the request; no restock needed.")

    alternative_options = alternative_quotes or quote.get("alternatives", [])
    if alternative_options:
        lines.append("Alternative packages to avoid restock delays:")
        for option in alternative_options:
            savings = option.get("savings_vs_primary")
            savings_clause = f" (saves ${savings:.2f})" if isinstance(savings, (int, float)) and savings else ""
            lines.append(
                f"  * {option.get('label', 'Alternative')}: ${option.get('total', 0.0):.2f}{savings_clause}"
            )

    lines.append(
        f"Post-order cash balance: ${report['cash_balance']:.2f} | Inventory value: ${report['inventory_value']:.2f}"
    )
    if not fulfilled:
        lines.append("Outcome: Request cannot be fulfilled with current inventory and cash reserves.")
    return "\n".join(lines)

