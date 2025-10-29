from __future__ import annotations

import pytest

from agents.customer_data.tools import (
    CustomerDetailsResult,
    _get_customer_details,
    get_customer_details,
)
from utils.results import ToolError


def test_get_customer_details_success(demo_data: None) -> None:
    result = _get_customer_details(880001)
    assert isinstance(result, CustomerDetailsResult)
    assert result.customer["customer_id"] == 880001

    payload = get_customer_details(880001)
    assert payload["success"] is True
    assert payload["customer"]["customer_id"] == 880001


@pytest.mark.parametrize("customer_id", [None, 999999])
def test_get_customer_details_errors(customer_id: int | None) -> None:
    result = _get_customer_details(customer_id)
    assert isinstance(result, ToolError)

    payload = get_customer_details(customer_id)
    assert payload["success"] is False

