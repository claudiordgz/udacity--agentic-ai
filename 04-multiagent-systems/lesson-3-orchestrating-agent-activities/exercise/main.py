"""
Main entry point for the Skate Park & Shop System Exercise.

Modes:
- UI mode: python main.py
- Automated tests: python main.py --test
- Evaluator: python main.py --evaluate
"""

from agents.orchestrator.orchestrator import OrchestratorAgent
from ui import UI
import sys

def test_system():
    """Test the orchestration system with various requests."""
    orchestrator = OrchestratorAgent()
    
    print("=" * 60)
    print("Skate Park & Shop System - Orchestration Test")
    print("=" * 60)
    print()
    
    # Test 1: Check stock inquiry
    print("TEST 1: Stock Inquiry")
    request1 = {
        "action": "inquire",
        "item": "skateboard"
    }
    print(f"  Request: {request1}")
    response1 = orchestrator.run(request1)
    print(f"  Response: {response1}")
    print()
    
    # Test 2: Purchase in stock item
    print("TEST 2: Purchase Item (In Stock)")
    request2 = {
        "action": "purchase",
        "item": "skateboard",
        "quantity": 2
    }
    print(f"  Request: {request2}")
    response2 = orchestrator.run(request2)
    print(f"  Response: {response2}")
    print()
    
    # Test 3: Check stock after purchase
    print("TEST 3: Stock Inquiry (After Purchase)")
    request3 = {
        "action": "inquire",
        "item": "skateboard"
    }
    print(f"  Request: {request3}")
    response3 = orchestrator.run(request3)
    print(f"  Response: {response3}")
    print()
    
    # Test 4: Purchase more than available
    print("TEST 4: Purchase Item (Out of Stock)")
    request4 = {
        "action": "purchase",
        "item": "skateboard",
        "quantity": 10
    }
    print(f"  Request: {request4}")
    response4 = orchestrator.run(request4)
    print(f"  Response: {response4}")
    print()
    
    # Test 5: Inquire about multiple items
    print("TEST 5: Check Multiple Items")
    for item in ["helmet", "wheels", "grip_tape"]:
        request = {"action": "inquire", "item": item}
        print(f"  Request: {request}")
        response = orchestrator.run(request)
        print(f"  Response: {response}")
    print()
    
    print("=" * 60)
    print("Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--evaluate":
        # Run evaluator (comprehensive test suite)
        from evaluator import run_evaluation
        run_evaluation()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run automated tests
        test_system()
    else:
        # Run interactive UI
        ui = UI()
        ui.run(orchestrator)

