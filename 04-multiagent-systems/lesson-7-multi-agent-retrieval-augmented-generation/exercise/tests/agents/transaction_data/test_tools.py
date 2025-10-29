from __future__ import annotations

from agents.transaction_data.tools import (
    TransactionsResult,
    TransactionDetailResult,
    _get_transaction_details,
    _list_transactions,
    get_transaction_details,
    list_transactions,
)
from data.fraud_data import get_transactions
from utils.results import ToolError


def test_list_transactions_returns_tool_success_type() -> None:
    result = _list_transactions()

    assert isinstance(result, TransactionsResult)
    assert isinstance(result.transactions, list)
    assert len(result.transactions) == len(get_transactions())


def test_list_transactions_tool_wrapper_formats_dict() -> None:
    payload = list_transactions()

    assert payload["success"] is True
    assert isinstance(payload["transactions"], list)
    assert payload["transactions"][0]["id"] == get_transactions()[0]["id"]


def test_get_transaction_details_success_cases() -> None:
    txn_id = get_transactions()[0]["id"]
    result = _get_transaction_details(txn_id)

    assert isinstance(result, TransactionDetailResult)
    assert result.transaction["id"] == txn_id

    payload = get_transaction_details(txn_id)
    assert payload["success"] is True
    assert payload["transaction"]["id"] == txn_id


def test_get_transaction_details_missing_returns_error() -> None:
    result = _get_transaction_details("UNKNOWN")
    assert isinstance(result, ToolError)
    assert result.error_type == "NotFoundError"

    payload = get_transaction_details("UNKNOWN")
    assert payload["success"] is False
    assert payload["error_type"] == "NotFoundError"

