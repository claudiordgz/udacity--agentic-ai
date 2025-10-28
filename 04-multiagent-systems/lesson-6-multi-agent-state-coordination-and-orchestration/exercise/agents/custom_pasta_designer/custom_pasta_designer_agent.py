"""Custom Pasta Designer Agent for creating custom pasta recipes."""

from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.custom_pasta_designer.tools import (
    check_inventory,
    create_custom_pasta_recipe,
    check_existing_recipes
)


class CustomPastaDesignerAgent(ToolCallingAgent):
    """Agent responsible for designing custom pasta recipes."""
    
    def __init__(self):
        super().__init__(
            tools=[check_inventory, create_custom_pasta_recipe, check_existing_recipes],
            model=model,
            name="custom_pasta_designer",
            description="Agent responsible for designing custom pasta recipes based on customer requirements."
        )

