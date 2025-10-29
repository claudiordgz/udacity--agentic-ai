"""Shared domain objects and database logic for the fraud detection exercise."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Dict, List, Optional


class PrivacyLevel:
    """Simplified privacy levels for data access."""

    PUBLIC = "public"
    CUSTOMER = "customer"
    AGENT = "agent"
    FINANCIAL = "financial"
    ADMIN = "admin"


class AccessControl:
    """Utility for checking access permissions."""

    @staticmethod
    def can_access(requester_level: str, data_level: str) -> bool:
        if requester_level == PrivacyLevel.ADMIN:
            return True
        if requester_level == data_level:
            return True
        if requester_level == PrivacyLevel.FINANCIAL and data_level == PrivacyLevel.AGENT:
            return True
        if requester_level == PrivacyLevel.AGENT and data_level == PrivacyLevel.CUSTOMER:
            return True
        if data_level == PrivacyLevel.PUBLIC:
            return True
        return False


class Claim:
    """Insurance claim record."""

    def __init__(
        self,
        patient_id: int,
        service_date: str,
        procedure_code: str,
        amount: float,
        privacy_level: str = PrivacyLevel.AGENT,
    ) -> None:
        self.patient_id = patient_id
        self.service_date = service_date
        self.procedure_code = procedure_code
        self.amount = amount
        self.status = "pending"
        self.decision_reason = ""
        self.id = f"CLM-{random.randint(100000, 999999)}"
        self.timestamp = datetime.now().isoformat()
        self.privacy_level = privacy_level
        self.complaint_history: List[Dict] = []

    def to_dict(self, requester_level: str = PrivacyLevel.ADMIN) -> Dict:
        base = {
            "id": self.id,
            "patient_id": self.patient_id,
            "service_date": self.service_date,
            "status": self.status,
        }
        if AccessControl.can_access(requester_level, self.privacy_level):
            base.update(
                {
                    "procedure_code": self.procedure_code,
                    "amount": self.amount,
                    "decision_reason": self.decision_reason,
                    "timestamp": self.timestamp,
                }
            )
        if requester_level in (PrivacyLevel.AGENT, PrivacyLevel.ADMIN):
            base["complaint_history"] = list(self.complaint_history)
        return base

    def add_complaint(self, complaint_text: str, complaint_id: str | None = None) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "text": complaint_text,
        }
        if complaint_id:
            entry["complaint_id"] = complaint_id
        self.complaint_history.append(entry)


class PatientRecord:
    """Patient profile with optional medical history."""

    def __init__(
        self,
        patient_id: int,
        name: str,
        policy_number: str,
        contact_info: Dict,
        medical_history: Optional[List[Dict]] = None,
        privacy_level: str = PrivacyLevel.CUSTOMER,
    ) -> None:
        self.patient_id = patient_id
        self.name = name
        self.policy_number = policy_number
        self.contact_info = contact_info
        self.medical_history = medical_history or []
        self.privacy_level = privacy_level
        self.claim_ids: set[str] = set()

    def to_dict(self, requester_level: str = PrivacyLevel.ADMIN) -> Dict:
        base = {
            "patient_id": self.patient_id,
            "name": self.name,
            "policy_number": self.policy_number,
        }
        if AccessControl.can_access(requester_level, PrivacyLevel.CUSTOMER):
            base["contact_info"] = self.contact_info
        if AccessControl.can_access(requester_level, PrivacyLevel.AGENT):
            base["medical_history"] = self.medical_history
            base["claim_ids"] = list(self.claim_ids)
        return base


class ComplaintRecord:
    """Complaint raised against a claim."""

    def __init__(
        self,
        complaint_id: str,
        patient_id: int,
        claim_id: str,
        description: str,
        status: str = "open",
        privacy_level: str = PrivacyLevel.AGENT,
    ) -> None:
        self.complaint_id = complaint_id
        self.patient_id = patient_id
        self.claim_id = claim_id
        self.description = description
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.resolution = ""
        self.privacy_level = privacy_level
        self.response_history: List[Dict] = []

    def to_dict(self, requester_level: str = PrivacyLevel.ADMIN) -> Dict:
        base = {
            "complaint_id": self.complaint_id,
            "patient_id": self.patient_id,
            "claim_id": self.claim_id,
            "status": self.status,
            "created_at": self.created_at,
        }
        if AccessControl.can_access(requester_level, self.privacy_level):
            base.update(
                {
                    "description": self.description,
                    "updated_at": self.updated_at,
                    "resolution": self.resolution,
                    "response_history": list(self.response_history),
                }
            )
        return base

    def add_response(self, response_text: str, responder: str) -> None:
        self.response_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "text": response_text,
                "responder": responder,
            }
        )
        self.updated_at = datetime.now().isoformat()

    def resolve(self, resolution_text: str) -> None:
        self.status = "resolved"
        self.resolution = resolution_text
        self.updated_at = datetime.now().isoformat()


class Database:
    """In-memory database used for the exercise."""

    PROCEDURE_CODES: Dict[str, str] = {
        "99214": "Office visit, established patient",
        "71020": "Chest X-ray, two views",
        "81003": "Urinalysis, automated, without microscopy",
        "85025": "Complete blood count (CBC) with differential",
        "93000": "Electrocardiogram (ECG)",
        "97110": "Physical therapy, therapeutic exercises",
        "43239": "Upper GI endoscopy, biopsy",
        "99283": "Emergency department visit, moderate severity",
        "11100": "Biopsy of skin lesion",
        "36415": "Collection of venous blood by venipuncture",
    }

    def __init__(self) -> None:
        self.claims: Dict[str, Claim] = {}
        self.patients: Dict[int, PatientRecord] = {}
        self.complaints: Dict[str, ComplaintRecord] = {}

    def add_claim(self, claim: Claim) -> None:
        self.claims[claim.id] = claim
        if claim.patient_id in self.patients:
            self.patients[claim.patient_id].claim_ids.add(claim.id)

    def add_patient(self, patient: PatientRecord) -> None:
        self.patients[patient.patient_id] = patient

    def add_complaint(self, complaint: ComplaintRecord) -> None:
        self.complaints[complaint.complaint_id] = complaint
        if complaint.claim_id in self.claims:
            self.claims[complaint.claim_id].add_complaint(
                complaint.description,
                complaint.complaint_id,
            )

    def remove_complaint(self, complaint_id: str) -> None:
        """Remove a complaint and detach it from related claim history."""

        complaint = self.complaints.pop(complaint_id, None)
        if not complaint:
            return

        claim = self.claims.get(complaint.claim_id)
        if not claim:
            return

        claim.complaint_history = [
            entry
            for entry in claim.complaint_history
            if entry.get("complaint_id") != complaint_id
        ]

    def reset(self) -> None:
        """Clear all stored records."""

        self.claims.clear()
        self.patients.clear()
        self.complaints.clear()

    def get_claim(self, claim_id: str, requester_level: str) -> Optional[Dict]:
        claim = self.claims.get(claim_id)
        if claim and AccessControl.can_access(requester_level, claim.privacy_level):
            return claim.to_dict(requester_level)
        return None

    def get_patient(self, patient_id: int, requester_level: str) -> Optional[Dict]:
        patient = self.patients.get(patient_id)
        if patient and AccessControl.can_access(requester_level, patient.privacy_level):
            return patient.to_dict(requester_level)
        return None

    def get_complaint(self, complaint_id: str, requester_level: str) -> Optional[Dict]:
        complaint = self.complaints.get(complaint_id)
        if complaint and AccessControl.can_access(requester_level, complaint.privacy_level):
            return complaint.to_dict(requester_level)
        return None

    def get_patient_claims(self, patient_id: int, requester_level: str) -> List[Dict]:
        results: List[Dict] = []
        patient = self.patients.get(patient_id)
        if not patient:
            return results
        if not AccessControl.can_access(requester_level, patient.privacy_level):
            return results
        for claim_id in patient.claim_ids:
            claim_data = self.get_claim(claim_id, requester_level)
            if claim_data:
                results.append(claim_data)
        return results

    def search_claims(self, query: Dict, requester_level: str) -> List[Dict]:
        matches: List[Dict] = []
        for claim in self.claims.values():
            if not AccessControl.can_access(requester_level, claim.privacy_level):
                continue
            hit = True
            for key, value in query.items():
                if not hasattr(claim, key) or getattr(claim, key) != value:
                    hit = False
                    break
            if hit:
                matches.append(claim.to_dict(requester_level))
        return matches

    def find_similar_claims(self, claim_dict: Dict, requester_level: str) -> List[Dict]:
        results: List[Dict] = []
        target_code = claim_dict.get("procedure_code", "")
        target_amount = float(claim_dict.get("amount", 0.0))
        target_patient = claim_dict.get("patient_id")

        for claim in self.claims.values():
            if not AccessControl.can_access(requester_level, claim.privacy_level):
                continue
            score = 0.0
            if claim.procedure_code == target_code:
                score += 0.5
            diff = abs(claim.amount - target_amount)
            if diff < 50:
                score += 0.3
            elif diff < 100:
                score += 0.1
            if target_patient is not None and claim.patient_id == target_patient:
                score += 0.1
            if score >= 0.4:
                results.append(
                    {
                        "claim": claim.to_dict(requester_level),
                        "similarity_score": round(score, 2),
                    }
                )
        return sorted(results, key=lambda item: item["similarity_score"], reverse=True)


database = Database()


class DataGenerator:
    """Utility for seeding the in-memory database with sample data."""

    @staticmethod
    def _random_name() -> str:
        first_names = [
            "James",
            "Mary",
            "Robert",
            "Patricia",
            "John",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
        ]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    @staticmethod
    def generate_patient(patient_id: Optional[int] = None) -> PatientRecord:
        patient_id = patient_id or random.randint(1000, 2000)
        name = DataGenerator._random_name()
        policy_number = f"POL-{random.randint(10000, 99999)}"
        contact_info = {
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 999)} Main St, Anytown, ST {random.randint(10000, 99999)}",
        }
        return PatientRecord(
            patient_id=patient_id,
            name=name,
            policy_number=policy_number,
            contact_info=contact_info,
        )

    @staticmethod
    def generate_claim(patient_id: int) -> Claim:
        procedure_code = random.choice(list(Database.PROCEDURE_CODES.keys()))
        service_date = datetime.now().strftime("%Y-%m-%d")
        amount = round(random.uniform(50.0, 3000.0), 2)
        claim = Claim(
            patient_id=patient_id,
            service_date=service_date,
            procedure_code=procedure_code,
            amount=amount,
        )
        if random.random() < 0.1:
            claim.status = "approved"
            claim.decision_reason = "Meets coverage criteria."
        else:
            claim.status = "denied"
            claim.decision_reason = random.choice(
                [
                    "Service not covered under current plan.",
                    "Insufficient documentation provided.",
                    "Exceeds coverage limits.",
                    "Experimental/investigational procedure.",
                    "Pre-authorization required but not obtained.",
                    "Out-of-network provider.",
                    "Non-medically necessary.",
                    "Duplicate claim.",
                    "Patient not eligible on date of service.",
                    "Covered by another insurance plan.",
                ]
            )
        return claim

    @staticmethod
    def generate_complaint(claim: Claim) -> ComplaintRecord:
        complaint_id = f"CMPL-{random.randint(1000, 9999)}"
        description = random.choice(
            [
                "Claim denied without explanation.",
                "Procedure should be covered per policy.",
                "Received an unexpected bill after denial.",
                "Need reconsideration based on medical necessity.",
            ]
        )
        return ComplaintRecord(
            complaint_id=complaint_id,
            patient_id=claim.patient_id,
            claim_id=claim.id,
            description=description,
        )

    @staticmethod
    def populate_database(
        num_patients: int = 20,
        num_claims: int = 50,
        num_complaints: int = 10,
    ) -> None:
        for _ in range(num_patients):
            patient = DataGenerator.generate_patient()
            database.add_patient(patient)

        patient_ids = list(database.patients.keys())

        for _ in range(num_claims):
            patient_id = random.choice(patient_ids)
            claim = DataGenerator.generate_claim(patient_id)
            database.add_claim(claim)

        denied_claims = [claim for claim in database.claims.values() if claim.status == "denied"]
        for _ in range(min(num_complaints, len(denied_claims))):
            claim = random.choice(denied_claims)
            complaint = DataGenerator.generate_complaint(claim)
            database.add_complaint(complaint)
            if random.random() < 0.5:
                complaint.add_response("We are reviewing your case.", "Customer Service")
                if random.random() < 0.3:
                    complaint.resolve("We upheld the original decision after review.")


def reset_database() -> None:
    """Reset the shared in-memory database to an empty state."""

    database.reset()


