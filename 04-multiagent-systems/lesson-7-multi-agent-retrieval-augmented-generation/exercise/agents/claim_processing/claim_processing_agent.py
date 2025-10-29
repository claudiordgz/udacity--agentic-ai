"""Claim processing agent copied from the lesson 7 demo."""

from __future__ import annotations

from smolagents import ToolCallingAgent

from core import PrivacyLevel
from tools.common_tools import (
    find_similar_claims,
    get_claim_details,
    process_new_claim,
    search_knowledge_base,
)


class ClaimProcessingAgent(ToolCallingAgent):
    """Agent for processing health insurance claims with RAG capabilities."""

    def __init__(self, model) -> None:
        super().__init__(
            tools=[process_new_claim, find_similar_claims, get_claim_details, search_knowledge_base],
            model=model,
            name="claim_processor",
            description="""Agent responsible for processing health insurance claims.
            You have access to the claims database but can only access data at the AGENT privacy level.
            Always search for similar claims and reference knowledge base when making decisions.
            Remember that most claims (98%) should be denied based on company policy.
            """,
        )
        self.access_level = PrivacyLevel.AGENT


