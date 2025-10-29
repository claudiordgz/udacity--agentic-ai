from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Dict, Optional


class ToolResponse:
    """Base class for tool responses that can be serialised for smolagents."""

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


@dataclass
class ToolSuccess(ToolResponse):
    """Generic success payload for tool responses."""

    def to_dict(self) -> Dict[str, Any]:
        payload = {"success": True}
        payload.update(asdict(self))
        return payload


@dataclass
class ToolError(ToolResponse, Exception):
    """Structured error payload for tool responses."""

    error: str
    error_type: str = "ToolError"
    details: Optional[Dict[str, Any]] = None
    extras: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "success": False,
            "error": self.error,
            "error_type": self.error_type,
        }
        if self.details:
            payload["details"] = self.details
        if self.extras:
            payload.update(self.extras)
        return payload


def to_tool_payload(result: Any) -> Dict[str, Any]:
    """Normalise a tool helper result into a serialisable dictionary."""

    if isinstance(result, ToolResponse):
        return result.to_dict()

    if is_dataclass(result):
        payload = asdict(result)
        if "success" not in payload:
            payload = {"success": True, **payload}
        return payload

    if isinstance(result, dict):
        payload = dict(result)
        if "success" not in payload:
            payload = {"success": True, **payload}
        return payload

    return {"success": True, "result": result}
