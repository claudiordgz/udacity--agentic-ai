from __future__ import annotations

from core import ComplaintRecord, PrivacyLevel, database_service


def test_scenario_scope_restores_complaints() -> None:
    initial_ids = set(database_service.list_complaint_ids())

    complaint = ComplaintRecord(
        complaint_id="CMPL-TEST-001",
        patient_id=1,
        claim_id="CLM-TEST-001",
        description="Test complaint",
    )

    with database_service.scenario_scope():
        database_service.add_complaint(complaint)
        assert "CMPL-TEST-001" in database_service.list_complaint_ids()

    # After scope exit the complaint should be removed
    assert set(database_service.list_complaint_ids()) == initial_ids


def test_clear_complaints_removes_specified_entries() -> None:
    complaint = ComplaintRecord(
        complaint_id="CMPL-KEEP",
        patient_id=1,
        claim_id="CLM-KEEP",
        description="Keep",
    )
    other = ComplaintRecord(
        complaint_id="CMPL-DROP",
        patient_id=1,
        claim_id="CLM-DROP",
        description="Drop",
    )

    database_service.add_complaint(complaint)
    database_service.add_complaint(other)

    database_service.clear_complaints(["CMPL-DROP"])

    assert "CMPL-DROP" not in database_service.list_complaint_ids()
    stored = database_service.get_complaint("CMPL-KEEP", PrivacyLevel.ADMIN)
    assert stored is not None

