from __future__ import annotations

from utils.state_cache import OutcomeCache


def test_outcome_cache_get_or_set_and_clear() -> None:
    cache = OutcomeCache()
    key = ("demo", 1)

    value = cache.get_or_set(key, lambda: {"result": 42})
    assert value == {"result": 42}

    # Subsequent get should not call factory again (value unchanged)
    value_again = cache.get_or_set(key, lambda: {"result": 0})
    assert value_again == {"result": 42}

    cache.clear()
    assert not cache.contains(key)

