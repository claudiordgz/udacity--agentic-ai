from __future__ import annotations

import argparse
import os
from typing import Dict, List

import pandas as pd
from smolagents import OpenAIServerModel

from agents import (
    BusinessOrchestrator,
    CustomerInsightsAgent,
    OrchestratorConfig,
)
from data import database_service, generate_financial_report
from utils.terminal_animation import render_negotiation_animation, render_workflow_animation


def build_model(*, require_api_key: bool = False) -> OpenAIServerModel:
    api_key = os.getenv("UDACITY_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if require_api_key and not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY or UDACITY_OPENAI_API_KEY must be set when running the LLM demo. "
            "Use --offline to run without model access."
        )
    if not api_key:
        api_key = "test-key"
    return OpenAIServerModel(
        model_id="gpt-4o-mini",
        api_base="https://openai.vocareum.com/v1",
        api_key=api_key,
    )

def seed_database(seed: int = 137) -> None:
    database_service.initialize(seed=seed)

def load_quote_requests() -> pd.DataFrame:
    requests = pd.read_csv("quote_requests_sample.csv")
    requests["request_date"] = pd.to_datetime(requests["request_date"], format="%m/%d/%y", errors="coerce")
    requests.dropna(subset=["request_date"], inplace=True)
    requests = requests.sort_values("request_date")
    return requests


def run_test_scenarios(*, model: OpenAIServerModel | None = None, requests: pd.DataFrame | None = None) -> List[Dict]:
    """
    Execute the pre-defined quote request scenarios using the multi-agent system.
    """
    seed_database()
    if model is None:
        model = build_model()
    orchestrator = BusinessOrchestrator(model, OrchestratorConfig(enable_llm=False))
    insights_agent = CustomerInsightsAgent(model)
    if requests is None:
        requests = load_quote_requests()

    initial_date = requests["request_date"].min().strftime("%Y-%m-%d")
    baseline_report = generate_financial_report(initial_date)
    print(f"Starting cash: ${baseline_report['cash_balance']:.2f}")
    print(f"Starting inventory value: ${baseline_report['inventory_value']:.2f}")

    outcomes: List[Dict] = []
    advisor_summaries: List[Dict] = []
    previous_cash = baseline_report["cash_balance"]
    for idx, row in requests.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")
        print(f"\n=== Request {idx + 1} ({request_date}) ===")
        print(f"Context: {row['job']} planning a {row['event']}")

        render_workflow_animation(
            [
                "Collecting customer requirements",
                "Consulting inventory specialist",
                "Preparing pricing proposal",
                "Coordinating substitution packages",
                "Evaluating restock impact",
                "Compiling customer-facing response",
            ]
        )

        response = orchestrator.handle_request(row["request"], request_date)
        print(response["response_text"])

        customer_feedback = insights_agent.negotiate(
            persona=row["job"],
            need_size=row.get("need_size", "medium"),
            event=row["event"],
            items=response["items"],
            restock_items=response["restock"]["items"],
            quote_total=response["quote"]["total"],
            fulfilled=response["fulfilled"],
            alternative_quotes=response["quote"].get("alternatives", []),
        )

        negotiation_applied = False
        if customer_feedback.accepted:
            print("CustomerInsightsAgent perspective: Quote accepted without changes.")
        elif customer_feedback.revised_request:
            render_negotiation_animation("Customer agent proposing counter-offer")
            print(f"CustomerInsightsAgent perspective: {customer_feedback.message}")
            if customer_feedback.preferred_option:
                suggested_total = customer_feedback.suggested_total
                if suggested_total is not None:
                    print(
                        f"CustomerInsightsAgent preference: Adopt '{customer_feedback.preferred_option}' at ${suggested_total:.2f}."
                    )
                else:
                    print(
                        f"CustomerInsightsAgent preference: Adopt '{customer_feedback.preferred_option}'."
                    )
            response = orchestrator.handle_request(customer_feedback.revised_request, request_date)
            negotiation_applied = True
            print("-- Updated quote after negotiation --")
            print(response["response_text"])
        else:
            print(f"CustomerInsightsAgent perspective: {customer_feedback.message}")
            if customer_feedback.preferred_option:
                suggested_total = customer_feedback.suggested_total
                if suggested_total is not None:
                    print(
                        f"CustomerInsightsAgent note: Would prefer '{customer_feedback.preferred_option}' at ${suggested_total:.2f}."
                    )
                else:
                    print(
                        f"CustomerInsightsAgent note: Would prefer '{customer_feedback.preferred_option}'."
                    )

        updated_report = generate_financial_report(request_date)
        print(f"Updated cash: ${updated_report['cash_balance']:.2f}")
        print(f"Updated inventory: ${updated_report['inventory_value']:.2f}")

        cash_delta = updated_report["cash_balance"] - previous_cash
        previous_cash = updated_report["cash_balance"]

        advisor_summaries.append(
            {
                "request_id": idx + 1,
                "quote_total": response["quote"]["total"],
                "cash_delta": cash_delta,
                "fulfilled": response["fulfilled"],
                "restock_required": response["restock"]["restock_required"],
                "restock_items": response["restock"].get("items", []),
                "preferred_option": customer_feedback.preferred_option,
            }
        )

        outcomes.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "quote_total": response["quote"]["total"],
                "cash_balance": updated_report["cash_balance"],
                "cash_delta": cash_delta,
                "inventory_value": updated_report["inventory_value"],
                "fulfilled": response["fulfilled"],
                "restock_required": response["restock"]["restock_required"],
                "negotiated": negotiation_applied,
                "response_text": response["response_text"],
                "preferred_option": customer_feedback.preferred_option,
            }
        )

    final_date = requests["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    pd.DataFrame(outcomes).to_csv("test_results.csv", index=False)

    advisor_summary = insights_agent.advise(advisor_summaries, final_report)
    print("\n===== BUSINESS ADVISOR RECOMMENDATIONS =====")
    metrics = advisor_summary.get("metrics", {})
    if metrics:
        for key, value in metrics.items():
            print(f"- {key.replace('_', ' ').title()}: {value}")
    suggestions = advisor_summary.get("suggestions", [])
    if suggestions:
        print("\nTop suggestions:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")

    return outcomes


def _should_run_llm_demo(args) -> bool:
    if getattr(args, "offline", False):
        return False

    flag = os.getenv("RUN_LLM_DEMO")
    if flag is not None:
        return flag.lower() in {"1", "true", "yes", "on"}

    return True


def run_llm_demo(model: OpenAIServerModel, requests: pd.DataFrame, *, limit: int = 3) -> None:
    """Execute a small subset of requests through the LLM-driven orchestration."""

    print("\n===== LLM-DRIVEN DEMO (non-deterministic) =====")
    seed_database()
    orchestrator = BusinessOrchestrator(model, OrchestratorConfig(enable_llm=True))
    sample = requests.head(limit)

    for idx, (_, row) in enumerate(sample.iterrows(), start=1):
        request_date = row["request_date"].strftime("%Y-%m-%d")
        prompt = (
            "You are the Munder Difflin business orchestrator.\n"
            f"Request date: {request_date}.\n"
            f"Customer persona: {row['job']} planning a {row['event']}.\n"
            "Use the available tools to prepare a quote, plan restocks if needed, and summarise the outcome.\n"
            "Return a concise report with any tool call issues.\n"
            f"Customer request text:\n{row['request']}"
        )
        result = orchestrator.run(prompt)
        output = getattr(result, "parsed_output", None) or getattr(result, "raw_output", None) or result

        print(f"\n--- LLM result for Request {idx} ({request_date}) ---")
        print(output)

        tool_calls = getattr(result, "tool_calls", None)
        if tool_calls:
            print("Tool call log:")
            for call in tool_calls:
                print(call)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Munder Difflin multi-agent evaluation.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip the LLM demo and run only the deterministic workflow.",
    )
    parser.add_argument(
        "--demo-limit",
        type=int,
        default=3,
        help="Number of requests to include in the LLM demo when enabled.",
    )
    cli_args = parser.parse_args()

    requests_df = load_quote_requests()
    should_run_llm = _should_run_llm_demo(cli_args)
    model_instance = build_model(require_api_key=should_run_llm)
    results = run_test_scenarios(model=model_instance, requests=requests_df)
    if should_run_llm:
        run_llm_demo(model_instance, requests_df, limit=cli_args.demo_limit)