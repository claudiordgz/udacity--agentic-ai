"""Recommendation Agent for providing personalized fruit recommendations."""


class RecommendationAgent:
    """
    Agent that provides personalized recommendations based on purchase history.
    
    This agent reads from the shared purchase_history state (written by SalesAgent)
    to provide context-aware recommendations without needing direct knowledge of sales.
    """
    
    def __init__(self, purchase_history):
        """
        Initialize the recommendation agent with reference to shared state.
        
        Args:
            purchase_history: Reference to the purchase_history dictionary in shared state
        """
        self.purchase_history = purchase_history  # Reference to shared state
    
    def generate_recommendation(self, customer_id):
        """
        Generate a personalized recommendation based on the customer's purchase history.
        
        Args:
            customer_id: The ID of the customer requesting recommendations
            
        Returns:
            A personalized recommendation message
        """
        # Check if customer has purchase history
        if customer_id not in self.purchase_history or not self.purchase_history[customer_id]:
            return "Welcome! Since you're new, why don't you try our fresh mangos? They're sweet and juicy!"
        
        # Get the customer's last purchase
        last_purchase = self.purchase_history[customer_id][-1]["item"]
        
        # Provide recommendations based on last purchase
        if last_purchase == "mangos":
            return "Since you liked mangos, you might also like papayas! They're similar in sweetness and texture."
        elif last_purchase == "papayas":
            return "Since you enjoyed papayas, you might also like passion fruit! They share that tropical flavor."
        elif last_purchase == "passion fruit":
            return "Since you enjoyed passion fruit, you might like trying lulo! It has a unique tart flavor."
        elif last_purchase == "lulo":
            return "Since you liked lulo, you might enjoy granadilla! It has a sweet and seedy texture."
        else:
            return "Based on your purchase history, we have a great selection of tropical fruits today! Try something new!"
    
    def get_purchase_summary(self, customer_id):
        """
        Get a summary of the customer's purchase history.
        
        Args:
            customer_id: The ID of the customer
            
        Returns:
            A summary of their purchases
        """
        if customer_id not in self.purchase_history or not self.purchase_history[customer_id]:
            return "You haven't made any purchases yet."
        
        purchases = self.purchase_history[customer_id]
        total_items = sum(p["quantity"] for p in purchases)
        
        return f"You've purchased {total_items} items in {len(purchases)} transactions."
