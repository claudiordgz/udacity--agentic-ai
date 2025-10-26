"""
Evaluator for the Skate Park & Shop System.

Tests orchestration logic, agent routing, and business rules.
"""

from typing import Dict, Any, List, Tuple
from agents.orchestrator.orchestrator import OrchestratorAgent
from data.inventory import inventory
import copy


class Evaluator:
    """Evaluates the system's orchestration and business logic."""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.test_results: List[Tuple[str, bool, str]] = []
        self.initial_stock = None
    
    def setup(self):
        """Save initial inventory state."""
        self.initial_stock = copy.deepcopy(inventory.stock)
    
    def teardown(self):
        """Restore initial inventory state."""
        inventory.stock = copy.deepcopy(self.initial_stock)
    
    def test(self, name: str, test_func):
        """Run a single test and record the result."""
        try:
            result = test_func()
            self.test_results.append((name, result, "PASS" if result else "FAIL"))
            print(f"{'✓' if result else '✗'} {name}")
        except Exception as e:
            self.test_results.append((name, False, f"ERROR: {str(e)}"))
            print(f"✗ {name} - ERROR: {str(e)}")
    
    def test_stock_inquiry_existing_item(self) -> bool:
        """Test 1: Inquire about stock for an existing item."""
        request = {"action": "inquire", "item": "skateboard"}
        response = self.orchestrator.run(request)
        
        # Should contain stock information
        return "stock" in response.lower() and ("skateboard" in response.lower() or "5" in response)
    
    def test_stock_inquiry_nonexistent_item(self) -> bool:
        """Test 2: Inquire about stock for item not in inventory."""
        request = {"action": "inquire", "item": "nonexistent_item"}
        response = self.orchestrator.run(request)
        
        # Should handle missing item gracefully
        return "out of stock" in response.lower() or "0" in response
    
    def test_purchase_with_sufficient_stock(self) -> bool:
        """Test 3: Purchase item when sufficient stock available."""
        initial_stock = inventory.stock.get("helmet", 0)
        
        request = {"action": "purchase", "item": "helmet", "quantity": 2}
        response = self.orchestrator.run(request)
        
        # Should succeed
        success = "successful" in response.lower() or "sold" in response.lower()
        
        # Stock should be reduced
        new_stock = inventory.stock.get("helmet", 0)
        stock_reduced = (initial_stock - new_stock) == 2
        
        return success and stock_reduced
    
    def test_purchase_with_insufficient_stock(self) -> bool:
        """Test 4: Attempt to purchase more than available stock."""
        # Set low stock
        inventory.stock["wheels"] = 2
        
        request = {"action": "purchase", "item": "wheels", "quantity": 5}
        response = self.orchestrator.run(request)
        
        # Should fail with clear message
        has_error = "insufficient" in response.lower() or "not enough" in response.lower()
        has_stock_info = "2" in response or "only" in response.lower()
        
        # Stock should NOT be reduced
        stock_unchanged = inventory.stock["wheels"] == 2
        
        return has_error and has_stock_info and stock_unchanged
    
    def test_purchase_zero_quantity(self) -> bool:
        """Test 5: Attempt to purchase zero quantity."""
        initial_stock = inventory.stock.get("skateboard", 0)
        
        request = {"action": "purchase", "item": "skateboard", "quantity": 0}
        response = self.orchestrator.run(request)
        
        # Should handle gracefully
        stock_unchanged = inventory.stock["skateboard"] == initial_stock
        return stock_unchanged
    
    def test_multiple_purchases_affect_stock(self) -> bool:
        """Test 6: Multiple purchases should properly track stock."""
        inventory.stock["grip_tape"] = 10
        
        # First purchase
        request1 = {"action": "purchase", "item": "grip_tape", "quantity": 3}
        self.orchestrator.run(request1)
        
        # Second purchase
        request2 = {"action": "purchase", "item": "grip_tape", "quantity": 2}
        self.orchestrator.run(request2)
        
        # Should have 5 remaining
        expected_stock = 10 - 3 - 2
        return inventory.stock["grip_tape"] == expected_stock
    
    def test_inquiry_before_purchase(self) -> bool:
        """Test 7: Verify inquiry doesn't affect stock."""
        initial_skateboard = inventory.stock.get("skateboard", 0)
        
        # Inquiry should not change stock
        request = {"action": "inquire", "item": "skateboard"}
        self.orchestrator.run(request)
        
        # Stock should be unchanged
        return inventory.stock["skateboard"] == initial_skateboard
    
    def test_orchestrator_routes_correctly(self) -> bool:
        """Test 8: Orchestrator routes to correct agents."""
        # This is a structural test
        assert hasattr(self.orchestrator, 'inventory_agent'), "Missing inventory_agent"
        assert hasattr(self.orchestrator, 'sales_agent'), "Missing sales_agent"
        return True
    
    def run_all_tests(self):
        """Run the complete test suite."""
        print("\n" + "=" * 70)
        print("EVALUATOR - ORCHESTRATION SYSTEM TESTS")
        print("=" * 70 + "\n")
        
        self.setup()
        
        # Run all tests
        self.test("1. Stock Inquiry - Existing Item", self.test_stock_inquiry_existing_item)
        self.test("2. Stock Inquiry - Non-existent Item", self.test_stock_inquiry_nonexistent_item)
        self.test("3. Purchase - Sufficient Stock", self.test_purchase_with_sufficient_stock)
        self.test("4. Purchase - Insufficient Stock", self.test_purchase_with_insufficient_stock)
        self.test("5. Purchase - Zero Quantity", self.test_purchase_zero_quantity)
        self.test("6. Multiple Purchases Track Stock", self.test_multiple_purchases_affect_stock)
        self.test("7. Inquiry Doesn't Affect Stock", self.test_inquiry_before_purchase)
        self.test("8. Orchestrator Structure", self.test_orchestrator_routes_correctly)
        
        self.teardown()
        
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, result, _ in self.test_results if result)
        total = len(self.test_results)
        
        for name, result, status in self.test_results:
            print(f"{name}: {status}")
        
        print("\n" + "-" * 70)
        print(f"Total: {passed}/{total} tests passed")
        print("=" * 70 + "\n")
        
        return passed == total


def run_evaluation():
    """Entry point for running the evaluation."""
    evaluator = Evaluator()
    all_passed = evaluator.run_all_tests()
    return all_passed


if __name__ == "__main__":
    success = run_evaluation()
    exit(0 if success else 1)

