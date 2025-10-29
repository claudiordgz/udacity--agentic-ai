"""Static data used by the fraud detection exercise."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from core import Claim, PatientRecord, PrivacyLevel, database_service


# ---------------------------------------------------------------------------
# Knowledge base of fraud patterns used to power the RAG components.
# ---------------------------------------------------------------------------
FRAUD_PATTERNS: List[Dict] = [
    {
        "id": "FP-001",
        "name": "High Amount For New Customer",
        "description": (
            "Large claim amount submitted by a customer with less than one year of "
            "history. Often combined with out-of-state providers or previously denied "
            "procedures."
        ),
        "signals": [
            "amount greater than 2000 USD",
            "customer tenure shorter than 12 months",
            "recent claim denials or complaints",
        ],
        "risk_weight": 0.45,
    },
    {
        "id": "FP-002",
        "name": "Repeated Procedure Code",
        "description": (
            "Multiple claims with the same procedure code submitted within a 30 day "
            "window. Frequently associated with duplicate billing scams."
        ),
        "signals": [
            "same procedure code reused",
            "claims filed less than 30 days apart",
            "patient received the procedure recently",
        ],
        "risk_weight": 0.35,
    },
    {
        "id": "FP-003",
        "name": "Out-Of-Network Upsell",
        "description": (
            "Charges submitted by out-of-network providers that are significantly higher "
            "than historical averages. Often accompanied by billing for optional "
            "services."
        ),
        "signals": [
            "provider not in network",
            "amount exceeds historical average by > 60%",
            "supplemental procedure codes added",
        ],
        "risk_weight": 0.25,
    },
    {
        "id": "FP-004",
        "name": "Complaint Escalation After Denial",
        "description": (
            "Customers who immediately escalate a complaint after a denial are often part "
            "of organized fraud rings attempting to pressure approvals."
        ),
        "signals": [
            "complaint filed within 24 hours of denial",
            "complaint references policy exceptions",
            "prior history of denied claims",
        ],
        "risk_weight": 0.2,
    },
]


# ---------------------------------------------------------------------------
# Additional structured customer metadata to support retrieval agents.
# ---------------------------------------------------------------------------
CUSTOMER_DATABASE: Dict[int, Dict] = {
    880001: {
        "customer_id": 880001,
        "name": "Alicia Burns",
        "is_long_term_customer": False,
        "account_age_months": 6,
        "average_claim_amount": 420.0,
        "recent_denials": 2,
        "has_active_complaint": True,
    },
    880002: {
        "customer_id": 880002,
        "name": "Marcus Chen",
        "is_long_term_customer": True,
        "account_age_months": 48,
        "average_claim_amount": 280.0,
        "recent_denials": 0,
        "has_active_complaint": False,
    },
    880003: {
        "customer_id": 880003,
        "name": "Priya Desai",
        "is_long_term_customer": True,
        "account_age_months": 96,
        "average_claim_amount": 650.0,
        "recent_denials": 1,
        "has_active_complaint": False,
    },
}


# ---------------------------------------------------------------------------
# Transactions under review for the demo run.
# Each entry references a claim stored in the shared database.
# ---------------------------------------------------------------------------
TRANSACTIONS_TO_REVIEW: List[Dict] = [
    {
        "id": "TXN-FD-001",
        "claim_id": "CLM-FD-001",
        "customer_id": 880001,
        "amount": 2450.0,
        "channel": "telehealth",
        "location": "Out-of-network",
        "submitted_at": datetime.now().isoformat(),
        "metadata": {
            "provider_specialty": "Pain Management",
            "procedure_code": "97110",
            "notes": "Same procedure submitted three times this month",
        },
        "expected_risk": "high",
    },
    {
        "id": "TXN-FD-002",
        "claim_id": "CLM-FD-002",
        "customer_id": 880002,
        "amount": 1580.0,
        "channel": "in-person",
        "location": "In-network",
        "submitted_at": datetime.now().isoformat(),
        "metadata": {
            "provider_specialty": "Cardiology",
            "procedure_code": "93000",
            "notes": "Follow-up stress test",
        },
        "expected_risk": "medium",
    },
    {
        "id": "TXN-FD-003",
        "claim_id": "CLM-FD-003",
        "customer_id": 880003,
        "amount": 420.0,
        "channel": "in-person",
        "location": "In-network",
        "submitted_at": datetime.now().isoformat(),
        "metadata": {
            "provider_specialty": "Primary Care",
            "procedure_code": "99214",
            "notes": "Annual physical",
        },
        "expected_risk": "low",
    },
]


def seed_demo_records() -> None:
    """Ensure the shared database contains deterministic records for the demo."""

    # High-risk new customer with repeated procedures
    if not database_service.has_patient(880001):
        database_service.add_patient(
            PatientRecord(
                patient_id=880001,
                name="Alicia Burns",
                policy_number="POL-880001",
                contact_info={
                    "email": "alicia.burns@example.com",
                    "phone": "555-0101",
                    "address": "101 Market St, New York, NY 10001",
                },
                privacy_level=PrivacyLevel.CUSTOMER,
            )
        )

    if not database_service.has_claim("CLM-FD-001"):
        claim = Claim(
            patient_id=880001,
            service_date=(datetime.now() - timedelta(days=5)).date().isoformat(),
            procedure_code="97110",
            amount=2450.0,
            privacy_level=PrivacyLevel.AGENT,
        )
        claim.id = "CLM-FD-001"
        claim.status = "denied"
        claim.decision_reason = "Duplicate billing suspected."
        database_service.add_claim(claim)

    existing_duplicates = [
        c
        for c in database_service.iter_claims()
        if c.patient_id == 880001 and c.procedure_code == "97110" and c.id != "CLM-FD-001"
    ]
    missing_duplicates = max(0, 2 - len(existing_duplicates))
    for offset in (12, 27)[:missing_duplicates]:
        duplicate = Claim(
            patient_id=880001,
            service_date=(datetime.now() - timedelta(days=offset)).date().isoformat(),
            procedure_code="97110",
            amount=2400.0,
            privacy_level=PrivacyLevel.AGENT,
        )
        duplicate.status = "denied"
        duplicate.decision_reason = "Exceeded frequency limits."
        database_service.add_claim(duplicate)

    # Medium-risk long-term customer with slightly elevated amount
    if not database_service.has_patient(880002):
        database_service.add_patient(
            PatientRecord(
                patient_id=880002,
                name="Marcus Chen",
                policy_number="POL-880002",
                contact_info={
                    "email": "marcus.chen@example.com",
                    "phone": "555-0202",
                    "address": "202 Pine Ave, San Francisco, CA 94105",
                },
                privacy_level=PrivacyLevel.CUSTOMER,
            )
        )

    if not database_service.has_claim("CLM-FD-002"):
        claim = Claim(
            patient_id=880002,
            service_date=(datetime.now() - timedelta(days=18)).date().isoformat(),
            procedure_code="93000",
            amount=1580.0,
            privacy_level=PrivacyLevel.AGENT,
        )
        claim.id = "CLM-FD-002"
        claim.status = "pending"
        claim.decision_reason = "Awaiting review"
        database_service.add_claim(claim)

    # Low-risk loyal customer with routine visit
    if not database_service.has_patient(880003):
        database_service.add_patient(
            PatientRecord(
                patient_id=880003,
                name="Priya Desai",
                policy_number="POL-880003",
                contact_info={
                    "email": "priya.desai@example.com",
                    "phone": "555-0303",
                    "address": "303 Cedar Blvd, Austin, TX 73301",
                },
                privacy_level=PrivacyLevel.CUSTOMER,
            )
        )

    if not database_service.has_claim("CLM-FD-003"):
        claim = Claim(
            patient_id=880003,
            service_date=(datetime.now() - timedelta(days=45)).date().isoformat(),
            procedure_code="99214",
            amount=420.0,
            privacy_level=PrivacyLevel.AGENT,
        )
        claim.id = "CLM-FD-003"
        claim.status = "approved"
        claim.decision_reason = "Routine preventive visit"
        database_service.add_claim(claim)


def get_transactions() -> List[Dict]:
    """Return a copy of the transactions to analyse."""

    return [dict(transaction) for transaction in TRANSACTIONS_TO_REVIEW]


