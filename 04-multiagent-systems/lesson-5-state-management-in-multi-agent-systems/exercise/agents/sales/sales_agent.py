"""Sales Agent for processing fruit purchases."""

from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.sales.tools import process_purchase, check_inventory


class SalesAgent(ToolCallingAgent):
    """Agent for processing sales using LLM reasoning."""
    
    def __init__(self):
        super().__init__(
            tools=[process_purchase, check_inventory],
            model=model,
            name="sales_agent",
            description="Agent responsible for processing customer purchases and managing inventory."
        )

