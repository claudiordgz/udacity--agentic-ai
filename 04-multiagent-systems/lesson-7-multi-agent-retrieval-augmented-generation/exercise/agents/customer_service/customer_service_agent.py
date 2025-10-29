"""Customer service agent copied from the lesson 7 demo."""

from __future__ import annotations

from smolagents import ToolCallingAgent

from core import PrivacyLevel
from tools.common_tools import (
    get_claim_details,
    get_complaint_history,
    get_patient_info,
    respond_to_complaint,
    retrieve_claim_history,
    search_knowledge_base,
    submit_complaint,
)


class CustomerServiceAgent(ToolCallingAgent):
    """Agent for handling customer inquiries and complaints with RAG capabilities."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[
                get_patient_info,
                get_claim_details,
                submit_complaint,
                get_complaint_history,
                respond_to_complaint,
                search_knowledge_base,
                retrieve_claim_history,
            ],
            model=model,
            name="customer_service",
            description="""Agent responsible for handling customer inquiries and complaints.
            You have CUSTOMER level access to the database.
            You can access basic patient info and their claims, submit complaints on their behalf,
            and provide information about insurance policies.
            Always be empathetic and helpful, especially when dealing with denied claims.
            """,
        )
        self.access_level = PrivacyLevel.CUSTOMER


