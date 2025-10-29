"""Agent responsible for retrieving enriched customer metadata."""

from __future__ import annotations

from typing import Dict, Optional

from smolagents import ToolCallingAgent

from config import model
from agents.customer_data.tools import _get_customer_details, get_customer_details, CustomerDetailsResult
from utils.results import ToolError


class CustomerDataAgent(ToolCallingAgent):
    """Provides access to additional customer information via tools."""

    def __init__(self) -> None:
        super().__init__(
            tools=[get_customer_details],
            model=model,
            name="customer_data_agent",
            description="Retrieve customer metadata to enrich fraud investigations.",
        )

    def fetch(self, customer_id: int) -> Optional[Dict]:
        """Convenience method wrapping the get_customer_details tool."""

        result = _get_customer_details(customer_id=customer_id)

        if isinstance(result, CustomerDetailsResult):
            return result.customer

        if isinstance(result, ToolError):
            return None

        if isinstance(result, dict):
            return result.get("customer") if result.get("success") else None

        return None



