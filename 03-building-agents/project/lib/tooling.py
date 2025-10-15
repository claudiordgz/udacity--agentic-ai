import inspect
import json
import datetime
from typing import (
    Any, Callable, 
    Literal, Optional, Union, TypeAlias,
    get_type_hints, get_origin, get_args,
)
from functools import wraps
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
import tiktoken


# Type alias for OpenAI's tool call implementation
ToolCall: TypeAlias = ChatCompletionMessageToolCall

class Tool:
    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        self.func = func
        self.name = name or func.__name__
        self.description = description or inspect.getdoc(func)
        self.signature = inspect.signature(func, eval_str=True)
        self.type_hints = get_type_hints(func)

        self.parameters = [
            self._build_param_schema(key, param)
            for key, param in self.signature.parameters.items()
        ]

        # Append return JSON schema (derived from type hints) to description for the model
        ret_schema = self._build_return_schema()
        if ret_schema:
            ret_schema_str = json.dumps(ret_schema, indent=2, ensure_ascii=False)
            suffix = "\n\nReturns schema:\n" + ret_schema_str
            self.description = (self.description + suffix) if self.description else suffix

    def _build_param_schema(self, name: str, param: inspect.Parameter):
        param_type = self.type_hints.get(name, str)
        schema = self._infer_json_schema_type(param_type)
        return {
            "name": name,
            "schema": schema,
            "required": param.default == inspect.Parameter.empty
        }

    def _infer_json_schema_type(self, typ: Any) -> dict:
        origin = get_origin(typ)

        # Handle Literal (enums)
        if origin is Literal:
            return {
                "type": "string",
                "enum": list(get_args(typ))
            }

        # Handle Optional[T]
        if origin is Union:
            args = get_args(typ)
            non_none = [arg for arg in args if arg is not type(None)]
            if len(non_none) == 1:
                return self._infer_json_schema_type(non_none[0])
            return {"type": "string"}  # fallback

        # Handle collections
        if origin is list:
            return {
                "type": "array",
                "items": self._infer_json_schema_type(get_args(typ)[0] if get_args(typ) else str)
            }

        if origin is dict:
            return {
                "type": "object",
                "additionalProperties": self._infer_json_schema_type(get_args(typ)[1] if get_args(typ) else str)
            }

        # Handle TypedDict-like classes (have __annotations__)
        if inspect.isclass(typ) and hasattr(typ, "__annotations__"):
            props = {}
            annotations = getattr(typ, "__annotations__", {})
            for field_name, field_type in annotations.items():
                props[field_name] = self._infer_json_schema_type(field_type)
            return {
                "type": "object",
                "properties": props,
            }

        # Primitive mappings
        mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            datetime.date: "string",
            datetime.datetime: "string",
        }

        return {"type": mapping.get(typ, "string")}

    def _build_return_schema(self) -> Optional[dict]:
        ret_type = self.type_hints.get('return')
        if not ret_type:
            return None
        try:
            return self._infer_json_schema_type(ret_type)
        except Exception:
            return None

    def dict(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        param["name"]: param["schema"]
                        for param in self.parameters
                    },
                    "required": [
                        param["name"] for param in self.parameters if param["required"]
                    ],
                    "additionalProperties": False
                }
            }
        }

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return f"<Tool name={self.name} params={[p['name'] for p in self.parameters]}>"

    @classmethod
    def from_func(cls, func: Callable):
        return cls(func)



def tool(func=None, *, name: str = None, description: str = None):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        return Tool(f, name=name, description=description)
    
    # @tool ou @tool(name="foo")
    return wrapper(func) if func else wrapper


# =================== Token utilities ===================

def estimate_tokens_for_payload(messages: list[dict], tools: list[dict] | None = None) -> int:
    """Estimate token count for gpt-4o-mini payload (messages + tools).

    Uses tiktoken o200k_base to approximate the input tokens. This is an estimate,
    not an exact server-side count.
    """
    enc = tiktoken.get_encoding("o200k_base")

    def _sanitize(obj: Any) -> Any:
        # Drop non-serializable fields (e.g., tool_calls) and coerce unknowns to str
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items() if k != "tool_calls"}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        try:
            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)

    def _tok_len(obj: dict) -> int:
        sanitized = _sanitize(obj)
        return len(enc.encode(json.dumps(sanitized, ensure_ascii=False)))

    total = _tok_len({"messages": messages})
    if tools:
        total += _tok_len({"tools": tools})
    return total


class ModelConfig:
    def __init__(self, name: str, max_context_tokens: int, input_budget_tokens: int | None = None):
        self.name = name
        self.max_context_tokens = max_context_tokens
        # Input budget (leave room for output). If None, default to 85% of max.
        self.input_budget_tokens = input_budget_tokens or int(max_context_tokens * 0.85)

    @staticmethod
    def for_gpt4o_mini():
        return ModelConfig(name="gpt-4o-mini", max_context_tokens=128_000)
