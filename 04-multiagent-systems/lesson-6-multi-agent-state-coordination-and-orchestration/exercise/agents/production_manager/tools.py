"""Tools for the Production Manager Agent."""

from smolagents import tool
from typing import Dict, Any


@tool
def check_production_capacity(days_ahead: int = 7) -> str:
    """
    Check the current production capacity and queue for the next X days.
    
    Args:
        days_ahead: Number of days to forecast ahead
        
    Returns:
        A summary of production capacity and queue status
    """
    from data.factory_state import factory_state
    
    queue_size = len(factory_state.production_queue)
    total_volume = sum(order.quantity for order in factory_state.production_queue)
    daily_capacity = 10.0  # kg per day
    days_to_complete = max(1, total_volume / daily_capacity)
    
    priority_orders = [o for o in factory_state.production_queue if o.priority > 1]
    priority_volume = sum(order.quantity for order in priority_orders)
    
    return f"""Production Capacity Report:
- Queue size: {queue_size} orders
- Total volume in queue: {total_volume} kg
- Days to complete current queue: {days_to_complete:.1f} days
- Daily capacity: {daily_capacity} kg/day
- Priority orders: {len(priority_orders)} ({priority_volume} kg)"""


@tool
def add_to_production_queue(order_id: str, pasta_shape: str, quantity: float, priority: int = 1, customer_notes: str = "") -> str:
    """
    Add an order to the production queue.
    
    Args:
        order_id: Unique order identifier
        pasta_shape: Type of pasta to produce
        quantity: Amount in kg
        priority: Order priority (1=normal, 2=rush, 3=emergency)
        customer_notes: Additional notes from customer
        
    Returns:
        Status of the queuing operation
    """
    from data.factory_state import factory_state, PastaOrder
    
    # Verify pasta shape exists
    if pasta_shape not in factory_state.pasta_recipes and pasta_shape not in factory_state.custom_recipes:
        return f"Error: {pasta_shape} is not a valid pasta shape."
    
    # Create order
    order = PastaOrder(
        order_id=order_id,
        pasta_shape=pasta_shape,
        quantity=quantity,
        priority=priority,
        customer_notes=customer_notes,
        status="queued"
    )
    
    # Add to queue (priority orders at the front)
    if priority > 1:
        factory_state.production_queue.insert(0, order)
    else:
        factory_state.production_queue.append(order)
    
    # Calculate estimated delivery
    total_volume = sum(order.quantity for order in factory_state.production_queue)
    daily_capacity = 10.0  # kg per day
    estimated_delivery = total_volume / daily_capacity
    
    priority_text = "rush" if priority == 2 else "emergency" if priority == 3 else "normal"
    return f"Order {order_id} added to production queue with {priority_text} priority. Estimated delivery: {estimated_delivery:.1f} days."


@tool
def prioritize_order(order_id: str, new_priority: int) -> str:
    """
    Change the priority of an existing order in the queue.
    
    Args:
        order_id: ID of the order to update
        new_priority: New priority level (1=normal, 2=rush, 3=emergency)
        
    Returns:
        Status of the priority change
    """
    from data.factory_state import factory_state
    
    # Find the order
    for order in factory_state.production_queue:
        if order.order_id == order_id:
            order.priority = new_priority
            
            # Re-sort queue by priority
            factory_state.production_queue.sort(key=lambda x: x.priority, reverse=True)
            
            # Recalculate estimate
            total_volume = sum(order.quantity for order in factory_state.production_queue)
            daily_capacity = 10.0
            estimated_delivery = total_volume / daily_capacity
            
            priority_text = "rush" if new_priority == 2 else "emergency" if new_priority == 3 else "normal"
            return f"Order {order_id} priority updated to {priority_text}. New estimated delivery: {estimated_delivery:.1f} days."
    
    return f"Error: Order {order_id} not found in queue."

