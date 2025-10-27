"""
Main entry point for the Colombian Fruit Market with Purchase Tracking.

Demonstrates:
- Shared persistent state management
- How one agent (SalesAgent) can write to state
- How another agent (RecommendationAgent) can read from state
- State persistence across agent interactions
"""

from data.market_state import market_state
from agents.orchestrator.orchestrator import MarketOrchestrator


def print_state():
    """Print the current state of the market."""
    print("\n" + "=" * 70)
    print("CURRENT MARKET STATE")
    print("=" * 70)
    print("\nInventory:")
    for item, quantity in market_state["inventory"].items():
        print(f"  - {item}: {quantity}")
    print("\nPurchase History:")
    for customer_id, purchases in market_state["purchase_history"].items():
        print(f"  Customer {customer_id}:")
        for purchase in purchases:
            print(f"    - {purchase['quantity']} of {purchase['item']}")


def demonstrate_state_management():
    """
    Demonstrate how two agents can share and access persistent state.
    """
    print("=" * 70)
    print("COLOMBIAN FRUIT MARKET - State Management Demo")
    print("=" * 70)
    
    # Create orchestrator that manages both LLM-powered agents
    orchestrator = MarketOrchestrator()
    
    print("\n--- Initial State ---")
    print_state()
    
    # Scenario 1: Customer 1 makes purchases (SalesAgent writes to state)
    print("\n" + "=" * 70)
    print("SCENARIO 1: Customer 1 Makes Purchases")
    print("=" * 70)
    
    print("\n1. Customer 1 buys 3 mangos")
    result1 = orchestrator.process_purchase("customer_1", "mangos", 3)
    print(f"   Result: {result1}")
    
    print("\n2. Customer 1 buys 2 papayas")
    result2 = orchestrator.process_purchase("customer_1", "papayas", 2)
    print(f"   Result: {result2}")
    
    print_state()
    
    # Scenario 2: RecommendationAgent reads from state (no direct knowledge of sales)
    print("\n" + "=" * 70)
    print("SCENARIO 2: RecommendationAgent Provides Personalized Recommendations")
    print("=" * 70)
    
    print("\n3. Getting recommendation for Customer 1")
    recommendation = orchestrator.get_recommendation("customer_1")
    print(f"   Result: {recommendation}")
    
    print("\n4. Getting purchase summary for Customer 1")
    summary = orchestrator.get_customer_summary("customer_1")
    print(f"   Result: {summary}")
    
    # Scenario 3: Customer 2 makes purchases
    print("\n" + "=" * 70)
    print("SCENARIO 3: Customer 2 Makes Purchases")
    print("=" * 70)
    
    print("\n5. Customer 2 buys 4 passion fruit")
    result3 = orchestrator.process_purchase("customer_2", "passion fruit", 4)
    print(f"   Result: {result3}")
    
    print_state()
    
    # Scenario 4: Different recommendations for different customers
    print("\n" + "=" * 70)
    print("SCENARIO 4: Personalized Recommendations for Different Customers")
    print("=" * 70)
    
    print("\n6. Getting recommendation for Customer 1")
    rec1 = orchestrator.get_recommendation("customer_1")
    print(f"   Result: {rec1}")
    
    print("\n7. Getting recommendation for Customer 2")
    rec2 = orchestrator.get_recommendation("customer_2")
    print(f"   Result: {rec2}")
    
    print("\n8. New customer gets a welcome recommendation")
    rec3 = orchestrator.get_recommendation("customer_3")
    print(f"   Result: {rec3}")
    
    # Final state
    print("\n" + "=" * 70)
    print("FINAL STATE")
    print("=" * 70)
    print_state()
    
    print("\n" + "=" * 70)
    print("KEY INSIGHT")
    print("=" * 70)
    print("""
The RecommendationAgent has no direct knowledge of the sales transactions.
Yet, it can provide intelligent, personalized recommendations by reading
from the shared purchase_history state that the SalesAgent writes to.

This demonstrates the power of persistent state management in multi-agent systems:
- One agent (SalesAgent) writes to shared state
- Another agent (RecommendationAgent) reads from that same state
- Both agents act independently but share context through persistent state
""")


if __name__ == "__main__":
    demonstrate_state_management()
