"""
Main entry point for the Chinese Bank Post Office routing system.

Demonstrates:
- Content-based routing (urgency detection)
- Priority-based routing (urgent requests handled first)
- Two-tiered routing system combining both approaches

Usage:
    python main.py              # Run demo
    python main.py --evaluate   # Run evaluator
"""

import sys
import time
from agents.orchestrator.orchestrator import ChineseBankPostOfficeAgent
from data.booking_manager import booking_manager


def print_state():
    """Prints the current state of the system."""
    print("\n" + "=" * 80)
    print("CURRENT SYSTEM STATE")
    print("=" * 80)
    
    # Service availability
    print("\nRemaining Service Availability:")
    for service, count in booking_manager.availability.items():
        print(f"  - {service}: {'∞' if count == float('inf') else count} slots")
    
    # Bookings made
    print("\nBookings Completed:")
    for service, customers in booking_manager.bookings.items():
        if customers:
            print(f"  - {service}: {', '.join(customers)}")
    
    # Performance metrics
    state = booking_manager.get_state()
    
    print("\nPerformance Metrics:")
    print(f"  - Request Routing Accuracy: {state['accuracy']:.1f}%")
    print(f"  - Special Customer Handling Applied: {booking_manager.routing_accuracy['special_handling_applied']} times")
    print(f"  - Urgent Requests Handled: {state['urgent_handled']} times")
    
    # Overall success assessment
    if (state['accuracy'] >= 80 and 
        booking_manager.routing_accuracy["special_handling_applied"] >= 2 and
        state['urgent_handled'] > 0):
        print("\n✅ SUCCESS: The system demonstrated proper routing, urgency handling, and special case handling!")
    else:
        print("\n⚠️ The system needs improvement.")
    print("=" * 80)


if __name__ == "__main__":
    # Check for --evaluate flag
    if len(sys.argv) > 1 and sys.argv[1] == "--evaluate":
        from evaluator import run_evaluation
        run_evaluation()
        sys.exit(0)
    
    bank_post_office_agent = ChineseBankPostOfficeAgent()
    
    print("🏦 Chinese Postal Bank Service Demo (中国邮政银行服务示例) 🏦\n")
    print("Demonstrating: Content-based routing + Priority-based routing\n")

    # Initial state
    print("INITIAL STATE:")
    for service, count in booking_manager.availability.items():
        print(f"  - {service}: {count} slots available")
    print("-" * 60)

    # Test cases with expected service mapping
    test_cases = [
        {
            "name": "Wang Xiaoming (王小明)",
            "request": "I need to deposit money into my account. (我需要存一些钱到我的账户。)",
            "expected_service": "deposit",
            "metadata": "VIP customer eligible for special handling"
        },
        {
            "name": "Li Jiayi (李佳怡)",
            "request": "I want to send a package to Shanghai. (我想邮寄一个包裹到上海。大街)", 
            "expected_service": "postal",
            "metadata": "Regular customer"
        },
        {
            "name": "Emergency Customer (紧急客户)",
            "request": "I urgently need to transfer money for a medical emergency! (我急需汇款处理医疗紧急情况！)",
            "expected_service": "international_transfer",
            "metadata": "URGENT REQUEST"
        },
        {
            "name": "Chen Student (陈学生)",
            "request": "How do I apply for a student loan? (我该如何申请学生贷款？)", 
            "expected_service": "loan",
            "metadata": "Student customer eligible for special handling"
        },
        {
            "name": "Zhang Senior (张老先生)",
            "request": "I need help paying my electricity bill. (我需要帮助支付我的电费。)", 
            "expected_service": "bill_payment",
            "metadata": "Senior customer eligible for special handling"
        },
        {
            "name": "Ms. Qian (钱女士)",
            "request": "I want to transfer money to my son in Canada. (我想给我在加拿大的儿子转账。)", 
            "expected_service": "international_transfer",
            "metadata": "VIP customer eligible for special handling"
        },
        {
            "name": "Mr. Zhao (赵先生)",
            "request": "What are the business hours for the Beijing branch? (北京分行的营业时间是什么时候？)", 
            "expected_service": "general_inquiry",
            "metadata": "Regular customer"
        }
    ]
    
    for case in test_cases:
        print(f"\nProcessing request from {case['name']}:")
        print(f"Request: \"{case['request']}\"")
        print(f"Customer info: {case['metadata']}")
        
        # Run the request
        response = bank_post_office_agent.handle_customer_request(
            case['name'], 
            case['request'], 
            case['expected_service']
        )
        
        # Display response
        print(f"Response: {response}")
        
        # Show mini-state change after each request
        print("\nService availability after this request:")
        for service, count in booking_manager.availability.items():
            if service == case['expected_service']:
                print(f"  - {service}: {'∞' if count == float('inf') else count} slots")
        print("-" * 60)
        
        # Small delay for readability
        time.sleep(0.5)
    
    # Print final state and success metrics
    print_state()

