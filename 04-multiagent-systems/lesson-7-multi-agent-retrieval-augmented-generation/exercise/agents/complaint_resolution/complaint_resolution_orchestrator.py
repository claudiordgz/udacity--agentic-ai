"""Complaint resolution orchestrator copied from the lesson 7 demo."""

from __future__ import annotations

import random
from dataclasses import dataclass

from smolagents import ToolCallingAgent, tool

from agents.claim_processing import ClaimProcessingAgent
from agents.customer_service import CustomerServiceAgent
from agents.medical_review import MedicalReviewAgent
from core import PrivacyLevel, database_service
from utils.results import ToolError, ToolSuccess
from utils.tooling import safe_tool_call


@dataclass
class ComplaintWorkflowResult(ToolSuccess):
    complaint_id: str
    claim_id: str
    resolution: str
    medical_response: str


@dataclass
class RandomComplaintResult(ToolSuccess):
    patient_id: int
    claim_id: str
    complaint_text: str


class ComplaintResolutionOrchestrator(ToolCallingAgent):
    """Orchestrates the complaint resolution workflow using RAG."""

    def __init__(self, model) -> None:
        self.model = model
        self.customer_service = CustomerServiceAgent(model)
        self.medical_reviewer = MedicalReviewAgent(model)
        self.claim_processor = ClaimProcessingAgent(model)

        @tool
        def handle_customer_complaint(
            patient_id: int,
            complaint_text: str,
            claim_id: str | None = None,
        ) -> dict:
            """Handle a customer complaint about a claim.

            Args:
                patient_id: Identifier of the patient raising the complaint.
                complaint_text: Text describing the customer's complaint.
                claim_id: Optional claim identifier if already known.

            Returns:
                Dictionary describing the outcome of the complaint workflow.
            """

            return safe_tool_call(
                self._handle_complaint_workflow,
                patient_id,
                complaint_text,
                claim_id,
            )

        @tool
        def generate_random_complaint() -> dict:
            """Generate a random customer complaint for demonstration purposes."""

            denied_claims = list(database_service.iter_claims(status="denied"))
            if not denied_claims:
                return ToolError(
                    "No denied claims in database",
                    error_type="NotFoundError",
                ).to_dict()

            claim = random.choice(denied_claims)

            complaint_reasons = [
                f"I don't understand why my claim {claim.id} was denied. Can you please explain?",
                f"I believe my claim {claim.id} was denied in error. My doctor says this is a covered procedure.",
                f"This is outrageous! How can you deny claim {claim.id} when I've been paying premiums for years?",
                f"I was told procedure {claim.procedure_code} would be covered by my insurance, but claim {claim.id} was denied.",
                f"I need help with claim {claim.id}. I can't afford to pay this out of pocket and I don't understand the denial.",
            ]

            complaint_text = random.choice(complaint_reasons)

            return safe_tool_call(
                lambda: RandomComplaintResult(
                    patient_id=claim.patient_id,
                    claim_id=claim.id,
                    complaint_text=complaint_text,
                )
            )

        super().__init__(
            tools=[handle_customer_complaint, generate_random_complaint],
            model=model,
            name="orchestrator",
            description="""You are an orchestrator that manages the insurance complaint resolution workflow.
            You coordinate between customer service, medical review, and claim processing agents.
            Your focus is on handling the 98% of claims that get denied and resolving customer complaints efficiently.
            """,
        )

    def _handle_complaint_workflow(
        self,
        patient_id: int,
        complaint_text: str,
        claim_id: str | None = None,
    ) -> ToolSuccess | ToolError:
        if not claim_id:
            claims_result = self.customer_service.run(
                f"""
                We've received a complaint from patient ID {patient_id}.
                The complaint says: "{complaint_text}"

                First, retrieve the patient's claim history using retrieve_claim_history tool.
                Then identify which claim they're referring to.
                """
            )

            text_content = str(claims_result)
            if "CLM-" in text_content:
                start_idx = text_content.find("CLM-")
                end_idx = start_idx + 10
                potential_claim_id = text_content[start_idx:end_idx]
                if potential_claim_id.startswith("CLM-") and len(potential_claim_id) >= 9:
                    claim_id = potential_claim_id

        if not claim_id:
            return ToolError(
                "Could not identify which claim the complaint is about",
                error_type="NotFoundError",
                extras={"recommendation": "Please provide a specific claim ID"},
            )

        complaint_result = self.customer_service.run(
            f"""
            Submit a complaint for patient {patient_id} about claim {claim_id}.
            The complaint says: "{complaint_text}"

            Use the submit_complaint tool.
            """
        )

        complaint_id = None
        if hasattr(complaint_result, "tool_calls") and complaint_result.tool_calls:
            for call in complaint_result.tool_calls:
                if call.name == "submit_complaint" and "complaint_id" in call.arguments:
                    complaint_id = call.arguments["complaint_id"]

        if not complaint_id:
            text_content = str(complaint_result)
            if "CMPL-" in text_content:
                start_idx = text_content.find("CMPL-")
                end_idx = start_idx + 9
                potential_id = text_content[start_idx:end_idx]
                if potential_id.startswith("CMPL-"):
                    complaint_id = potential_id

        if not complaint_id:
            return ToolError(
                "Failed to register complaint",
                error_type="ComplaintRegistrationError",
                extras={"message": str(complaint_result)},
            )

        medical_review = self.medical_reviewer.run(
            f"""
            Review complaint {complaint_id} about claim {claim_id} for patient {patient_id}.
            The complaint says: "{complaint_text}"

            First, get claim details using get_claim_details tool.
            Then search for similar claims using find_similar_claims tool.
            Also search knowledge_base for relevant information.

            Based on your analysis, provide a response to the complaint.
            Use respond_to_complaint tool to record your response.
            """
        )

        medical_response = ""
        if hasattr(medical_review, "tool_calls") and medical_review.tool_calls:
            for call in medical_review.tool_calls:
                if call.name == "respond_to_complaint" and "response" in call.arguments:
                    medical_response = call.arguments["response"]

        final_response = self.customer_service.run(
            f"""
            Provide a final response to complaint {complaint_id} about claim {claim_id}.

            First, get the complaint history using get_complaint_history tool.
            Consider the medical review already provided.

            Provide a final response that is empathetic and clear about the decision.
            Use respond_to_complaint tool with resolve=true to finish handling this complaint.
            """
        )

        resolution = ""
        if hasattr(final_response, "tool_calls") and final_response.tool_calls:
            for call in final_response.tool_calls:
                if call.name == "respond_to_complaint" and "response" in call.arguments:
                    resolution = call.arguments["response"]

        if not resolution:
            complaint_info = database_service.get_complaint(complaint_id, PrivacyLevel.ADMIN)
            if complaint_info and complaint_info.get("status") == "resolved":
                resolution = complaint_info.get("resolution", "")

        if not resolution:
            text_content = str(final_response)
            if "apologize" in text_content.lower() or "review" in text_content.lower():
                sentences = text_content.split(".")
                if len(sentences) > 1:
                    resolution = ". ".join(sentences[:3]) + "."

        if not resolution:
            resolution = (
                "We have reviewed your complaint and our decision is to uphold the "
                "original claim determination based on your policy coverage."
            )

        return ComplaintWorkflowResult(
            complaint_id=complaint_id,
            claim_id=claim_id,
            resolution=resolution,
            medical_response=medical_response,
        )

    def handle_complaint_direct(
        self,
        patient_id: int,
        complaint_text: str,
        claim_id: str | None = None,
    ) -> dict:
        result = self._handle_complaint_workflow(patient_id, complaint_text, claim_id)

        if isinstance(result, ToolError):
            return result.to_dict()

        if isinstance(result, ToolSuccess):
            return result.to_dict()

        if isinstance(result, dict):
            return result

        return {
            "success": False,
            "error": "Unexpected complaint workflow result",
            "error_type": "TypeError",
        }


__all__ = ["ComplaintResolutionOrchestrator"]


