"""Evaluator for the combined customer insights agent."""

from __future__ import annotations

from typing import Dict, Optional

from agents import CustomerInsightsAgent
from evaluator.common import assert_tool_called, ensure_seed, get_model


def _build_item(name: str, quantity: int, unit_price: float) -> Dict:
    return {"name": name, "quantity": quantity, "unit_price": unit_price}


def _build_restock_item(name: str, deficit: int, current_stock: int) -> Dict:
    return {"item_name": name, "deficit": deficit, "current_stock": current_stock}


def evaluate_customer_insights_agent(
    *, model: Optional[object] = None, offline: bool = False
) -> Dict:
    """Check negotiation outcomes and advisory suggestions."""

    ensure_seed()
    insights_agent = CustomerInsightsAgent(get_model(model, require_api_key=not offline))

    if not offline:
        negotiation_prompt = (
            "Review the following quote for a large business owner event and call"
            " review_quote_tool to determine whether to accept: persona=business owner,"
            " need_size=large, event=expo, total=$640, restock required on Glossy paper."
        )
        negotiation_result = insights_agent.run(negotiation_prompt)
        assert_tool_called(insights_agent, negotiation_result, "review_quote_tool")

        financial_prompt = (
            "Provide financial guidance for 2025-04-01 by calling"
            " get_financial_report_tool and then generate_business_recommendations_tool using"
            " the provided report and two sample scenarios. Summarise briefly."
        )
        guidance_result = insights_agent.run(financial_prompt)
        assert_tool_called(insights_agent, guidance_result, "get_financial_report_tool")
        assert_tool_called(insights_agent, guidance_result, "generate_business_recommendations_tool")

    accepted_feedback = insights_agent.negotiate(
        persona="office manager",
        need_size="small",
        event="ceremony",
        items=[_build_item("Glossy paper", 100, 0.2)],
        restock_items=[],
        quote_total=20.0,
        fulfilled=True,
    )
    if not accepted_feedback.accepted:
        raise AssertionError("Expected quote to be accepted without adjustments")

    counter_feedback = insights_agent.negotiate(
        persona="business owner",
        need_size="large",
        event="expo",
        items=[_build_item("Glossy paper", 800, 0.2)],
        restock_items=[_build_restock_item("Glossy paper", 500, 0)],
        quote_total=640.0,
        fulfilled=False,
    )
    if counter_feedback.accepted:
        raise AssertionError("Expected negotiation to propose a counter offer")
    if not counter_feedback.revised_request:
        raise AssertionError("Counter negotiation should return a revised request")

    request_summaries = [
        {
            "quote_total": 120.0,
            "cash_delta": 40.0,
            "fulfilled": True,
            "restock_required": False,
            "restock_items": [],
        },
        {
            "quote_total": 540.0,
            "cash_delta": -120.0,
            "fulfilled": False,
            "restock_required": True,
            "restock_items": [_build_restock_item("Matte paper", 300, 0)],
        },
    ]
    final_financials = insights_agent.financial_report("2025-04-15")
    advisor_output = insights_agent.advise(request_summaries, final_financials)
    suggestions = advisor_output.get("suggestions", [])
    metrics = advisor_output.get("metrics", {})
    if not suggestions:
        raise AssertionError("Advisor should return at least one suggestion")
    if "fulfilled_percent" not in metrics:
        raise AssertionError("Advisor metrics missing fulfilled percent")

    return {
        "suggestion_count": len(suggestions),
        "fulfilled_percent": metrics["fulfilled_percent"],
    }

