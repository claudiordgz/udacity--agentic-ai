"""Production Manager Agent for managing production queue."""

from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.production_manager.tools import (
    check_production_capacity,
    add_to_production_queue,
    prioritize_order
)


class ProductionManagerAgent(ToolCallingAgent):
    """Agent responsible for managing production scheduling and prioritization."""
    
    def __init__(self):
        super().__init__(
            tools=[check_production_capacity, add_to_production_queue, prioritize_order],
            model=model,
            name="production_manager",
            description="Agent responsible for managing production scheduling and prioritization."
        )

