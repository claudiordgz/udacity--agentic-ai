"""Synthesis agent that evaluates aggregated fraud context."""

from __future__ import annotations

from typing import Dict

from smolagents import ToolCallingAgent

from config import model
from agents.synthesis.tools import _synthesize_fraud_report, synthesize_fraud_report


class SynthesisAgent(ToolCallingAgent):
    """Combine retrieved evidence to produce a fraud risk report."""

    def __init__(self) -> None:
        super().__init__(
            tools=[synthesize_fraud_report],
            model=model,
            name="synthesis_agent",
            description="Synthesise fraud evidence into a risk report.",
        )

    def synthesize_report(self, context: Dict) -> Dict:
        """Convenience wrapper for the synthesize_fraud_report tool."""

        return _synthesize_fraud_report(context)


