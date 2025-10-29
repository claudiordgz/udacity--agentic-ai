"""Tools for interacting with transaction data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from smolagents import tool

from data.fraud_data import get_transactions
from utils.results import ToolError, ToolSuccess
from utils.tooling import safe_tool_call


@dataclass
class TransactionsResult(ToolSuccess):
    transactions: List[Dict]


@dataclass
class TransactionDetailResult(ToolSuccess):
    transaction: Dict


def _list_transactions() -> TransactionsResult:
    transactions = get_transactions()
    return TransactionsResult(transactions=transactions)


def _get_transaction_details(transaction_id: str) -> ToolSuccess | ToolError:
    if not transaction_id:
        return ToolError(
            error="transaction_id is required",
            error_type="ValidationError",
        )
    for transaction in get_transactions():
        if transaction["id"] == transaction_id:
            return TransactionDetailResult(transaction=transaction)
    return ToolError(error=f"Transaction {transaction_id} not found", error_type="NotFoundError")


@tool
def list_transactions() -> Dict:
    """Return all transactions slated for fraud review.

    Returns:
        Dictionary containing a success flag and the list of pending transactions.
    """

    return safe_tool_call(_list_transactions)


@tool
def get_transaction_details(transaction_id: str) -> Dict:
    """Fetch a specific transaction by its identifier.

    Args:
        transaction_id: External identifier of the transaction to retrieve.

    Returns:
        Dictionary containing a success flag and the transaction payload when found.
    """

    return safe_tool_call(_get_transaction_details, transaction_id)



