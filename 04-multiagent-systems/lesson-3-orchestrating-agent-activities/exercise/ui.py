"""UI component for the Skate Park & Shop System."""

from typing import Dict, Any, List
from agents.inventory.tools import check_stock, InventoryAgent

class UI:
    """User interface for browsing and selecting items."""
    
    def __init__(self):
        # Available items in the shop (hardcoded from inventory)
        self.available_items = ["skateboard", "helmet", "wheels", "grip_tape"]
        self.inventory_agent = InventoryAgent()
    
    def display_inventory(self) -> None:
        """Display current inventory to the user."""
        print("\n" + "=" * 60)
        print("SKATE PARK & SHOP - INVENTORY")
        print("=" * 60)
        
        for item in self.available_items:
            stock_info = check_stock(item)
            status = f"{stock_info['quantity']} in stock" if stock_info['in_stock'] else "OUT OF STOCK"
            print(f"  • {item.upper()}: {status}")
        
        print("=" * 60 + "\n")
    
    def select_item(self) -> Dict[str, Any]:
        """Interactive menu for user to select an item and action."""
        self.display_inventory()
        
        # Show available items
        print("Select an item:")
        for idx, item in enumerate(self.available_items, 1):
            print(f"  {idx}. {item.upper()}")
        
        try:
            choice = int(input("\nEnter item number: "))
            if 1 <= choice <= len(self.available_items):
                item = self.available_items[choice - 1]
                
                # Get action
                print("\nSelect action:")
                print("  1. Inquire about stock")
                print("  2. Purchase item")
                
                action_choice = int(input("\nEnter action number: "))
                
                if action_choice == 1:
                    return {"action": "inquire", "item": item}
                elif action_choice == 2:
                    quantity = int(input(f"Enter quantity to purchase: "))
                    return {"action": "purchase", "item": item, "quantity": quantity}
                else:
                    print("Invalid action choice")
                    return None
            else:
                print("Invalid item choice")
                return None
        except (ValueError, IndexError):
            print("Invalid input")
            return None
    
    def display_response(self, response: str) -> None:
        """Display the system's response to the user."""
        print("\n" + "-" * 60)
        print("SYSTEM RESPONSE:")
        print("-" * 60)
        print(response)
        print("-" * 60 + "\n")
    
    def run(self, orchestrator) -> None:
        """Run the interactive UI."""
        print("\n" + "=" * 60)
        print("WELCOME TO THE SKATE PARK & SHOP")
        print("=" * 60)
        
        while True:
            try:
                request = self.select_item()
                
                if request is None:
                    continue
                
                print(f"\nProcessing request: {request['action']} for {request['item']}...\n")
                
                # Send request to orchestrator
                response = orchestrator.run(request)
                
                # Display response
                self.display_response(response)
                
                # Ask if user wants to continue
                continue_choice = input("Do another action? (y/n): ").lower()
                if continue_choice != 'y':
                    break
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
        
        print("\nThank you for visiting the Skate Park & Shop!\n")

