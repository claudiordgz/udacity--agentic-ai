"""Sales Agent for processing fruit purchases."""


class SalesAgent:
    """
    Agent responsible for processing purchases and updating shared state.
    
    This agent reads and writes to the shared market_state dictionary,
    specifically managing inventory and recording purchase history.
    """
    
    def __init__(self, inventory, purchase_history):
        """
        Initialize the sales agent with references to shared state.
        
        Args:
            inventory: Reference to the inventory dictionary in shared state
            purchase_history: Reference to the purchase_history dictionary in shared state
        """
        self.inventory = inventory
        self.purchase_history = purchase_history  # Reference to shared state
    
    def process_purchase(self, customer_id, item, quantity):
        """
        Process a purchase, update inventory, and record in purchase history.
        
        Args:
            customer_id: The ID of the customer making the purchase
            item: The name of the fruit being purchased
            quantity: The quantity of fruit being purchased
            
        Returns:
            A confirmation message about the purchase
        """
        # Check if item exists in inventory
        if item not in self.inventory:
            return f"Sorry, {item} is not available in our inventory."
        
        # Check if we have enough stock
        if self.inventory[item] < quantity:
            available = self.inventory[item]
            return f"Sorry, we only have {available} {item} in stock. You requested {quantity}."
        
        # Update inventory
        self.inventory[item] -= quantity
        
        # Update purchase history (the key part: writing to shared state)
        if customer_id not in self.purchase_history:
            self.purchase_history[customer_id] = []
        
        # Record the purchase
        self.purchase_history[customer_id].append({
            "item": item,
            "quantity": quantity
        })
        
        print(f"Purchase history updated for customer {customer_id}.")
        return f"Purchase successful! You bought {quantity} of {item}."
