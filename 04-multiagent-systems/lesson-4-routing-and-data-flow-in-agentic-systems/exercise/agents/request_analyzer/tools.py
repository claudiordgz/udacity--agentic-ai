"""Tools and Agent for Request Analysis."""

from typing import Dict, Any
from smolagents import tool, ToolCallingAgent
import sys
sys.path.append('../..')
from config import model


@tool
def analyze_request(request: str) -> str:
    """Analyzes the customer request and identifies the service needed.
    This tool MUST return only the service type without additional text.

    Args:
        request: The customer's request.

    Returns:
        ONLY the identified service type (deposit, postal, loan, bill_payment, international_transfer, or general_inquiry).
    """
    # Map common request phrases to service types
    service_keywords = {
        "deposit": ["deposit", "save", "put money", "存", "存款", "存钱"],
        "postal": ["mail", "send", "package", "shipping", "邮寄", "包裹", "快递"],
        "loan": ["loan", "borrow", "贷款", "借钱"],
        "bill_payment": ["bill", "pay", "payment", "电费", "水费", "缴费", "账单"],
        "international_transfer": ["international", "transfer", "abroad", "foreign", "国际", "转账", "汇款"],
        "general_inquiry": ["hours", "information", "question", "when", "where", "how", "什么时候", "在哪里", "怎么样", "如何"]
    }
    
    request_lower = request.lower()
    for service, keywords in service_keywords.items():
        for keyword in keywords:
            if keyword.lower() in request_lower:
                return service
    
    # Default to general inquiry if no match
    return "general_inquiry"


class RequestAnalyzer(ToolCallingAgent):
    """Agent that analyzes customer requests."""

    def __init__(self):
        super().__init__(
            tools=[analyze_request],
            model=model,
            name="request_analyzer",
            description="""You are a request analyzer agent for a Chinese Postal Bank. 
            Your job is to identify what service a customer needs from their request.
            
            IMPORTANT: You MUST ONLY use the analyze_request tool to classify the request.
            NEVER provide explanations or direct responses to the customer."""
        )

