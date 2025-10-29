"""Coordinator responsible for orchestrating data retrieval for fraud checks."""

from __future__ import annotations

from typing import Dict, Optional

from agents.customer_data.customer_data_agent import CustomerDataAgent
from agents.fraud_pattern.fraud_pattern_agent import FraudPatternAgent
from agents.transaction_data.transaction_data_agent import TransactionDataAgent

from core import PrivacyLevel, database


class RetrievalCoordinator:
    """Collects information from specialised retrieval agents."""

    def __init__(
        self,
        transaction_agent: TransactionDataAgent | None = None,
        customer_agent: CustomerDataAgent | None = None,
        fraud_agent: FraudPatternAgent | None = None,
    ) -> None:
        self.transaction_agent = transaction_agent or TransactionDataAgent()
        self.customer_agent = customer_agent or CustomerDataAgent()
        self.fraud_agent = fraud_agent or FraudPatternAgent()

    def run(self, transaction_id: str) -> Dict:
        transaction = self.transaction_agent.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Unknown transaction_id: {transaction_id}")

        customer_info = None
        if customer_id := transaction.get("customer_id"):
            customer_info = self.customer_agent.fetch(customer_id)

        claim_info: Optional[Dict] = None
        if claim_id := transaction.get("claim_id"):
            claim_info = database.get_claim(claim_id, PrivacyLevel.AGENT)

        fraud_analysis = self.fraud_agent.check_fraud_patterns(
            transaction,
            customer_info=customer_info,
            claim_id=transaction.get("claim_id"),
        )

        context = {
            "transaction": transaction,
            "customer_info": customer_info,
            "claim_info": claim_info,
            "fraud_analysis": fraud_analysis,
        }

        return context


