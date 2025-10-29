"""Tools for accessing customer metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from smolagents import tool

from data.fraud_data import CUSTOMER_DATABASE
from utils.results import ToolError, ToolSuccess
from utils.tooling import safe_tool_call


@dataclass
class CustomerDetailsResult(ToolSuccess):
    customer: Dict


def _get_customer_details(customer_id: int) -> ToolSuccess | ToolError:
    if customer_id is None:
        return ToolError(
            error="customer_id is required",
            error_type="ValidationError",
        )
    record = CUSTOMER_DATABASE.get(customer_id)
    if record:
        return CustomerDetailsResult(customer=dict(record))
    return ToolError(error=f"Customer {customer_id} not found", error_type="NotFoundError")


@tool
def get_customer_details(customer_id: int) -> Dict:
    """Fetch customer details for the supplied identifier.

    Args:
        customer_id: Unique numeric identifier for the customer whose metadata is required.

    Returns:
        Dictionary containing the lookup result and customer payload when found.
    """

    return safe_tool_call(_get_customer_details, customer_id)


