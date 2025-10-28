"""
Main entry point for the Italian Pasta Factory Multi-Agent System.

Demonstrates:
- Stateful orchestration across multiple agents
- Context management and state persistence
- Production queue management
- Custom recipe creation
- Error handling and retry logic

Usage:
    python main.py              # Run demo
    python main.py --evaluate   # Run evaluator
"""

import sys
import json
from data.factory_state import factory_state
from agents.orchestrator.orchestrator import PastaFactoryOrchestrator


def print_state():
    """Print the current state of the factory."""
    print("\n" + "=" * 70)
    print("CURRENT FACTORY STATE")
    print("=" * 70)
    print(json.dumps(factory_state.to_dict(), indent=2))


def demonstrate_pasta_factory():
    """Demonstrate the multi-agent pasta factory system."""
    print("=" * 70)
    print("ITALIAN PASTA FACTORY - Multi-Agent State Coordination Demo")
    print("=" * 70)
    
    # Create orchestrator
    orchestrator = PastaFactoryOrchestrator()
    
    print("\n--- Initial Factory State ---")
    print_state()
    
    # Test Case 1: Standard order
    print("\n" + "=" * 70)
    print("TEST CASE 1: Standard Pasta Order")
    print("=" * 70)
    
    print("\nCustomer: I'd like to order 2kg of spaghetti please. When can I get it?")
    response = orchestrator.process_order("I'd like to order 2kg of spaghetti please. When can I get it?")
    print(f"\nFactory Response:\n{response}")
    
    print_state()
    
    # Test Case 2: Rush order
    print("\n" + "=" * 70)
    print("TEST CASE 2: Rush Order")
    print("=" * 70)
    
    print("\nCustomer: Rush order! We need 5kg of fettuccine for a catering event tomorrow!")
    response = orchestrator.process_order("Rush order! We need 5kg of fettuccine for a catering event tomorrow!")
    print(f"\nFactory Response:\n{response}")
    
    print_state()
    
    # Test Case 3: Custom pasta recipe
    print("\n" + "=" * 70)
    print("TEST CASE 3: Custom Pasta Recipe")
    print("=" * 70)
    
    print("\nCustomer: I need a custom pasta with extra semolina and no eggs. Can you make that?")
    response = orchestrator.create_custom_recipe("I need a custom pasta with extra semolina and no eggs. Can you make that?")
    print(f"\nFactory Response:\n{response}")
    
    print_state()
    
    # Test Case 4: Conflict Detection - Insufficient ingredients
    print("\n" + "=" * 70)
    print("TEST CASE 4: Conflict Detection & Resolution")
    print("=" * 70)
    
    print("\nCustomer: I need 100kg of lasagna immediately! We have a huge event!")
    response = orchestrator.process_order("I need 100kg of lasagna immediately! We have a huge event!")
    print(f"\nFactory Response:\n{response}")
    
    print_state()
    
    # Final state
    print("\n" + "=" * 70)
    print("FINAL STATE")
    print("=" * 70)
    print_state()
    
    print("\n" + "=" * 70)
    print("KEY INSIGHT")
    print("=" * 70)
    print("""
The system demonstrates advanced state coordination across multiple specialized agents:

1. **Order Processor**: Parses customer requests and generates order IDs
2. **Inventory Manager**: Tracks ingredient availability and checks for conflicts
3. **Production Manager**: Manages production queue with priority handling
4. **Custom Pasta Designer**: Creates custom recipes based on customer requirements

KEY CONCEPTS DEMONSTRATED:

⚡ STATE COORDINATION:
   - Orchestrator coordinates with specialist agents to check shared state
   - InventoryManager checks ingredients BEFORE proceeding with production

🔍 CONFLICT DETECTION:
   - System detects when ingredients are insufficient to fulfill an order
   - Conflict identified by checking ingredient availability vs. requirements

📋 CONFLICT RESOLUTION (Predefined Rule):
   - When conflict detected: Order is denied with clear explanation
   - When no conflict: Order proceeds to production queue
   - This prevents orders that cannot be fulfilled and maintains system integrity

All agents share the same factory_state, ensuring consistency across operations.
""")


if __name__ == "__main__":
    # Check for --evaluate flag
    if len(sys.argv) > 1 and sys.argv[1] == "--evaluate":
        from evaluator import run_evaluation
        run_evaluation()
    else:
        demonstrate_pasta_factory()

