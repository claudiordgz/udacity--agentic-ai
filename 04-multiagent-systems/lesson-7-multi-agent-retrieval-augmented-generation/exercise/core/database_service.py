"""Thin service layer around the shared in-memory database.

The goal of this module is to provide a single coordination point for all
read/write interactions with the global ``database`` object. Using the service
helps us swap out implementations (e.g. persistence, logging) and reason about
side-effects in tests and demos.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterable, Iterator, Optional, Set

from .state import (
    AccessControl,
    Claim,
    ComplaintRecord,
    DataGenerator,
    Database,
    PatientRecord,
    PrivacyLevel,
    database,
    reset_database,
)


class DatabaseService:
    """Coordinate all direct database access for the exercise code."""

    def __init__(self) -> None:
        self._db: Database = database

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def reset_all(self) -> None:
        """Clear all database tables and cached outcomes."""

        reset_database()

    def populate_random_demo_data(
        self,
        *,
        num_patients: int = 20,
        num_claims: int = 50,
        num_complaints: int = 10,
    ) -> None:
        """Populate random sample data using the existing generator."""

        DataGenerator.populate_database(
            num_patients=num_patients,
            num_claims=num_claims,
            num_complaints=num_complaints,
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def has_patient(self, patient_id: int) -> bool:
        return patient_id in self._db.patients

    def add_patient(self, patient: PatientRecord) -> None:
        self._db.add_patient(patient)

    def get_patient(self, patient_id: int, access_level: str) -> Optional[Dict]:
        return self._db.get_patient(patient_id, access_level)

    def get_patient_claims(self, patient_id: int, access_level: str) -> list[Dict]:
        return self._db.get_patient_claims(patient_id, access_level)

    def has_claim(self, claim_id: str) -> bool:
        return claim_id in self._db.claims

    def add_claim(self, claim: Claim) -> None:
        self._db.add_claim(claim)

    def get_claim(self, claim_id: str, access_level: str) -> Optional[Dict]:
        return self._db.get_claim(claim_id, access_level)

    def get_claim_record(self, claim_id: str) -> Optional[Claim]:
        return self._db.claims.get(claim_id)

    def search_claims(self, query: Dict, access_level: str) -> list[Dict]:
        return self._db.search_claims(query, access_level)

    def find_similar_claims(self, claim_dict: Dict, access_level: str) -> list[Dict]:
        return self._db.find_similar_claims(claim_dict, access_level)

    def iter_claims(self, *, status: str | None = None) -> Iterator[Claim]:
        for claim in self._db.claims.values():
            if status is None or claim.status == status:
                yield claim

    def add_complaint(self, complaint: ComplaintRecord) -> None:
        self._db.add_complaint(complaint)

    def get_complaint(self, complaint_id: str, access_level: str) -> Optional[Dict]:
        return self._db.get_complaint(complaint_id, access_level)

    def get_complaint_record(self, complaint_id: str) -> Optional[ComplaintRecord]:
        return self._db.complaints.get(complaint_id)

    def remove_complaint(self, complaint_id: str) -> None:
        self._db.remove_complaint(complaint_id)

    def list_complaint_ids(self) -> list[str]:
        return list(self._db.complaints.keys())

    def clear_complaints(self, complaint_ids: Optional[Iterable[str]] = None) -> None:
        ids = list(complaint_ids) if complaint_ids is not None else list(self._db.complaints)
        for complaint_id in ids:
            self._db.remove_complaint(complaint_id)

    def get_procedure_codes(self) -> Dict[str, str]:
        return dict(self._db.procedure_codes)

    def get_entity_counts(self) -> Dict[str, int]:
        return {
            "patients": len(self._db.patients),
            "claims": len(self._db.claims),
            "complaints": len(self._db.complaints),
        }

    # ------------------------------------------------------------------
    # Scenario scoping utilities
    # ------------------------------------------------------------------
    def snapshot_complaints(self) -> Set[str]:
        return set(self._db.complaints.keys())

    def restore_complaints(self, snapshot: Iterable[str]) -> None:
        preserved = set(snapshot)
        for complaint_id in list(self._db.complaints.keys()):
            if complaint_id not in preserved:
                self._db.remove_complaint(complaint_id)

    @contextmanager
    def scenario_scope(self) -> Iterator[None]:
        """Context manager to isolate complaint mutations within a scenario."""

        snapshot = self.snapshot_complaints()
        try:
            yield
        finally:
            self.restore_complaints(snapshot)


database_service = DatabaseService()

__all__ = [
    "database_service",
    "DatabaseService",
]


