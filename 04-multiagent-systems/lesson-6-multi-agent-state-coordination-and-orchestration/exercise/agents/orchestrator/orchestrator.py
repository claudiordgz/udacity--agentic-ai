"""Orchestrator Agent for coordinating the Italian Pasta Factory system."""

import traceback
import time
from typing import Dict, Any, Optional
from agents.order_processor.order_processor_agent import OrderProcessorAgent
from agents.inventory_manager.inventory_manager_agent import InventoryManagerAgent
from agents.production_manager.production_manager_agent import ProductionManagerAgent
from agents.custom_pasta_designer.custom_pasta_designer_agent import CustomPastaDesignerAgent


class PastaFactoryOrchestrator:
    """
    Advanced orchestrator with stateful orchestration, context management, and error handling.
    
    Coordinates multiple agents in the pasta factory system to process orders,
    manage inventory, schedule production, and create custom recipes.
    """
    
    def __init__(self):
        """Initialize the orchestrator with LLM-powered agents and state tracking."""
        self.order_processor = OrderProcessorAgent()
        self.inventory_manager = InventoryManagerAgent()
        self.production_manager = ProductionManagerAgent()
        self.custom_pasta_designer = CustomPastaDesignerAgent()
        
        # State management
        self.session_state: Dict[str, Any] = {}
        self.workflow_state: Dict[str, Any] = {}
        
        # Error handling configuration
        self.max_retries = 3
        self.retry_delay = 1
    
    def update_session_context(self, order_id: str, **kwargs):
        """Update the session-level context."""
        if order_id not in self.session_state:
            self.session_state[order_id] = {}
        self.session_state[order_id].update(kwargs)
    
    def get_session_context(self, order_id: str) -> Dict[str, Any]:
        """Retrieve the session-level context."""
        return self.session_state.get(order_id, {})
    
    def _retry_with_fallback(self, func, *args, **kwargs):
        """Retry logic with exponential backoff and fallback."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                    print(f"⏱️  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ All {self.max_retries} attempts failed")
        
        return f"Error: Unable to complete request after {self.max_retries} attempts. {str(last_error)}"
    
    def process_order(self, customer_request: str) -> str:
        """
        Process a customer order with STATE COORDINATION, CONFLICT DETECTION, and CONFLICT RESOLUTION.
        
        Args:
            customer_request: Natural language order request from customer
            
        Returns:
            Response to customer with order details and status or conflict resolution message
        """
        def execute_order():
            # Check if this is an inquiry (check inventory/stock) vs an actual order
            request_lower = customer_request.lower()
            if any(keyword in request_lower for keyword in ["check", "what", "show", "inventory", "ingredients", "stock", "available"]):
                if "order" not in request_lower and "need" not in request_lower and "want" not in request_lower:
                    # This is an inquiry, not an order - just return inventory info
                    print("\n📋 INQUIRY: Customer is checking inventory...")
                    inventory_response = self.inventory_manager.run(
                        f"""The customer is asking: "{customer_request}"
                        
                        Use check_inventory to show current ingredient stock levels.
                        Return a clear inventory report.
                        """
                    )
                    return inventory_response
            
            # Check if this is a custom pasta request
            if "custom" in customer_request.lower():
                print("\n🎨 CUSTOM RECIPE: Customer wants a custom pasta...")
                # Route to custom pasta designer first
                custom_response = self.create_custom_recipe(customer_request)
                return custom_response
            
            # Step 1: Parse the order (get pasta_shape and quantity)
            order_response = self.order_processor.run(
                f"""The customer says: "{customer_request}"
                
                Identify:
                1. What pasta shape they want
                2. How much they want (in kg)
                
                Use check_pasta_recipe to verify the shape exists, and generate_order_id to create an order ID.
                """
            )
            
            # Extract pasta_shape and quantity from response (simplified - in production would use better parsing)
            # For now, we'll pass the full request and let the inventory manager extract what it needs
            
            # Step 2: STATE COORDINATION - Check ingredients via specialist agent
            print("\n🔍 CONFLICT DETECTION: Checking ingredients...")
            ingredients_check = self.inventory_manager.run(
                f"""Check if we have sufficient ingredients for this order: "{customer_request}"
                
                Use check_ingredients tool with the pasta_shape and quantity from the order.
                Return whether ingredients are SUFFICIENT or INSUFFICIENT.
                """
            )
            
            # Step 3: CONFLICT DETECTION
            # Check explicitly for INSUFFICIENT (conflict) vs SUFFICIENT (no conflict)
            is_sufficient = "SUFFICIENT" in ingredients_check or "sufficient" in ingredients_check.lower()
            is_insufficient = "INSUFFICIENT" in ingredients_check or "insufficient" in ingredients_check.lower()
            
            # Step 4: CONFLICT RESOLUTION
            # Conflict = insufficient ingredients
            if is_insufficient or not is_sufficient:
                print("❌ CONFLICT DETECTED: Insufficient ingredients")
                print("📋 RESOLUTION: Denying order (Predefined Rule)")
                return f"Order Denied: Insufficient ingredients to fulfill your request.\n\n{ingredients_check}"
            
            # Step 5: No conflict - proceed with production workflow
            print("✅ No conflict detected. Proceeding to production...")
            
            # Check production capacity
            capacity_response = self.production_manager.run(
                f"""Check the production capacity and queue status.
                
                Use check_production_capacity to see current queue status.
                """
            )
            
            # Add to production queue
            queue_response = self.production_manager.run(
                f"""Add this order to the production queue.
                
                Use add_to_production_queue with the pasta_shape and quantity from: "{customer_request}"
                """
            )
            
            return f"""Order Processing Complete:
            
{ingredients_check}

{capacity_response}

{queue_response}
"""
        
        return self._retry_with_fallback(execute_order)
    
    def create_custom_recipe(self, customer_request: str) -> str:
        """
        Create a custom pasta recipe based on customer requirements.
        
        Args:
            customer_request: Natural language request for custom pasta
            
        Returns:
            Status of the custom recipe creation
        """
        def execute_design():
            prompt = f"""The customer says: "{customer_request}"
            
            Understand what custom pasta they want and design a recipe using available ingredients.
            
            Use check_inventory to see available ingredients, then use create_custom_pasta_recipe 
            to add the new recipe to the system.
            """
            return self.custom_pasta_designer.run(prompt)
        
        return self._retry_with_fallback(execute_design)
    
    def upgrade_order(self, order_id: str, new_priority: int) -> str:
        """
        Upgrade the priority of an existing order.
        
        Args:
            order_id: The order ID to upgrade
            new_priority: New priority level (1=normal, 2=rush, 3=emergency)
            
        Returns:
            Status of the upgrade
        """
        def execute_upgrade():
            prompt = f"""Update the priority of order {order_id} to priority level {new_priority}.
            
            Use prioritize_order tool to change the order priority.
            """
            return self.production_manager.run(prompt)
        
        return self._retry_with_fallback(execute_upgrade)
    
    def get_status(self, order_id: str) -> str:
        """
        Get the current status of an order.
        
        Args:
            order_id: The order ID to check
            
        Returns:
            Current status information
        """
        def execute_status():
            prompt = f"""Get the status of order {order_id}.
            
            Use check_production_capacity to see where this order is in the queue.
            """
            return self.production_manager.run(prompt)
        
        return self._retry_with_fallback(execute_status)

