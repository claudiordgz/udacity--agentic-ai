"""
Evaluator for the Italian Pasta Factory Multi-Agent System with LLM testing.

Tests:
- Order processing workflow via LLM agents
- Inventory management via LLM agents
- Production queue management via LLM agents
- Custom recipe creation via LLM agents
- Priority handling
- State coordination across agents with LLM reasoning
"""

import sys
from data.factory_state import factory_state


class PastaFactoryEvaluator:
    """Evaluates the pasta factory multi-agent system with LLM agent testing."""
    
    def __init__(self):
        from agents.orchestrator.orchestrator import PastaFactoryOrchestrator
        self.orchestrator = PastaFactoryOrchestrator()
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def reset_factory_state(self):
        """Reset factory state to initial values."""
        factory_state.inventory = {
            "flour": 10.0,
            "water": 5.0,
            "eggs": 24,
            "semolina": 8.0
        }
        factory_state.production_queue = []
        factory_state.pasta_recipes = {
            "spaghetti": {"flour": 0.2, "water": 0.1},
            "fettuccine": {"flour": 0.25, "water": 0.1},
            "penne": {"flour": 0.2, "water": 0.1},
            "ravioli": {"flour": 0.3, "water": 0.1, "eggs": 2},
            "lasagna": {"flour": 0.3, "water": 0.15, "eggs": 3}
        }
        factory_state.custom_recipes = {}
        factory_state.order_counter = 0
    
    def run_test(self, test_name, customer_request, expected_keywords=None):
        """Run a test with LLM agent processing."""
        self.test_results["total_tests"] += 1
        
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print('='*80)
        print(f"Customer Request: {customer_request}")
        
        issues = []
        
        try:
            # Process the request through the LLM-powered orchestrator
            response = self.orchestrator.process_order(customer_request)
            
            print(f"Agent Response: {response[:200]}..." if len(response) > 200 else f"Agent Response: {response}")
            
            # Check if response contains expected information
            if expected_keywords:
                for keyword in expected_keywords:
                    if keyword.lower() not in response.lower():
                        issues.append(f"Response missing expected keyword: '{keyword}'")
            
            # Check if order was added to queue
            if len(factory_state.production_queue) == 0:
                issues.append("No orders added to production queue")
            
            # Check state was modified
            if factory_state.order_counter == 0:
                issues.append("Order counter not incremented")
            
            passed = len(issues) == 0
            
            if passed:
                self.test_results["passed"] += 1
                print(f"✅ PASSED")
            else:
                self.test_results["failed"] += 1
                print(f"❌ FAILED")
                for issue in issues:
                    print(f"   - {issue}")
            
        except Exception as e:
            self.test_results["failed"] += 1
            print(f"❌ FAILED with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            issues = [f"Exception: {str(e)}"]
            passed = False
        
        self.test_results["tests"].append({
            "name": test_name,
            "passed": passed,
            "issues": issues,
            "response_length": len(response) if 'response' in locals() else 0
        })
    
    def test_standard_order(self):
        """Test processing a standard pasta order via LLM agents."""
        self.run_test(
            test_name="Standard Order Processing",
            customer_request="I'd like to order 2kg of spaghetti please.",
            expected_keywords=["spaghetti", "sufficient"]
        )
    
    def test_conflict_detection(self):
        """Test conflict detection when ingredients are insufficient."""
        self.run_test(
            test_name="Conflict Detection - Insufficient Ingredients",
            customer_request="I need 100kg of lasagna immediately!",
            expected_keywords=["insufficient", "denied"]
        )
    
    def test_rush_order(self):
        """Test processing a rush order with priority via LLM agents."""
        self.run_test(
            test_name="Rush Order with Priority",
            customer_request="Rush order! We need 3kg of fettuccine for an event today!",
            expected_keywords=["rush", "fettuccine", "priority"]
        )
    
    def test_custom_recipe_request(self):
        """Test creating a custom recipe via LLM agents."""
        self.run_test(
            test_name="Custom Recipe Creation",
            customer_request="I need a custom pasta with extra semolina, no eggs please.",
            expected_keywords=["custom", "semolina"]
        )
    
    def test_inventory_check(self):
        """Test inventory checking via LLM agents."""
        self.run_test(
            test_name="Inventory Check",
            customer_request="Can you check what ingredients you have in stock?",
            expected_keywords=["inventory", "ingredients"]
        )
    
    def run_all_tests(self):
        """Run all test scenarios with LLM agents."""
        print("\n" + "="*80)
        print("STARTING PASTA FACTORY EVALUATION (LLM-Powered)")
        print("="*80)
        print("\n⚠️  Note: Tests will make LLM API calls and may take some time.")
        
        # Reset state before testing
        self.reset_factory_state()
        
        # Run tests
        self.test_standard_order()
        self.test_inventory_check()
        self.test_conflict_detection()  # Tests conflict detection and resolution
        self.test_rush_order()
        self.test_custom_recipe_request()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print evaluation summary."""
        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Show state after tests
        print(f"\nFinal State:")
        print(f"  - Production Queue: {len(factory_state.production_queue)} orders")
        print(f"  - Order Counter: {factory_state.order_counter}")
        print(f"  - Custom Recipes: {len(factory_state.custom_recipes)}")
        
        # Print failed tests details
        failed_tests = [t for t in self.test_results["tests"] if not t["passed"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['name']}")
                for issue in test.get('issues', []):
                    print(f"     * {issue}")
        
        print("\n" + "="*80)
        
        # Return status
        return failed == 0


def run_evaluation():
    """Main entry point for running the evaluation."""
    evaluator = PastaFactoryEvaluator()
    success = evaluator.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    run_evaluation()
