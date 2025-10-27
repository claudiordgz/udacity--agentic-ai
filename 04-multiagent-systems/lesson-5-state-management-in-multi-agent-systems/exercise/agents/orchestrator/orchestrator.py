"""Orchestrator Agent for coordinating the Colombian fruit market system."""

from agents.sales.tools import SalesAgent
from agents.recommendation.tools import RecommendationAgent


class MarketOrchestrator:
    """
    Orchestrator that coordinates the fruit market system.
    
    Manages interactions between SalesAgent (writes to state) and
    RecommendationAgent (reads from state), demonstrating state persistence
    across agent boundaries.
    """
    
    def __init__(self):
        """Initialize the orchestrator with LLM-powered agents."""
        self.sales_agent = SalesAgent()
        self.recommendation_agent = RecommendationAgent()
    
    def process_purchase(self, customer_id, item, quantity):
        """
        Process a purchase through the SalesAgent using LLM.
        
        Args:
            customer_id: The ID of the customer
            item: The fruit being purchased
            quantity: Quantity of fruit
            
        Returns:
            Confirmation message from SalesAgent
        """
        prompt = f"""
        Process a purchase for customer {customer_id}:
        - Item: {item}
        - Quantity: {quantity}
        
        Use the process_purchase tool to complete this transaction.
        """
        return self.sales_agent.run(prompt)
    
    def get_recommendation(self, customer_id):
        """
        Get a recommendation through the RecommendationAgent using LLM.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            Personalized recommendation
        """
        prompt = f"""
        Generate a personalized recommendation for customer {customer_id}.
        
        Use the generate_recommendation tool to provide a tailored suggestion.
        """
        return self.recommendation_agent.run(prompt)
    
    def get_customer_summary(self, customer_id):
        """
        Get a summary of the customer's purchase history through LLM.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            Summary of purchases
        """
        prompt = f"""
        Get the purchase history summary for customer {customer_id}.
        
        Use the get_purchase_history tool to retrieve their past purchases.
        """
        return self.recommendation_agent.run(prompt)
