from __future__ import annotations

from core import database_service
from data.fraud_data import seed_demo_records


def test_seed_demo_records_is_idempotent() -> None:
    seed_demo_records()
    first_claim_ids = {claim.id for claim in database_service.iter_claims()}
    first_counts = database_service.get_entity_counts()

    seed_demo_records()
    second_claim_ids = {claim.id for claim in database_service.iter_claims()}
    second_counts = database_service.get_entity_counts()

    assert first_claim_ids == second_claim_ids
    assert first_counts == second_counts

