"""LLM-powered demonstration scenarios for the fraud detection exercise."""

from __future__ import annotations

from typing import Dict, List

from config import model
from agents.complaint_resolution import ComplaintResolutionOrchestrator
from agents.customer_service import CustomerServiceAgent
from agents.fraud_detection.fraud_detection_agent import FraudDetectionAgent
from core import PrivacyLevel, database_service, reset_database
from data.fraud_data import get_transactions, seed_demo_records
from utils.state_cache import outcome_cache


def _extract_tool_logs(response) -> List[Dict]:
    logs: List[Dict] = []
    tool_calls = getattr(response, "tool_calls", None)
    if not tool_calls:
        return logs
    for call in tool_calls:
        logs.append(
            {
                "name": getattr(call, "name", None),
                "arguments": getattr(call, "arguments", None),
                "output": getattr(call, "output", getattr(call, "result", None)),
            }
        )
    return logs


def demo_fraud_assessment(transaction_id: str) -> Dict:
    """Demonstrate LLM-driven fraud assessment for a single transaction."""

    agent = FraudDetectionAgent(model)
    prompt = (
        "You are a fraud investigator. Analyse transaction {tid} for fraud risk.\n"
        "Call the check_transaction_for_fraud tool with transaction_id='{tid}' and report the results."
    ).format(tid=transaction_id)

    response = agent.run(prompt, max_steps=3)
    logs = _extract_tool_logs(response)

    deterministic = outcome_cache.get_or_set(
        ("fraud_assessment", transaction_id),
        lambda: agent.evaluate_transaction(transaction_id),
    )

    fallback_used = not any(
        log.get("name") == "check_transaction_for_fraud" and isinstance(log.get("output"), dict)
        and log["output"].get("success", True)
        for log in logs
    )

    fallback_reason = None
    if fallback_used:
        fallback_reason = "LLM did not produce a successful check_transaction_for_fraud tool call"

    return {
        "transaction_id": transaction_id,
        "deterministic": deterministic,
        "llm_calls": logs,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "llm_response": response,
    }


def demo_customer_claim_history(patient_id: int) -> Dict:
    """Demonstrate retrieving claim history through the customer service agent."""

    agent = CustomerServiceAgent(model)
    prompt = (
        "Retrieve the claim history for patient {pid}.\n"
        "Use the retrieve_claim_history tool and present a concise summary."
    ).format(pid=patient_id)

    response = agent.run(prompt, max_steps=3)
    logs = _extract_tool_logs(response)

    fallback_used = not any(
        log.get("name") == "retrieve_claim_history" and isinstance(log.get("output"), dict)
        and log["output"].get("success", True)
        for log in logs
    )

    fallback_reason = None
    if fallback_used:
        fallback_reason = "LLM did not produce a successful retrieve_claim_history tool call"

    deterministic = outcome_cache.get_or_set(
        ("claim_history", patient_id),
        lambda: {
            "success": True,
            "patient_id": patient_id,
            "claims": database_service.get_patient_claims(patient_id, PrivacyLevel.AGENT),
        },
    )

    return {
        "patient_id": patient_id,
        "deterministic": deterministic,
        "llm_calls": logs,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "llm_response": response,
    }


def demo_complaint_resolution(patient_id: int, claim_id: str, complaint_text: str) -> Dict:
    """Demonstrate orchestrated complaint handling via the LLM orchestrator."""

    orchestrator = ComplaintResolutionOrchestrator(model)
    prompt = (
        "Handle this customer complaint using the handle_customer_complaint tool.\n"
        "Patient ID: {pid}.\n"
        "Claim ID: {cid}.\n"
        "Complaint: \"{text}\""
    ).format(pid=patient_id, cid=claim_id, text=complaint_text)

    cache_key = ("complaint_resolution", patient_id, claim_id, complaint_text)
    if not outcome_cache.contains(cache_key):
        with database_service.scenario_scope():
            deterministic_result = orchestrator.handle_complaint_direct(
                patient_id=patient_id,
                complaint_text=complaint_text,
                claim_id=claim_id,
            )
        outcome_cache.set(cache_key, deterministic_result)

    deterministic = outcome_cache.get(cache_key)

    with database_service.scenario_scope():
        response = orchestrator.run(prompt, max_steps=6)
        logs = _extract_tool_logs(response)

    fallback_used = not any(
        log.get("name") == "handle_customer_complaint" and isinstance(log.get("output"), dict)
        and log["output"].get("success", True)
        for log in logs
    )

    fallback_reason = None
    if fallback_used:
        fallback_reason = "LLM did not produce a successful handle_customer_complaint tool call"

    return {
        "patient_id": patient_id,
        "claim_id": claim_id,
        "deterministic": deterministic,
        "llm_calls": logs,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "llm_response": response,
    }


def run_llm_demos() -> Dict[str, Dict]:
    """Execute all LLM demos and return their outputs."""

    reset_database()
    outcome_cache.clear()
    seed_demo_records()

    transactions = get_transactions()
    results = {}
    if transactions:
        results["fraud_demo"] = demo_fraud_assessment(transactions[0]["id"])

    # Demo for customer claim history using first transaction patient if available
    if transactions:
        results["claim_history_demo"] = demo_customer_claim_history(transactions[0]["customer_id"])

    # Complaint resolution demo using deterministic IDs from seed data
    results["complaint_demo"] = demo_complaint_resolution(
        patient_id=880001,
        claim_id="CLM-FD-001",
        complaint_text="I believe this duplicate billing denial was a mistake.",
    )

    return results


