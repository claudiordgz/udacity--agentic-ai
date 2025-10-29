"""Workflow utilities for the fraud detection exercise."""

from __future__ import annotations

from typing import List

from config import model
from core import reset_database
from data.fraud_data import get_transactions, seed_demo_records
from agents.fraud_detection.fraud_detection_agent import FraudDetectionAgent


def demonstrate_fraud_detection() -> List[dict]:
    """Run the multi-agent fraud detection workflow and return the results."""

    reset_database()
    seed_demo_records()

    agent = FraudDetectionAgent(model)

    results = []
    for transaction in get_transactions():
        result = agent.evaluate_transaction(transaction["id"])
        results.append(result)

        if result.get("success"):
            report = result["report"]["text"]
            print(report)
            print("-" * 70)
        else:
            print(f"Failed to evaluate transaction {transaction['id']}: {result.get('error')}")

    return results


