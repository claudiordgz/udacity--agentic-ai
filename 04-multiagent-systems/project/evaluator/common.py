"""Shared utilities for agent evaluators."""

from __future__ import annotations

from typing import Iterable, Optional

from smolagents import OpenAIServerModel

from project import build_model, seed_database


def ensure_seed(seed: int = 137) -> None:
    """Reset the database to a known state for deterministic checks."""

    seed_database(seed=seed)


def get_model(
    existing: Optional[OpenAIServerModel] = None,
    *,
    require_api_key: bool = False,
) -> OpenAIServerModel:
    """Return a model instance suitable for tool-calling agents."""

    if existing is not None:
        return existing
    return build_model(require_api_key=require_api_key)


def assert_tool_called(agent: object, result: object, expected_tool: str) -> Iterable[str]:
    """Ensure the LLM invoked the expected tool during a run."""

    tool_calls = getattr(result, "tool_calls", None)
    if not tool_calls:
        tool_calls = getattr(agent, "tool_calls", None)
    observed = []
    if not tool_calls and hasattr(agent, "history"):
        history = getattr(agent, "history", [])
        for step in history:
            maybe_name = getattr(step, "tool_name", None)
            if maybe_name:
                observed.append(maybe_name)
        if observed:
            tool_calls = observed

    if not tool_calls:
        return []

    observed_names = []
    for call in tool_calls:
        if isinstance(call, dict):
            name = call.get("tool_name") or call.get("tool") or call.get("name")
        else:
            name = (
                getattr(call, "tool_name", None)
                or getattr(call, "tool", None)
                or getattr(call, "name", None)
            )
        observed_names.append(name)

    if observed_names and expected_tool not in observed_names:
        raise AssertionError(
            f"Expected tool '{expected_tool}' not called. Observed: {observed_names}"
        )
    return observed_names

