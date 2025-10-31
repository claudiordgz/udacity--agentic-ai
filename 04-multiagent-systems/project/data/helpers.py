"""Compatibility helper functions wrapping the database service.

These functions mirror the signatures provided in the starter project so that
agent tools can reference them directly and still benefit from the new
`DatabaseService` implementation under the hood.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Iterable, List

from .database_service import QuoteRecord, database_service


def create_transaction(
    item_name: str | None,
    transaction_type: str,
    quantity: int | None,
    price: float,
    date: datetime | str,
) -> int:
    """Record a stock order or sales transaction and return its row id."""

    return database_service.record_transaction(
        item_name=item_name,
        transaction_type=transaction_type,
        units=quantity,
        price=price,
        date=date,
    )


def get_all_inventory(as_of_date: str) -> dict[str, int]:
    """Return available stock levels keyed by item name."""

    return database_service.get_inventory_snapshot(as_of_date)


def get_stock_level(item_name: str, as_of_date: str) -> int:
    """Return the on-hand quantity for a specific item as of the given date."""

    return database_service.get_stock_level(item_name, as_of_date)


def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """Estimate delivery date based on quantity thresholds."""

    try:
        base_date = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        base_date = datetime.now()

    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    return (base_date + timedelta(days=days)).strftime("%Y-%m-%d")


def get_cash_balance(as_of_date: str) -> float:
    """Return the cash balance as of the supplied date."""

    return database_service.get_cash_balance(as_of_date)


def generate_financial_report(as_of_date: str) -> dict:
    """Return the full financial report from the database service."""

    return database_service.generate_financial_report(as_of_date)


def search_quote_history(search_terms: Iterable[str], limit: int = 5) -> List[dict]:
    """Return historical quotes matching the provided search terms."""

    records: List[QuoteRecord] = database_service.search_quote_history(search_terms, limit=limit)
    return [asdict(record) for record in records]

