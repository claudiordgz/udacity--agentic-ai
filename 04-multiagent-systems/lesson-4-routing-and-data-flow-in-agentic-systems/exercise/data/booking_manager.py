"""Data layer for booking management."""

import random


class BookingManager:
    """Manages bookings, availability, and customer profiles."""
    
    def __init__(self):
        self.bookings = {}
        self.locations = ["Beijing Branch (北京分行)", "Shanghai Branch (上海分行)", "Guangzhou Branch (广州分行)"]
        self.special_services = {
            "VIP": ["deposit", "international_transfer"],
            "Regular": [], 
            "Student": ["loan"],
            "Senior": ["bill_payment"]
        }
        # Limited availability for services
        self.availability = {
            "deposit": 2,
            "postal": 2,
            "loan": 2,
            "bill_payment": 2,
            "international_transfer": 2,
            "general_inquiry": float('inf')  # unlimited
        }
        # Track proper routing decisions
        self.routing_accuracy = {
            "correct_service_type": 0,
            "total_requests": 0,
            "special_handling_applied": 0,
            "urgent_requests_handled": 0  # Track urgent requests
        }
        # Customer profiles
        self.customer_profiles = {
            "Wang Xiaoming (王小明)": {"type": "VIP", "language": "Mandarin"},
            "Li Jiayi (李佳怡)": {"type": "Regular", "language": "Mandarin"},
            "Chen Student (陈学生)": {"type": "Student", "language": "Mandarin"},
            "Zhang Senior (张老先生)": {"type": "Senior", "language": "Cantonese"},
            "Ms. Qian (钱女士)": {"type": "VIP", "language": "English"},
            "Mr. Zhao (赵先生)": {"type": "Regular", "language": "Mandarin"}
        }
    
    def check_availability(self, service_type):
        """Check if a service type is available."""
        return self.availability[service_type] > 0
    
    def add_booking(self, service_type, customer_name, is_urgent=False, expected_service=None):
        """Add a booking for a service.
        
        Args:
            service_type: Type of service requested
            customer_name: Name of the customer
            is_urgent: Whether this is an urgent request
            expected_service: Expected service type for validation
            
        Returns:
            Confirmation message
        """
        if service_type not in self.bookings:
            self.bookings[service_type] = []
            
        if not self.check_availability(service_type):
            return f"Sorry, no availability for {service_type} service. (很抱歉，{service_type}服务目前没有可用名额。)"
        
        # Track proper service identification
        if expected_service and service_type == expected_service:
            self.routing_accuracy["correct_service_type"] += 1
        
        # Track urgent requests
        if is_urgent:
            self.routing_accuracy["urgent_requests_handled"] += 1
        
        # Update state
        self.bookings[service_type].append(customer_name)
        self.availability[service_type] -= 1
        
        # Get customer type
        customer_type = "Regular"
        for cust, profile in self.customer_profiles.items():
            if customer_name in cust:
                customer_type = profile["type"]
                break
                
        # Check if special handling is applied for eligible customers
        special_handling = ""
        if customer_type in self.special_services and service_type in self.special_services[customer_type]:
            special_handling = f" with {customer_type} priority service (享受{customer_type}优先服务)"
            self.routing_accuracy["special_handling_applied"] += 1
        
        # Add urgent handling indicator
        urgent_indicator = ""
        if is_urgent:
            urgent_indicator = " [URGENT] 🚨"
        
        # Random branch assignment
        branch = random.choice(self.locations)
        
        # Return bilingual response
        return f"{customer_name}'s {service_type} service booking is confirmed at {branch}{special_handling}{urgent_indicator}. ({customer_name}的{service_type}服务预约已确认，地点在{branch}{special_handling}{urgent_indicator}。)"
    
    def get_state(self):
        """Get current system state for reporting."""
        accuracy = 0
        if self.routing_accuracy["total_requests"] > 0:
            accuracy = (self.routing_accuracy["correct_service_type"] / 
                       self.routing_accuracy["total_requests"]) * 100
        
        return {
            "availability": self.availability.copy(),
            "bookings": self.bookings.copy(),
            "accuracy": accuracy,
            "urgent_handled": self.routing_accuracy["urgent_requests_handled"]
        }

# Global instance
booking_manager = BookingManager()

