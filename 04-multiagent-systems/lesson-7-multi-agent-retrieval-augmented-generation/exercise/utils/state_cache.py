"""Simple in-memory cache for deterministic scenario outcomes."""

from __future__ import annotations

from typing import Any, Dict, Hashable, Tuple


class OutcomeCache:
    """Store deterministic results keyed by tuples."""

    def __init__(self) -> None:
        self._store: Dict[Tuple[Hashable, ...], Any] = {}

    def clear(self) -> None:
        self._store.clear()

    def contains(self, key: Tuple[Hashable, ...]) -> bool:
        return key in self._store

    def get(self, key: Tuple[Hashable, ...]) -> Any:
        return self._store[key]

    def set(self, key: Tuple[Hashable, ...], value: Any) -> None:
        self._store[key] = value

    def get_or_set(self, key: Tuple[Hashable, ...], factory) -> Any:
        if key not in self._store:
            self._store[key] = factory()
        return self._store[key]


outcome_cache = OutcomeCache()

__all__ = ["OutcomeCache", "outcome_cache"]

