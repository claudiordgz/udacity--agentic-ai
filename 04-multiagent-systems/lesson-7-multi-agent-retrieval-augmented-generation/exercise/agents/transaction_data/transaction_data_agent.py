"""Agent responsible for retrieving transaction-level data."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from smolagents import ToolCallingAgent

from config import model
from agents.transaction_data.tools import (
    _get_transaction_details,
    _list_transactions,
    get_transaction_details,
    list_transactions,
    TransactionDetailResult,
    TransactionsResult,
)
from utils.results import ToolError


class TransactionDataAgent(ToolCallingAgent):
    """Agent that serves transaction data via smolagents tools."""

    def __init__(self) -> None:
        super().__init__(
            tools=[get_transaction_details, list_transactions],
            model=model,
            name="transaction_data_agent",
            description="Retrieve transaction records for fraud analysis.",
        )

    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Convenience wrapper around the get_transaction_details tool."""

        result = _get_transaction_details(transaction_id)

        if isinstance(result, TransactionDetailResult):
            return result.transaction

        if isinstance(result, ToolError):
            return None

        if isinstance(result, dict):
            return result.get("transaction") if result.get("success") else None

        return None

    def iter_transactions(self) -> Iterable[Dict]:
        """Yield transactions returned by the list_transactions tool."""

        result = _list_transactions()

        if isinstance(result, TransactionsResult):
            return result.transactions

        if isinstance(result, ToolError):
            return []

        if isinstance(result, dict):
            return result.get("transactions", [])

        return []



