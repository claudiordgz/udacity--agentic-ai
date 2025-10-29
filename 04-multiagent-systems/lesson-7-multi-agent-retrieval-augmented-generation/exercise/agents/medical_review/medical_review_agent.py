"""Medical review agent copied from the lesson 7 demo."""

from __future__ import annotations

from smolagents import ToolCallingAgent

from core import PrivacyLevel
from tools.common_tools import (
    find_similar_claims,
    get_claim_details,
    get_patient_info,
    respond_to_complaint,
    search_knowledge_base,
)


class MedicalReviewAgent(ToolCallingAgent):
    """Agent for medical review of claims with RAG capabilities."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[
                get_claim_details,
                get_patient_info,
                find_similar_claims,
                search_knowledge_base,
                respond_to_complaint,
            ],
            model=model,
            name="medical_reviewer",
            description="""Agent responsible for medical review of claims.
            You have AGENT level access to the database.
            You focus on reviewing denied claims that have received complaints,
            and can provide medical justification for decisions.
            Use the knowledge base and similar claims history to inform your decisions.
            """,
        )
        self.access_level = PrivacyLevel.AGENT


