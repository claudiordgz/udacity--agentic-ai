from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from openai import OpenAI
from lib.messages import (
    AnyMessage,
    AIMessage,
    BaseMessage,
    UserMessage,
)
from lib.tooling import Tool, estimate_tokens_for_payload, ModelConfig
import os

class LLM:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        tools: Optional[List[Tool]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.model = model
        self.temperature = temperature
        self.tools: Dict[str, Tool] = {
            tool.name: tool for tool in (tools or [])
        }
        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        else:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            client_kwargs["api_key"] = openai_api_key

        # Prefer explicit arg, then env OPENAI_BASE_URL, then Vocareum default
        env_base_url = os.getenv("OPENAI_BASE_URL")
        client_kwargs["base_url"] = base_url or env_base_url or "https://openai.vocareum.com/v1"
    
        self.client = OpenAI(**client_kwargs)
        # Default model config (you can override externally if needed)
        self.model_config = ModelConfig.for_gpt4o_mini()
        self.last_usage: Optional[Dict[str, Any]] = None

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def _build_payload(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [m.dict() for m in messages],
        }

        if self.tools:
            # Start with all tools, then prune if exceeding input budget
            tool_specs = [tool.dict() for tool in self.tools.values()]
            payload["tools"] = tool_specs
            payload["tool_choice"] = "auto"

            # Token budget prune pass
            est = estimate_tokens_for_payload(payload["messages"], tool_specs)
            if est > self.model_config.input_budget_tokens:
                # Keep tools in declared order and drop from the end until it fits
                pruned = []
                for spec in tool_specs:
                    candidate = pruned + [spec]
                    if estimate_tokens_for_payload(payload["messages"], candidate) <= self.model_config.input_budget_tokens:
                        pruned = candidate
                    else:
                        break
                payload["tools"] = pruned

        return payload

    def _convert_input(self, input: Any) -> List[BaseMessage]:
        if isinstance(input, str):
            return [UserMessage(content=input)]
        elif isinstance(input, BaseMessage):
            return [input]
        elif isinstance(input, list) and all(isinstance(m, BaseMessage) for m in input):
            return input
        else:
            raise ValueError(f"Invalid input type {type(input)}.")

    def invoke(self, 
               input: str | BaseMessage | List[BaseMessage],
               response_format: BaseModel = None,) -> AIMessage:
        messages = self._convert_input(input)
        payload = self._build_payload(messages)
        if response_format:
            payload.update({"response_format": response_format})
            response = self.client.beta.chat.completions.parse(**payload)
        else:
            response = self.client.chat.completions.create(**payload)
        choice = response.choices[0]
        message = choice.message

        # Capture usage if provided by API
        usage = getattr(response, "usage", None)
        if usage:
            self.last_usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
        else:
            self.last_usage = None

        return AIMessage(
            content=message.content,
            tool_calls=message.tool_calls
        )
