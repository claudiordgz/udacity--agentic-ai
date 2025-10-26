"""Tools and Agent for the Sales Agent."""

from typing import Dict, Any
from smolagents import tool, ToolCallingAgent

import sys
sys.path.append('../..')
from config import model
from data.inventory import inventory

@tool
def sell_item(item: str, quantity: int) -> Dict[str, Any]:
    """Sell an item and update inventory.
    
    Args:
        item: The name of the item to sell
        quantity: The quantity to sell
        
    Returns:
        Dictionary with 'success' (bool) and 'message' (str)
    """
    if inventory.sell_item(item, quantity):
        return {
            "success": True,
            "message": f"Successfully sold {quantity} {item}(s)"
        }
    return {
        "success": False,
        "message": f"Insufficient stock. Only {inventory.check_stock(item)} {item}(s) available."
    }

class SalesAgent(ToolCallingAgent):
    """Agent for processing sales using LLM reasoning."""
    
    def __init__(self):
        super().__init__(
            tools=[sell_item],
            model=model,
            name="sales_agent",
            description="Agent responsible for processing customer purchases and sales."
        )

