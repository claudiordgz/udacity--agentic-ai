from __future__ import annotations

import os
from typing import TypedDict, List, Dict, Any, Optional

from sqlalchemy import create_engine, text
import sqlalchemy

from .tooling import tool
from .tools import ToolStatus  # unified status envelope


class ColumnSchema(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Optional[str]
    primary_key: bool


class ListTablesResult(ToolStatus, total=False):
    tables: List[str]


class TableSchemaResult(ToolStatus, total=False):
    schema: List[ColumnSchema]


class SQLQueryResult(ToolStatus, total=False):
    rows: List[Dict[str, Any]]


def _get_engine():
    """Create a SQLAlchemy engine from env `DATABASE_URL` or default to sqlite:///sales.db.

    Notes:
        - Supported URLs: any SQLAlchemy-compatible URL (e.g., sqlite:///file.db, postgresql://...)
        - Default: sqlite:///sales.db (relative to current working directory)
    """
    db_url = os.getenv("DATABASE_URL", "sqlite:///sales.db")
    return create_engine(db_url)


@tool
def list_tables_tool() -> ListTablesResult:
    """List all tables available in the connected database with status envelope.

    Inputs:
        None

    Returns:
        {"status": "ok", "tables": [str]} on success
        {"status": "error", "error": str} on failure

    Notes:
        - Uses env `DATABASE_URL` if set; otherwise falls back to sqlite:///sales.db.
        - Requires SQLAlchemy.
    """
    try:
        engine = _get_engine()
        inspector = sqlalchemy.inspect(engine)
        return {"status": "ok", "tables": inspector.get_table_names()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@tool
def get_table_schema_tool(table_name: str) -> TableSchemaResult:
    """Return schema information about a table with status envelope.

    Inputs:
        table_name (str): Target table name.

    Returns:
        {"status": "ok", "schema": [ColumnSchema]} on success
        {"status": "no_context"} if table not found (or empty)
        {"status": "error", "error": str} on failure

    Notes:
        - Column types are stringified (e.g., "INTEGER()", "VARCHAR(50)").
        - Uses env `DATABASE_URL` if set; otherwise falls back to sqlite:///sales.db.
    """
    try:
        engine = _get_engine()
        inspector = sqlalchemy.inspect(engine)
        cols = inspector.get_columns(table_name)
        if not cols:
            return {"status": "no_context"}
        schema: List[ColumnSchema] = []
        for c in cols:
            schema.append(
                {
                    "name": c.get("name", ""),
                    "type": str(c.get("type", "")),
                    "nullable": bool(c.get("nullable", False)),
                    "default": (str(c.get("default")) if c.get("default") is not None else None),
                    "primary_key": bool(c.get("primary_key", False)),
                }
            )
        return {"status": "ok", "schema": schema}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@tool
def execute_sql_tool(query: str) -> SQLQueryResult:
    """Execute a SQL query and return rows with status envelope.

    Inputs:
        query (str): ANSI SQL query to execute.

    Returns:
        {"status": "ok", "rows": [dict]} on success
        {"status": "no_context", "rows": []} if no rows returned
        {"status": "error", "error": str} on failure

    Notes:
        - Uses env `DATABASE_URL` if set; otherwise falls back to sqlite:///sales.db.
        - For large results, consider adding LIMIT in the query.
    """
    try:
        engine = _get_engine()
        with engine.begin() as connection:
            result = connection.execute(text(query))
            keys = list(result.keys()) if result.returns_rows else []
            rows: List[Dict[str, Any]] = []
            if not keys:
                return {"status": "no_context", "rows": rows}
            for r in result.fetchall():
                rows.append({k: v for k, v in zip(keys, r)})
            return {"status": "ok", "rows": rows if rows else []}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_sql_tools() -> List:
    """Return the SQL-related tools defined in this module."""
    return [list_tables_tool, get_table_schema_tool, execute_sql_tool]


