"""Tools for the SalesAgent."""

from typing import Dict, Any, List
from smolagents import tool
import sys
sys.path.append('../..')
from config import model


@tool
def process_purchase(customer_id: str, item: str, quantity: int) -> str:
    """
    Process a purchase transaction for a customer.
    
    Args:
        customer_id: The ID of the customer making the purchase
        item: The name of the fruit being purchased
        quantity: The quantity of fruit being purchased
        
    Returns:
        A confirmation message about the purchase status
    """
    # Import here to avoid circular imports
    from data.market_state import market_state
    
    inventory = market_state["inventory"]
    purchase_history = market_state["purchase_history"]
    
    # Check if item exists in inventory
    if item not in inventory:
        return f"Sorry, {item} is not available in our inventory."
    
    # Check if we have enough stock
    if inventory[item] < quantity:
        available = inventory[item]
        return f"Sorry, we only have {available} {item} in stock. You requested {quantity}."
    
    # Update inventory
    inventory[item] -= quantity
    
    # Update purchase history (the key part: writing to shared state)
    if customer_id not in purchase_history:
        purchase_history[customer_id] = []
    
    # Record the purchase
    purchase_history[customer_id].append({
        "item": item,
        "quantity": quantity
    })
    
    print(f"Purchase history updated for customer {customer_id}.")
    return f"Purchase successful! You bought {quantity} of {item}."


@tool
def check_inventory(item: str) -> str:
    """
    Check the current inventory for a specific fruit.
    
    Args:
        item: The name of the fruit to check
        
    Returns:
        A message with the current stock level
    """
    from data.market_state import market_state
    inventory = market_state["inventory"]
    
    if item not in inventory:
        return f"{item} is not in our inventory."
    
    quantity = inventory[item]
    return f"We have {quantity} {item} in stock."


from smolagents import ToolCallingAgent


class SalesAgent(ToolCallingAgent):
    """Agent for processing sales using LLM reasoning."""
    
    def __init__(self):
        super().__init__(
            tools=[process_purchase, check_inventory],
            model=model,
            name="sales_agent",
            description="Agent responsible for processing customer purchases and managing inventory."
        )

