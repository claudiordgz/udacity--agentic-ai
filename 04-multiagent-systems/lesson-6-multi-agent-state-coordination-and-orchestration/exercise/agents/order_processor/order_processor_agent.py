"""Order Processor Agent for handling customer orders."""

from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.order_processor.tools import check_pasta_recipe, generate_order_id


class OrderProcessorAgent(ToolCallingAgent):
    """Agent responsible for processing customer order requests."""
    
    def __init__(self):
        super().__init__(
            tools=[check_pasta_recipe, generate_order_id],
            model=model,
            name="order_processor",
            description="Agent responsible for processing customer orders. Parses requests, identifies pasta shapes and quantities."
        )

