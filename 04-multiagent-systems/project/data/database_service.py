"""SQLite-backed data access layer for the Munder Difflin project."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import Engine, create_engine, text

from .constants import PAPER_SUPPLIES


DEFAULT_DB_PATH = Path("munder_difflin.db")


def _ensure_datetime(value: datetime | str) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@dataclass
class QuoteRecord:
    original_request: str
    total_amount: float
    quote_explanation: str
    job_type: str
    order_size: str
    event_type: str
    order_date: str


class DatabaseService:
    """Wrapper around the SQLite database with helper utilities."""

    def __init__(self, database_path: Path = DEFAULT_DB_PATH) -> None:
        self.database_path = database_path
        self.engine: Engine = create_engine(f"sqlite:///{database_path}")

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def initialize(self, *, seed: int = 137) -> None:
        self._create_transactions_table()
        self._load_quote_requests()
        self._load_quotes()
        self._seed_inventory(seed)

    def _create_transactions_table(self) -> None:
        schema = pd.DataFrame(
            {
                "id": [],
                "item_name": [],
                "transaction_type": [],
                "units": [],
                "price": [],
                "transaction_date": [],
            }
        )
        schema.to_sql("transactions", self.engine, if_exists="replace", index=False)

    def _load_quote_requests(self) -> None:
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", self.engine, if_exists="replace", index=False)

    def _load_quotes(self) -> None:
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = datetime(2025, 1, 1).isoformat()

        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))
        else:
            for column in ("job_type", "order_size", "event_type"):
                quotes_df[column] = ""

        quotes_df = quotes_df[
            [
                "request_id",
                "total_amount",
                "quote_explanation",
                "order_date",
                "job_type",
                "order_size",
                "event_type",
            ]
        ]
        quotes_df.to_sql("quotes", self.engine, if_exists="replace", index=False)

    def _seed_inventory(self, seed: int) -> None:
        inventory_df = self._generate_sample_inventory(PAPER_SUPPLIES, seed=seed)
        initial_date = datetime(2025, 1, 1).isoformat()

        transactions = [
            {
                "item_name": None,
                "transaction_type": "sales",
                "units": None,
                "price": 50_000.0,
                "transaction_date": initial_date,
            }
        ]

        for _, item in inventory_df.iterrows():
            transactions.append(
                {
                    "item_name": item["item_name"],
                    "transaction_type": "stock_orders",
                    "units": int(item["current_stock"]),
                    "price": float(item["current_stock"] * item["unit_price"]),
                    "transaction_date": initial_date,
                }
            )

        pd.DataFrame(transactions).to_sql("transactions", self.engine, if_exists="append", index=False)
        inventory_df.to_sql("inventory", self.engine, if_exists="replace", index=False)

    # ------------------------------------------------------------------
    # Inventory helpers
    # ------------------------------------------------------------------
    def _generate_sample_inventory(
        self,
        supplies: List[Dict],
        *,
        coverage: float = 0.4,
        seed: int = 137,
    ) -> pd.DataFrame:
        np.random.seed(seed)
        sample_size = max(1, int(len(supplies) * coverage))
        indices = np.random.choice(len(supplies), size=sample_size, replace=False)
        selected = [supplies[i] for i in indices]

        inventory = []
        for item in selected:
            inventory.append(
                {
                    "item_name": item["item_name"],
                    "category": item["category"],
                    "unit_price": item["unit_price"],
                    "current_stock": int(np.random.randint(200, 800)),
                    "min_stock_level": int(np.random.randint(50, 150)),
                }
            )

        return pd.DataFrame(inventory)

    def get_inventory_snapshot(self, as_of_date: str) -> Dict[str, int]:
        query = text(
            """
            SELECT
                item_name,
                SUM(CASE
                    WHEN transaction_type = 'stock_orders' THEN units
                    WHEN transaction_type = 'sales' THEN -units
                    ELSE 0
                END) as stock
            FROM transactions
            WHERE item_name IS NOT NULL
              AND transaction_date <= :as_of_date
            GROUP BY item_name
            HAVING stock > 0
            """
        )
        result = pd.read_sql(query, self.engine, params={"as_of_date": as_of_date})
        return dict(zip(result["item_name"], result["stock"]))

    def get_stock_level(self, item_name: str, as_of_date: str) -> int:
        query = text(
            """
            SELECT COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
            FROM transactions
            WHERE item_name = :item_name AND transaction_date <= :as_of_date
            """
        )
        with self.engine.connect() as conn:
            result = conn.execute(query, {"item_name": item_name, "as_of_date": as_of_date}).scalar()
        return int(result or 0)

    def get_inventory_reference(self) -> pd.DataFrame:
        return pd.read_sql("SELECT * FROM inventory", self.engine)

    # ------------------------------------------------------------------
    # Financial helpers
    # ------------------------------------------------------------------
    def record_transaction(
        self,
        *,
        item_name: Optional[str],
        transaction_type: str,
        units: Optional[int],
        price: float,
        date: datetime | str,
    ) -> int:
        date_str = _ensure_datetime(date)
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        record = pd.DataFrame(
            [
                {
                    "item_name": item_name,
                    "transaction_type": transaction_type,
                    "units": units,
                    "price": price,
                    "transaction_date": date_str,
                }
            ]
        )
        record.to_sql("transactions", self.engine, if_exists="append", index=False)
        result = pd.read_sql("SELECT last_insert_rowid() as id", self.engine)
        return int(result.iloc[0]["id"])

    def get_cash_balance(self, as_of_date: str) -> float:
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :date",
            self.engine,
            params={"date": as_of_date},
        )
        sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
        purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
        return float(sales - purchases)

    def generate_financial_report(self, as_of_date: str) -> Dict:
        cash = self.get_cash_balance(as_of_date)
        inventory_df = self.get_inventory_reference()
        inventory_value = 0.0
        summary = []
        for _, item in inventory_df.iterrows():
            stock = self.get_stock_level(item["item_name"], as_of_date)
            value = stock * item["unit_price"]
            inventory_value += value
            summary.append(
                {
                    "item_name": item["item_name"],
                    "stock": stock,
                    "unit_price": item["unit_price"],
                    "value": value,
                }
            )

        top_sales = pd.read_sql(
            text(
                """
                SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
                FROM transactions
                WHERE transaction_type = 'sales' AND transaction_date <= :date
                GROUP BY item_name
                ORDER BY total_revenue DESC
                LIMIT 5
                """
            ),
            self.engine,
            params={"date": as_of_date},
        )

        return {
            "as_of_date": as_of_date,
            "cash_balance": cash,
            "inventory_value": inventory_value,
            "total_assets": cash + inventory_value,
            "inventory_summary": summary,
            "top_selling_products": top_sales.to_dict(orient="records"),
        }

    # ------------------------------------------------------------------
    # Quote history
    # ------------------------------------------------------------------
    def search_quote_history(self, search_terms: Iterable[str], *, limit: int = 5) -> List[QuoteRecord]:
        terms = list(search_terms)
        if not terms:
            where_clause = "1=1"
            params: Dict[str, str] = {}
        else:
            conditions = []
            params = {}
            for index, term in enumerate(terms):
                key = f"term_{index}"
                conditions.append(
                    f"(LOWER(qr.response) LIKE :{key} OR LOWER(q.quote_explanation) LIKE :{key})"
                )
                params[key] = f"%{term.lower()}%"
            where_clause = " AND ".join(conditions)

        query = text(
            f"""
            SELECT
                qr.response AS original_request,
                q.total_amount,
                q.quote_explanation,
                q.job_type,
                q.order_size,
                q.event_type,
                q.order_date
            FROM quotes q
            JOIN quote_requests qr ON q.request_id = qr.id
            WHERE {where_clause}
            ORDER BY q.order_date DESC
            LIMIT :limit
            """
        )
        params["limit"] = limit
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [QuoteRecord(**dict(row._mapping)) for row in rows]


database_service = DatabaseService()

__all__ = ["database_service", "DatabaseService", "QuoteRecord", "PAPER_SUPPLIES"]

