"""Data layer for inventory management."""

class Inventory:
    """Manages inventory stock levels."""
    
    def __init__(self):
        self.stock = {
            "skateboard": 5,
            "helmet": 10,
            "wheels": 20,
            "grip_tape": 15
        }
    
    def check_stock(self, item: str) -> int:
        """Check the stock level of an item.
        
        Args:
            item: The item to check
            
        Returns:
            The quantity available (0 if not in stock)
        """
        return self.stock.get(item, 0)
    
    def sell_item(self, item: str, quantity: int) -> bool:
        """Sell an item and update inventory.
        
        Args:
            item: The item to sell
            quantity: The quantity to sell
            
        Returns:
            True if sale was successful, False otherwise
        """
        if self.stock.get(item, 0) >= quantity:
            self.stock[item] -= quantity
            return True
        return False
    
    def get_all_stock(self) -> dict:
        """Get all inventory levels.
        
        Returns:
            Dictionary of all items and their stock levels
        """
        return self.stock.copy()

# Global inventory instance
inventory = Inventory()

