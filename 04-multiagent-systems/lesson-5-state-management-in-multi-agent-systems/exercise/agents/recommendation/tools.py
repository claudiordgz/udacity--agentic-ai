"""Tools for the RecommendationAgent."""

from typing import Dict, Any, List
from smolagents import tool
import sys
sys.path.append('../..')
from config import model


@tool
def get_purchase_history(customer_id: str) -> str:
    """
    Retrieve the purchase history for a customer.
    
    Args:
        customer_id: The ID of the customer
        
    Returns:
        A summary of the customer's purchase history
    """
    from data.market_state import market_state
    purchase_history = market_state["purchase_history"]
    
    if customer_id not in purchase_history or not purchase_history[customer_id]:
        return f"Customer {customer_id} has no purchase history yet."
    
    purchases = purchase_history[customer_id]
    items = [f"{p['quantity']} of {p['item']}" for p in purchases]
    return f"Customer {customer_id} has purchased: {', '.join(items)}"


@tool
def generate_recommendation(customer_id: str) -> str:
    """
    Generate a personalized fruit recommendation based on purchase history.
    
    Args:
        customer_id: The ID of the customer
        
    Returns:
        A personalized recommendation message
    """
    from data.market_state import market_state
    purchase_history = market_state["purchase_history"]
    
    # Check if customer has purchase history
    if customer_id not in purchase_history or not purchase_history[customer_id]:
        return "Welcome! Since you're new, why don't you try our fresh mangos? They're sweet and juicy!"
    
    # Get the customer's last purchase
    last_purchase = purchase_history[customer_id][-1]["item"]
    
    # Provide recommendations based on last purchase
    if last_purchase == "mangos":
        return "Since you liked mangos, you might also like papayas! They're similar in sweetness and texture."
    elif last_purchase == "papayas":
        return "Since you enjoyed papayas, you might also like passion fruit! They share that tropical flavor."
    elif last_purchase == "passion fruit":
        return "Since you enjoyed passion fruit, you might like trying lulo! It has a unique tart flavor."
    elif last_purchase == "lulo":
        return "Since you liked lulo, you might enjoy granadilla! It has a sweet and seedy texture."
    else:
        return "Based on your purchase history, we have a great selection of tropical fruits today! Try something new!"


from smolagents import ToolCallingAgent


class RecommendationAgent(ToolCallingAgent):
    """Agent for providing personalized recommendations using LLM reasoning."""
    
    def __init__(self):
        super().__init__(
            tools=[get_purchase_history, generate_recommendation],
            model=model,
            name="recommendation_agent",
            description="Agent that provides personalized fruit recommendations based on customer purchase history."
        )

