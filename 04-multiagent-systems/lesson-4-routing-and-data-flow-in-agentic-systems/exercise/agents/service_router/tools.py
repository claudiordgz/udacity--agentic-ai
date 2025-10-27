"""Tools and Agent for Service Routing."""

from typing import Dict, Any
from smolagents import tool, ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from data.booking_manager import booking_manager


@tool
def handle_deposit(customer_name: str, is_urgent: bool = False, expected_service: str = "deposit") -> str:
    """Handles deposit requests.

    Args:
        customer_name: The name of the customer.
        is_urgent: Whether this is an urgent request.
        expected_service: The expected service type for routing accuracy tracking.

    Returns:
        A message indicating the deposit process has been initiated.
    """
    return booking_manager.add_booking("deposit", customer_name, is_urgent, expected_service)


@tool
def handle_postal(customer_name: str, is_urgent: bool = False, expected_service: str = "postal") -> str:
    """Handles postal service requests.

    Args:
        customer_name: The name of the customer.
        is_urgent: Whether this is an urgent request.
        expected_service: The expected service type for routing accuracy tracking.

    Returns:
        A message indicating the package details have been collected.
    """
    return booking_manager.add_booking("postal", customer_name, is_urgent, expected_service)


@tool
def handle_loan(customer_name: str, is_urgent: bool = False, expected_service: str = "loan") -> str:
    """Handles loan application requests.

    Args:
        customer_name: The name of the customer.
        is_urgent: Whether this is an urgent request.
        expected_service: The expected service type for routing accuracy tracking.

    Returns:
        A message indicating the loan application process has started.
    """
    return booking_manager.add_booking("loan", customer_name, is_urgent, expected_service)


@tool
def handle_bill_payment(customer_name: str, is_urgent: bool = False, expected_service: str = "bill_payment") -> str:
    """Handles bill payment requests.

    Args:
        customer_name: The name of the customer.
        is_urgent: Whether this is an urgent request.
        expected_service: The expected service type for routing accuracy tracking.

    Returns:
        A message indicating the bill payment process has started.
    """
    return booking_manager.add_booking("bill_payment", customer_name, is_urgent, expected_service)


@tool
def handle_international_transfer(customer_name: str, is_urgent: bool = False, expected_service: str = "international_transfer") -> str:
    """Handles international transfer requests.

    Args:
        customer_name: The name of the customer.
        is_urgent: Whether this is an urgent request.
        expected_service: The expected service type for routing accuracy tracking.

    Returns:
        A message indicating the international transfer process has started.
    """
    return booking_manager.add_booking("international_transfer", customer_name, is_urgent, expected_service)


@tool
def handle_general_inquiry(customer_name: str, is_urgent: bool = False, expected_service: str = "general_inquiry") -> str:
    """Handles general inquiry requests.

    Args:
        customer_name: The name of the customer.
        is_urgent: Whether this is an urgent request.
        expected_service: The expected service type for routing accuracy tracking.

    Returns:
        A message indicating redirection to the general information desk.
    """
    if expected_service == "general_inquiry":
        booking_manager.routing_accuracy["correct_service_type"] += 1
    return f"{customer_name} has been redirected to the general information desk. (已将{customer_name}转接至一般咨询服务台。)"


class ServiceRouter(ToolCallingAgent):
    """Agent that routes customer requests to the appropriate service agent."""

    def __init__(self):
        super().__init__(
            tools=[
                handle_deposit,
                handle_postal,
                handle_loan,
                handle_bill_payment,
                handle_international_transfer,
                handle_general_inquiry,
            ],
            model=model,
            name="service_router",
            description="""You are a service router agent for a Chinese Postal Bank.
            Your job is to route the customer to the appropriate service handler based on the service type.
            
            IMPORTANT: You MUST ONLY use the appropriate handle_* tool. 
            DO NOT add additional explanations or messages."""
        )

