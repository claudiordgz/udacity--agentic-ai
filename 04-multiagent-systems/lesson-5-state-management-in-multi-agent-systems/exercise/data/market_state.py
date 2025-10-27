"""Shared market state for the Colombian fruit market system."""

# Shared state: inventory and purchase history
market_state = {
    "inventory": {
        "mangos": 50,
        "papayas": 30,
        "passion fruit": 40,
        "lulo": 60,
        "granadilla": 25,
    },
    "purchase_history": {}  # Will store {customer_id: [list of purchases]}
}
