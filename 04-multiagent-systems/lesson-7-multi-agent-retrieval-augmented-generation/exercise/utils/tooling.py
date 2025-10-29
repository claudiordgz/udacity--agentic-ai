from __future__ import annotations

from typing import Any, Callable, Dict

from utils.results import ToolError, ToolResponse, to_tool_payload


def safe_tool_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Execute a tool helper with consistent error handling."""

    try:
        result = func(*args, **kwargs)
    except Exception as exc:  # pragma: no cover - defensive catch for tool execution
        return ToolError(error=str(exc), error_type=exc.__class__.__name__).to_dict()

    if isinstance(result, ToolError):
        return result.to_dict()

    if isinstance(result, ToolResponse):
        return result.to_dict()

    payload = to_tool_payload(result)
    if not payload.get("success", True) and "error_type" not in payload:
        payload = {**payload, "error_type": "ToolError"}
    return payload
