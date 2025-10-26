"""Orchestrator Agent for coordinating workflows with LLM reasoning."""

from typing import Dict, Any
from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.inventory.tools import check_stock, get_inventory_report, InventoryAgent
from agents.sales.tools import sell_item, SalesAgent

class OrchestratorAgent(ToolCallingAgent):
    """Orchestrator that coordinates workflow between agents using LLM reasoning."""
    
    def __init__(self):
        # Initialize child agents
        self.inventory_agent = InventoryAgent()
        self.sales_agent = SalesAgent()
        
        # Orchestrator doesn't need tools - it routes to agents
        super().__init__(
            tools=[],
            model=model,
            name="orchestrator_agent",
            description="Orchestrator that routes requests to appropriate agents."
        )
    
    def run(self, request: Dict[str, Any]) -> str:
        """
        Main orchestration logic.
        
        Workflow:
        1. Check stock first suing InventoryAgent tools
        2. If action is "inquire" -> return stock information
        3. If action is "purchase":
           - If in stock -> process sale using SalesAgent tools
           - If not in stock -> return error message
        
        Args:
            request: Dictionary with keys:
                - "action": "purchase" or "inquire"
                - "item": name of the item (e.g., "skateboard")
                - "quantity": quantity to purchase (optional, for purchase actions)
        
        Returns:
            Response string to the customer
        """
        action = request.get("action", "")
        item = request.get("item", "")
        quantity = request.get("quantity", 1)
        
        # Use LLM reasoning to determine routing, then route to agents
        # For now, implement deterministic routing based on action
        # The LLM will be consulted for complex routing decisions in the future
        
        if action == "inquire":
            # Route to InventoryAgent for stock inquiry
            prompt = f"""Check the stock level for {item} and provide information about availability."""
            return self.inventory_agent.run(prompt)
        
        elif action == "purchase":
            # First check stock via InventoryAgent
            stock_prompt = f"""Check the stock level for {item}."""
            stock_response = self.inventory_agent.run(stock_prompt)
            
            # Parse stock info from response (for now, check directly)
            stock_info = check_stock(item)
            
            if stock_info["quantity"] >= quantity:
                # Enough stock - route to SalesAgent
                sales_prompt = f"""Process a sale for {quantity} {item}(s)."""
                return self.sales_agent.run(sales_prompt)
            else:
                return f"Insufficient stock. We only have {stock_info['quantity']} {item}(s) available, but you requested {quantity}."
        
        else:
            return f"Unknown action: {action}"

