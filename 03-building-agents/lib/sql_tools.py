from __future__ import annotations

import os
from typing import TypedDict, List, Dict, Any, Optional

from sqlalchemy import create_engine, text
import sqlalchemy

from .tooling import tool


class ColumnSchema(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Optional[str]
    primary_key: bool


def _get_engine():
    """Create a SQLAlchemy engine from env `DATABASE_URL` or default to sqlite:///sales.db.

    Notes:
        - Supported URLs: any SQLAlchemy-compatible URL (e.g., sqlite:///file.db, postgresql://...)
        - Default: sqlite:///sales.db (relative to current working directory)
    """
    db_url = os.getenv("DATABASE_URL", "sqlite:///sales.db")
    return create_engine(db_url)


@tool
def list_tables_tool() -> List[str]:
    """List all tables available in the connected database.

    Inputs:
        None

    Returns:
        List[str]: Table names.

    Notes:
        - Uses env `DATABASE_URL` if set; otherwise falls back to sqlite:///sales.db.
        - Requires SQLAlchemy.
    """
    engine = _get_engine()
    inspector = sqlalchemy.inspect(engine)
    return inspector.get_table_names()


@tool
def get_table_schema_tool(table_name: str) -> List[ColumnSchema]:
    """Return schema information about a table as a list of column descriptors.

    Inputs:
        table_name (str): Target table name.

    Returns:
        List[ColumnSchema]: Each item includes {name, type, nullable, default, primary_key}.

    Notes:
        - Column types are stringified (e.g., "INTEGER()", "VARCHAR(50)").
        - Uses env `DATABASE_URL` if set; otherwise falls back to sqlite:///sales.db.
        - Raises if the table does not exist.
    """
    engine = _get_engine()
    inspector = sqlalchemy.inspect(engine)
    cols = inspector.get_columns(table_name)
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
    return schema


@tool
def execute_sql_tool(query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query and return the result rows as a list of dicts.

    Inputs:
        query (str): ANSI SQL query to execute.

    Returns:
        List[dict]: List of rows, each row is a dict mapping column->value.

    Notes:
        - Uses env `DATABASE_URL` if set; otherwise falls back to sqlite:///sales.db.
        - Exceptions from the database driver will propagate (e.g., syntax errors).
        - For large results, consider adding LIMIT in the query.
    """
    engine = _get_engine()
    with engine.begin() as connection:
        result = connection.execute(text(query))
        keys = list(result.keys()) if result.returns_rows else []
        rows: List[Dict[str, Any]] = []
        if not keys:
            return rows
        for r in result.fetchall():
            rows.append({k: v for k, v in zip(keys, r)})
        return rows


def get_sql_tools() -> List:
    """Return the SQL-related tools defined in this module."""
    return [list_tables_tool, get_table_schema_tool, execute_sql_tool]


