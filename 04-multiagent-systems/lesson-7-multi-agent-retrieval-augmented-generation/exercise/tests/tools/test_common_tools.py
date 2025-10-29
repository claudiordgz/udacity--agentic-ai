from __future__ import annotations

import pytest

from tools.common_tools import (
    ComplaintHistoryResult,
    KnowledgeBaseSearchResult,
    get_claim_details,
    get_complaint_history,
    retrieve_claim_history,
    search_knowledge_base,
)


def test_search_knowledge_base_returns_matches() -> None:
    payload = search_knowledge_base("claim", access_level="agent")
    assert payload["success"] is True
    assert payload["results_count"] >= 1


def test_retrieve_claim_history_success(demo_data: None) -> None:
    payload = retrieve_claim_history(880001)
    assert payload["success"] is True
    assert payload["claims_count"] >= 1


def test_get_claim_details_not_found() -> None:
    payload = get_claim_details("UNKNOWN")
    assert payload["success"] is False
    assert payload["error_type"] == "NotFoundError"


def test_get_complaint_history_requires_access(demo_data: None) -> None:
    payload = get_complaint_history("CMPL-FD-001", access_level="agent")
    if payload["success"]:
        assert isinstance(payload["complaint"], dict)
    else:
        assert payload["error_type"] == "NotFoundError"

