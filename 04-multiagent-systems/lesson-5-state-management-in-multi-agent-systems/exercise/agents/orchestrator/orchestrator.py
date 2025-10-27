"""Orchestrator Agent for coordinating the Colombian fruit market system with advanced state management."""

import traceback
from typing import Dict, Any, Optional
from agents.sales.sales_agent import SalesAgent
from agents.recommendation.recommendation_agent import RecommendationAgent


class MarketOrchestrator:
    """
    Advanced orchestrator with stateful orchestration, context management, and error handling.
    
    Manages interactions between SalesAgent (writes to state) and
    RecommendationAgent (reads from state), demonstrating state persistence
    across agent boundaries with robust error handling.
    """
    
    def __init__(self):
        """Initialize the orchestrator with LLM-powered agents and state tracking."""
        self.sales_agent = SalesAgent()
        self.recommendation_agent = RecommendationAgent()
        
        # State management: Track conversation-level and system-level state
        self.session_state: Dict[str, Any] = {}  # Current session context
        self.workflow_state: Dict[str, Any] = {}  # Persistent workflow state
        
        # Error handling configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def update_session_context(self, customer_id: str, **kwargs):
        """Update the session-level context for a customer."""
        if customer_id not in self.session_state:
            self.session_state[customer_id] = {}
        self.session_state[customer_id].update(kwargs)
    
    def get_session_context(self, customer_id: str) -> Dict[str, Any]:
        """Retrieve the session-level context for a customer."""
        return self.session_state.get(customer_id, {})
    
    def _retry_with_fallback(self, func, *args, **kwargs):
        """
        Retry logic with exponential backoff and fallback.
        
        Args:
            func: The function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of the function call
        """
        import time
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                    print(f"⏱️  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ All {self.max_retries} attempts failed")
        
        # Fallback: Return a graceful error message
        return f"Error: Unable to complete request after {self.max_retries} attempts. {str(last_error)}"
    
    def process_purchase(self, customer_id, item, quantity):
        """
        Process a purchase through the SalesAgent using LLM with error handling.
        
        Args:
            customer_id: The ID of the customer
            item: The fruit being purchased
            quantity: Quantity of fruit
            
        Returns:
            Confirmation message from SalesAgent
        """
        # Update context before processing
        self.update_session_context(
            customer_id,
            current_action="purchase",
            item=item,
            quantity=quantity
        )
        
        def execute_purchase():
            prompt = f"""
            Process a purchase for customer {customer_id}:
            - Item: {item}
            - Quantity: {quantity}
            
            Use the process_purchase tool to complete this transaction.
            """
            return self.sales_agent.run(prompt)
        
        # Try with retry logic
        result = self._retry_with_fallback(execute_purchase)
        
        # Update workflow state after successful processing
        if "Error" not in result:
            if customer_id not in self.workflow_state:
                self.workflow_state[customer_id] = {"purchases": []}
            self.workflow_state[customer_id]["purchases"].append({
                "item": item,
                "quantity": quantity
            })
        
        return result
    
    def get_recommendation(self, customer_id):
        """
        Get a recommendation through the RecommendationAgent using LLM with error handling.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            Personalized recommendation
        """
        # Update context
        self.update_session_context(customer_id, current_action="recommendation")
        
        def execute_recommendation():
            # Include session context in the prompt for better recommendations
            session_context = self.get_session_context(customer_id)
            
            prompt = f"""
            Generate a personalized recommendation for customer {customer_id}.
            
            Session context: {session_context}
            
            Use the generate_recommendation tool to provide a tailored suggestion.
            """
            return self.recommendation_agent.run(prompt)
        
        return self._retry_with_fallback(execute_recommendation)
    
    def get_customer_summary(self, customer_id):
        """
        Get a summary of the customer's purchase history through LLM with error handling.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            Summary of purchases
        """
        self.update_session_context(customer_id, current_action="summary")
        
        def execute_summary():
            prompt = f"""
            Get the purchase history summary for customer {customer_id}.
            
            Use the get_purchase_history tool to retrieve their past purchases.
            """
            return self.recommendation_agent.run(prompt)
        
        return self._retry_with_fallback(execute_summary)
    
    def handle_customer_request(self, customer_id, request_type, **kwargs):
        """
        Handle various types of customer requests with comprehensive error handling.
        
        Args:
            customer_id: The ID of the customer
            request_type: Type of request ('purchase', 'recommendation', 'summary')
            **kwargs: Additional arguments based on request type
            
        Returns:
            Response based on request type
        """
        try:
            if request_type == "purchase":
                return self.process_purchase(customer_id, kwargs.get("item"), kwargs.get("quantity"))
            elif request_type == "recommendation":
                return self.get_recommendation(customer_id)
            elif request_type == "summary":
                return self.get_customer_summary(customer_id)
            else:
                return f"Unknown request type: {request_type}"
        except Exception as e:
            # Graceful failure reporting
            error_msg = f"Failed to process {request_type} request for {customer_id}: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return error_msg
    
    def get_workflow_state(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the current workflow state, optionally filtered by customer."""
        if customer_id:
            return self.workflow_state.get(customer_id, {})
        return self.workflow_state
    
    def clear_session(self, customer_id: str):
        """Clear session state for a customer."""
        if customer_id in self.session_state:
            del self.session_state[customer_id]
        print(f"✅ Session cleared for {customer_id}")
