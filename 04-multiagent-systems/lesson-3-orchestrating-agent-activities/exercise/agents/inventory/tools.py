"""Tools and Agent for the Inventory Agent."""

from typing import Dict, Any
from smolagents import tool, ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from data.inventory import inventory

@tool
def check_stock(item: str) -> Dict[str, Any]:
    """Check the stock level of an item.
    
    Args:
        item: The name of the item to check (e.g., 'skateboard', 'helmet', 'wheels')
    
    Returns:
        Dictionary with 'item', 'in_stock' (bool), and 'quantity' (int)
    """
    quantity = inventory.check_stock(item)
    return {
        "item": item,
        "in_stock": quantity > 0,
        "quantity": quantity
    }

@tool
def get_inventory_report() -> Dict[str, int]:
    """Get a complete inventory report.
    
    Returns:
        Dictionary mapping item names to their stock levels
    """
    return inventory.get_all_stock()

class InventoryAgent(ToolCallingAgent):
    """Agent for managing inventory using LLM reasoning."""
    
    def __init__(self):
        super().__init__(
            tools=[check_stock, get_inventory_report],
            model=model,
            name="inventory_agent",
            description="Agent responsible for checking inventory and stock levels."
        )

