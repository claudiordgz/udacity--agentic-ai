"""Inventory Manager Agent for managing ingredient inventory."""

from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.inventory_manager.tools import check_inventory, check_pasta_recipe, check_ingredients


class InventoryManagerAgent(ToolCallingAgent):
    """Agent responsible for managing ingredient inventory."""
    
    def __init__(self):
        super().__init__(
            tools=[check_inventory, check_pasta_recipe, check_ingredients],
            model=model,
            name="inventory_manager",
            description="Agent responsible for tracking and managing ingredient inventory."
        )

