"""Common tools adapted from the lesson 7 demo without external dependencies."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from smolagents import tool

from core import AccessControl, Claim, ComplaintRecord, PrivacyLevel, database_service
from utils.results import ToolError, ToolSuccess
from utils.tooling import safe_tool_call


KNOWLEDGE_BASE: List[Dict[str, str]] = [
    {
        "topic": "claim denial",
        "content": "Claims may be denied for reasons such as missing documentation, service not covered, or policy limits.",
        "privacy_level": PrivacyLevel.PUBLIC,
    },
    {
        "topic": "appeal process",
        "content": "Customers can appeal within 60 days by providing additional supporting medical documents.",
        "privacy_level": PrivacyLevel.PUBLIC,
    },
    {
        "topic": "coverage verification",
        "content": "Agents must verify eligibility, plan limits, deductibles, and coordination of benefits before confirming coverage.",
        "privacy_level": PrivacyLevel.AGENT,
    },
    {
        "topic": "out-of-network coverage",
        "content": "Out-of-network providers often lead to higher out-of-pocket expenses; some plans only cover emergencies.",
        "privacy_level": PrivacyLevel.PUBLIC,
    },
]


@dataclass
class KnowledgeBaseSearchResult(ToolSuccess):
    query: str
    results_count: int
    results: List[Dict[str, str]]


@dataclass
class ClaimHistoryResult(ToolSuccess):
    patient_id: int
    claims_count: int
    claims: List[Dict]


@dataclass
class ClaimDetailsResult(ToolSuccess):
    claim: Dict


@dataclass
class PatientInfoResult(ToolSuccess):
    patient: Dict


@dataclass
class SimilarClaimsResult(ToolSuccess):
    query_claim: Dict
    results_count: int
    similar_claims: List[Dict]


@dataclass
class ComplaintSubmissionResult(ToolSuccess):
    message: str
    complaint_id: str


@dataclass
class ComplaintResponseResult(ToolSuccess):
    message: str
    complaint_status: str


@dataclass
class ComplaintHistoryResult(ToolSuccess):
    complaint: Dict


@dataclass
class NewClaimProcessingResult(ToolSuccess):
    claim_id: str
    status: str
    decision_reason: str


def _search_knowledge_base(query: str, access_level: str) -> ToolSuccess | ToolError:
    if not query:
        return ToolError("query is required", error_type="ValidationError")
    lowered = query.lower()
    matches = []
    for entry in KNOWLEDGE_BASE:
        if not AccessControl.can_access(access_level, entry["privacy_level"]):
            continue
        if lowered in entry["topic"].lower() or lowered in entry["content"].lower():
            matches.append(entry)

    return KnowledgeBaseSearchResult(query=query, results_count=len(matches), results=matches)


def _retrieve_claim_history(patient_id: int, access_level: str) -> ToolSuccess | ToolError:
    if patient_id is None:
        return ToolError("patient_id is required", error_type="ValidationError")
    claims = database_service.get_patient_claims(patient_id, access_level)
    return ClaimHistoryResult(patient_id=patient_id, claims_count=len(claims), claims=claims)


def _get_claim_details(claim_id: str, access_level: str) -> ToolSuccess | ToolError:
    if not claim_id:
        return ToolError("claim_id is required", error_type="ValidationError")
    claim = database_service.get_claim(claim_id, access_level)
    if claim:
        return ClaimDetailsResult(claim=claim)
    return ToolError("Claim not found or access denied", error_type="NotFoundError")


def _get_patient_info(patient_id: int, access_level: str) -> ToolSuccess | ToolError:
    if patient_id is None:
        return ToolError("patient_id is required", error_type="ValidationError")
    patient = database_service.get_patient(patient_id, access_level)
    if patient:
        return PatientInfoResult(patient=patient)
    return ToolError("Patient not found or access denied", error_type="NotFoundError")


def _find_similar_claims(claim: Optional[Dict], access_level: str) -> ToolSuccess | ToolError:
    if not claim:
        return ToolError(
            "No claim data provided for similarity search",
            error_type="ValidationError",
            extras={"similar_claims": []},
        )

    similar = database_service.find_similar_claims(claim, access_level)
    return SimilarClaimsResult(
        query_claim=claim,
        results_count=len(similar),
        similar_claims=similar,
    )


def _submit_complaint(patient_id: int, claim_id: str, description: str) -> ToolSuccess | ToolError:
    if patient_id is None or not claim_id or not description:
        return ToolError(
            "patient_id, claim_id, and description are required",
            error_type="ValidationError",
        )
    claim = database_service.get_claim(claim_id, PrivacyLevel.ADMIN)
    if not claim:
        return ToolError("Claim not found", error_type="NotFoundError")

    complaint_id = f"CMPL-{random.randint(1000, 9999)}"
    complaint = ComplaintRecord(
        complaint_id=complaint_id,
        patient_id=patient_id,
        claim_id=claim_id,
        description=description,
    )
    database_service.add_complaint(complaint)
    return ComplaintSubmissionResult(
        message="Complaint submitted successfully",
        complaint_id=complaint_id,
    )


def _respond_to_complaint(
    complaint_id: str,
    response: str,
    responder: str,
    resolve: bool = False,
) -> ToolSuccess | ToolError:
    if not complaint_id or not response or not responder:
        return ToolError(
            "complaint_id, response, and responder are required",
            error_type="ValidationError",
        )
    complaint_data = database_service.get_complaint(complaint_id, PrivacyLevel.ADMIN)
    if not complaint_data:
        return ToolError("Complaint not found", error_type="NotFoundError")

    complaint = database_service.get_complaint_record(complaint_id)
    complaint.add_response(response, responder)
    if resolve:
        complaint.resolve(response)

    return ComplaintResponseResult(
        message="Response recorded",
        complaint_status=complaint.status,
    )


def _get_complaint_history(complaint_id: str, access_level: str) -> ToolSuccess | ToolError:
    if not complaint_id:
        return ToolError("complaint_id is required", error_type="ValidationError")
    complaint = database_service.get_complaint(complaint_id, access_level)
    if complaint:
        return ComplaintHistoryResult(complaint=complaint)
    return ToolError("Complaint not found or access denied", error_type="NotFoundError")


def _process_new_claim(claim_data: Dict) -> ToolSuccess | ToolError:
    required_fields = {"patient_id", "service_date", "procedure_code", "amount"}
    missing = sorted(required_fields - set(claim_data or {}))
    if missing:
        return ToolError(
            f"Missing claim fields: {', '.join(missing)}",
            error_type="ValidationError",
        )
    claim = Claim(
        patient_id=claim_data["patient_id"],
        service_date=claim_data["service_date"],
        procedure_code=claim_data["procedure_code"],
        amount=float(claim_data["amount"]),
    )

    if random.random() < 0.15:
        claim.status = "approved"
        claim.decision_reason = "Meets coverage criteria."
    else:
        claim.status = "denied"
        claim.decision_reason = random.choice(
            [
                "Service not covered under current plan.",
                "Insufficient documentation provided.",
                "Pre-authorization required but not obtained.",
                "Non-medically necessary.",
            ]
        )

    database_service.add_claim(claim)
    return NewClaimProcessingResult(
        claim_id=claim.id,
        status=claim.status,
        decision_reason=claim.decision_reason,
    )


@tool
def search_knowledge_base(query: str, access_level: str = PrivacyLevel.AGENT) -> Dict:
    """Search the canned knowledge base using substring matching.

    Args:
        query: Text to search for within knowledge base topics and content.
        access_level: Privacy level of the caller requesting the information.

    Returns:
        Structured search results with the number of matches and their details.
    """

    return safe_tool_call(_search_knowledge_base, query, access_level)


@tool
def retrieve_claim_history(patient_id: int, access_level: str = PrivacyLevel.AGENT) -> Dict:
    """Retrieve the list of claims for a patient at a given access level.

    Args:
        patient_id: Identifier of the patient whose claims are requested.
        access_level: Privacy level of the requester, used for filtering.

    Returns:
        Dictionary containing a success flag, number of claims, and claim list.
    """

    return safe_tool_call(_retrieve_claim_history, patient_id, access_level)


@tool
def get_claim_details(claim_id: str, access_level: str = PrivacyLevel.AGENT) -> Dict:
    """Return detailed information about a specific claim.

    Args:
        claim_id: Identifier of the claim to inspect.
        access_level: Privacy level of the requester.

    Returns:
        Claim metadata when accessible or an error response otherwise.
    """

    return safe_tool_call(_get_claim_details, claim_id, access_level)


@tool
def get_patient_info(patient_id: int, access_level: str = PrivacyLevel.AGENT) -> Dict:
    """Retrieve patient information with respect to access controls.

    Args:
        patient_id: Identifier of the patient whose record is needed.
        access_level: Privacy level of the requester.

    Returns:
        Patient information or an error if access is denied.
    """

    return safe_tool_call(_get_patient_info, patient_id, access_level)


@tool
def find_similar_claims(
    claim: Optional[Dict] = None,
    access_level: str = PrivacyLevel.AGENT,
) -> Dict:
    """Locate heuristically similar claims for comparison.

    Args:
        claim: Candidate claim dictionary used as the similarity seed.
        access_level: Privacy level of the requester.

    Returns:
        Collection of similar claims ranked by heuristic score.
    """

    return safe_tool_call(_find_similar_claims, claim, access_level)


@tool
def submit_complaint(patient_id: int, claim_id: str, description: str) -> Dict:
    """File a new complaint on behalf of a patient.

    Args:
        patient_id: Identifier of the complaining patient.
        claim_id: Identifier of the related claim.
        description: Free-text description of the complaint.

    Returns:
        Confirmation payload with the new complaint identifier.
    """

    return safe_tool_call(_submit_complaint, patient_id, claim_id, description)


@tool
def respond_to_complaint(
    complaint_id: str,
    response: str,
    responder: str,
    resolve: bool = False,
) -> Dict:
    """Record a response and optional resolution for an existing complaint.

    Args:
        complaint_id: Identifier of the complaint being updated.
        response: Textual response supplied by the responder.
        responder: Name or role of the responder.
        resolve: Whether the complaint should be marked resolved.

    Returns:
        Success payload describing the updated complaint state.
    """

    return safe_tool_call(_respond_to_complaint, complaint_id, response, responder, resolve)


@tool
def get_complaint_history(complaint_id: str, access_level: str = PrivacyLevel.AGENT) -> Dict:
    """Fetch the history of a complaint when access permits.

    Args:
        complaint_id: Identifier of the complaint to retrieve.
        access_level: Privacy level of the requester.

    Returns:
        Complaint history or an error when insufficient permissions exist.
    """

    return safe_tool_call(_get_complaint_history, complaint_id, access_level)


@tool
def process_new_claim(claim_data: Dict) -> Dict:
    """Ingest a newly submitted claim and apply simple decision rules.

    Args:
        claim_data: Dictionary describing the incoming claim payload.

    Returns:
        Outcome of the claim decision including status and reasoning.
    """

    return safe_tool_call(_process_new_claim, claim_data)


