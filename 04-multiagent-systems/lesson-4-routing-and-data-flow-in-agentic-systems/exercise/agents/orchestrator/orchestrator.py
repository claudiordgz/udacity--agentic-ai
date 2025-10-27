"""Orchestrator Agent for coordinating workflow."""

from typing import Dict, Any
from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.urgency_detector.tools import analyze_urgency, UrgencyDetector
from agents.request_analyzer.tools import analyze_request, RequestAnalyzer
from agents.service_router.tools import (
    handle_deposit, handle_postal, handle_loan, 
    handle_bill_payment, handle_international_transfer, handle_general_inquiry,
    ServiceRouter
)
from data.booking_manager import booking_manager


class ChineseBankPostOfficeAgent(ToolCallingAgent):
    """Enhanced orchestrator agent for the Chinese Bank Post Office with urgency detection."""

    def __init__(self):
        # Initialize child agents
        self.urgency_detector = UrgencyDetector()
        self.request_analyzer = RequestAnalyzer()
        self.service_router = ServiceRouter()
        
        super().__init__(
            tools=[],
            model=model,
            name="bank_post_office_agent",
            description="Agent for the Chinese Postal Bank that analyzes and routes customer requests.",
        )

    def handle_customer_request(self, customer_name: str, request: str, expected_service: str) -> str:
        """Handles a customer request with urgency detection and routing.
        
        The workflow implements:
        1. Content-based routing: Detect urgency from request text
        2. Priority-based routing: Use urgency to route appropriately
        3. Service identification: Classify the service type
        4. Final routing: Handle the request with appropriate priority

        Args:
            customer_name: The name of the customer.
            request: The customer's request.
            expected_service: The service we expect this request to be routed to.

        Returns:
            The response from the service agent.
        """
        # Track total requests
        booking_manager.routing_accuracy["total_requests"] += 1
        
        # Step 1: Detect if the request is urgent (content-based routing)
        urgency_prompt = f"""
        Determine if this customer request is urgent: "{request}"
        
        Use the analyze_urgency tool and return ONLY true or false.
        Do not include any explanation or additional text.
        """
        
        urgency_result = self.urgency_detector.run(urgency_prompt).strip().lower()
        is_urgent = "true" in urgency_result  # Parse the string response to a boolean
        
        if is_urgent:
            print(f"🚨 URGENT request detected from {customer_name}")
        
        # Step 2: Analyze service type
        analyzer_prompt = f"""
        You are a service classifier that ONLY returns service type categories.
        
        Analyze this customer request: "{request}"
        
        Choose EXACTLY ONE service type from this list:
        - deposit
        - postal
        - loan
        - bill_payment
        - international_transfer
        - general_inquiry
        
        Return ONLY the service type as a single word. Do not include any explanation, 
        additional text, or punctuation. Just the service type alone.
        """
        
        service_type = self.request_analyzer.run(analyzer_prompt).strip().lower()
        
        # Clean up response to ensure it's just a service type
        for valid_type in ["deposit", "postal", "loan", "bill_payment", "international_transfer", "general_inquiry"]:
            if valid_type in service_type:
                service_type = valid_type
                break
        else:
            # Default if no valid type found
            service_type = "general_inquiry"
        
        # Step 3: Route to service handler with urgency flag
        # Priority-based routing: urgency affects how we handle the request
        router_prompt = f"""
        You must call the handle_{service_type} tool with ALL three parameters:
        1. customer_name='{customer_name}'
        2. is_urgent={is_urgent}
        3. expected_service='{expected_service}'
        
        IMPORTANT: You must include the expected_service parameter.
        Do not add any explanation or additional text. Just execute the tool.
        """
        
        # Route to the service handler
        return self.service_router.run(router_prompt)

