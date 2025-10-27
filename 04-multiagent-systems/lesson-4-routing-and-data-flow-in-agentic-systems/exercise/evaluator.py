"""
Evaluator for the Chinese Bank Post Office routing system.

Tests:
- Content-based routing (urgency detection)
- Priority-based routing (urgent request handling)
- Service classification accuracy
- Special customer handling
- Booking management
"""

from agents.orchestrator.orchestrator import ChineseBankPostOfficeAgent
from data.booking_manager import booking_manager
import sys


class RoutingEvaluator:
    """Evaluates the routing system with various test scenarios."""
    
    def __init__(self):
        self.orchestrator = ChineseBankPostOfficeAgent()
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def reset_booking_manager(self):
        """Reset booking manager to initial state."""
        booking_manager.availability = {
            "deposit": 2,
            "postal": 2,
            "loan": 2,
            "bill_payment": 2,
            "international_transfer": 2,
            "general_inquiry": float('inf')
        }
        booking_manager.bookings = {}
        booking_manager.routing_accuracy = {
            "correct_service_type": 0,
            "total_requests": 0,
            "special_handling_applied": 0,
            "urgent_requests_handled": 0
        }
    
    def run_test(self, test_name, request, customer_name, expected_service, expected_urgent=False):
        """Run a single test case."""
        self.test_results["total_tests"] += 1
        
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print(f"Customer: {customer_name}")
        print(f"Request: {request}")
        print(f"Expected Service: {expected_service}")
        print(f"Expected Urgent: {expected_urgent}")
        print('='*80)
        
        # Check initial availability
        initial_availability = booking_manager.availability.get(expected_service, 0)
        
        # Process request
        response = self.orchestrator.handle_customer_request(
            customer_name=customer_name,
            request=request,
            expected_service=expected_service
        )
        
        # Verify results
        passed = True
        issues = []
        
        # Check urgency detection
        is_urgent_detected = "[URGENT]" in response or "🚨" in response
        if expected_urgent != is_urgent_detected:
            passed = False
            issues.append(f"Urgency mismatch: expected={expected_urgent}, got={is_urgent_detected}")
        
        # Check service classification
        if expected_service not in response.lower() and expected_service != "general_inquiry":
            passed = False
            issues.append(f"Service type not found in response")
        
        # Check booking was created
        bookings_for_service = booking_manager.bookings.get(expected_service, [])
        if expected_service != "general_inquiry":
            customer_found = any(customer_name in booking for booking in bookings_for_service)
            if not customer_found:
                passed = False
                issues.append(f"Customer booking not found for service {expected_service}")
        
        # Check availability decreased
        if expected_service != "general_inquiry":
            final_availability = booking_manager.availability.get(expected_service, float('inf'))
            if initial_availability != float('inf') and final_availability >= initial_availability:
                passed = False
                issues.append(f"Availability did not decrease")
        
        # Record results
        self.test_results["tests"].append({
            "name": test_name,
            "passed": passed,
            "issues": issues,
            "response": response
        })
        
        if passed:
            self.test_results["passed"] += 1
            print(f"✅ PASSED")
        else:
            self.test_results["failed"] += 1
            print(f"❌ FAILED")
            for issue in issues:
                print(f"   - {issue}")
        
        print(f"Response: {response[:100]}...")
    
    def run_all_tests(self):
        """Run all test scenarios."""
        print("\n" + "="*80)
        print("STARTING ROUTING SYSTEM EVALUATION")
        print("="*80)
        
        # Reset state
        self.reset_booking_manager()
        
        # Test 1: Regular deposit request
        self.run_test(
            test_name="Regular Deposit Request",
            request="I need to deposit money into my account.",
            customer_name="Test Customer 1",
            expected_service="deposit",
            expected_urgent=False
        )
        
        # Test 2: Urgent international transfer
        self.run_test(
            test_name="Urgent Medical Transfer",
            request="I urgently need to transfer money for a medical emergency!",
            customer_name="Emergency Test Customer",
            expected_service="international_transfer",
            expected_urgent=True
        )
        
        # Test 3: Postal service
        self.run_test(
            test_name="Postal Service Request",
            request="I want to send a package to Shanghai.",
            customer_name="Test Customer 3",
            expected_service="postal",
            expected_urgent=False
        )
        
        # Test 4: Loan inquiry
        self.run_test(
            test_name="Loan Inquiry",
            request="How do I apply for a student loan?",
            customer_name="Student Test Customer",
            expected_service="loan",
            expected_urgent=False
        )
        
        # Test 5: Bill payment
        self.run_test(
            test_name="Bill Payment",
            request="I need help paying my electricity bill.",
            customer_name="Test Customer 5",
            expected_service="bill_payment",
            expected_urgent=False
        )
        
        # Test 6: General inquiry
        self.run_test(
            test_name="General Inquiry",
            request="What are the business hours for the Beijing branch?",
            customer_name="Test Customer 6",
            expected_service="general_inquiry",
            expected_urgent=False
        )
        
        # Test 7: Non-urgent transfer
        self.run_test(
            test_name="Non-Urgent Transfer",
            request="I want to transfer money to my son in Canada next week.",
            customer_name="Test Customer 7",
            expected_service="international_transfer",
            expected_urgent=False
        )
        
        # Test 8: Another urgent request
        self.run_test(
            test_name="Urgent Bill Payment",
            request="I urgently need to pay my bill immediately before it gets disconnected!",
            customer_name="Urgent Test Customer",
            expected_service="bill_payment",
            expected_urgent=True
        )
        
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
        
        # Print routing accuracy from booking manager
        routing_stats = booking_manager.routing_accuracy
        if routing_stats["total_requests"] > 0:
            accuracy = (routing_stats["correct_service_type"] / routing_stats["total_requests"]) * 100
            print(f"\nRouting Accuracy: {accuracy:.1f}%")
        
        # Print failed tests details
        failed_tests = [t for t in self.test_results["tests"] if not t["passed"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['name']}")
                for issue in test['issues']:
                    print(f"     * {issue}")
        
        print("\n" + "="*80)
        
        # Return status
        return failed == 0


def run_evaluation():
    """Main entry point for running the evaluation."""
    evaluator = RoutingEvaluator()
    success = evaluator.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    run_evaluation()
