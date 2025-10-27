"""Tools and Agent for Urgency Detection."""

from typing import Dict, Any
from smolagents import tool, ToolCallingAgent
import sys
sys.path.append('../..')
from config import model


@tool
def analyze_urgency(request: str) -> bool:
    """Analyzes whether a customer request is urgent.
    
    Args:
        request: The customer's request text.
        
    Returns:
        True if the request is urgent, False otherwise.
    """
    # Content-based routing: check for urgency keywords
    urgency_keywords = [
        "urgent", "urgently", "urgently", "emergency", "critical", "asap", "immediately", 
        "now", "important", "hurry", "hurry up", "need urgently",
        "紧急", "急", "紧急情况", "急需", "立刻", "马上"
    ]
    
    request_lower = request.lower()
    for keyword in urgency_keywords:
        if keyword.lower() in request_lower:
            return True
    
    return False


class UrgencyDetector(ToolCallingAgent):
    """Agent that detects urgency in customer requests."""
    
    def __init__(self):
        super().__init__(
            tools=[analyze_urgency],
            model=model,
            name="urgency_detector",
            description="""Agent that analyzes customer requests to determine if they are urgent.
            Uses content-based routing to identify urgent requests by keywords."""
        )

