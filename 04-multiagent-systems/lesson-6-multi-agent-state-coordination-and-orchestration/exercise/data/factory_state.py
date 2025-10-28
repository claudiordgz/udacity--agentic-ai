"""Data layer for the Italian Pasta Factory with state management."""

from typing import Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class PastaOrder:
    """Represents a pasta production order."""
    order_id: str
    pasta_shape: str
    quantity: float  # in kg
    status: str = "pending"  # pending, queued, completed, cancelled
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 1  # 1 = normal, 2 = rush, 3 = emergency
    customer_notes: str = ""


@dataclass
class FactoryState:
    """Shared factory state for the pasta production system."""
    
    inventory: Dict[str, float] = field(default_factory=lambda: {
        "flour": 10.0,  # kg
        "water": 5.0,   # liters
        "eggs": 24,     # count
        "semolina": 8.0 # kg
    })
    
    production_queue: List[PastaOrder] = field(default_factory=list)
    
    pasta_recipes: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "spaghetti": {"flour": 0.2, "water": 0.1},
        "fettuccine": {"flour": 0.25, "water": 0.1},
        "penne": {"flour": 0.2, "water": 0.1},
        "ravioli": {"flour": 0.3, "water": 0.1, "eggs": 2},
        "lasagna": {"flour": 0.3, "water": 0.15, "eggs": 3}
    })
    
    custom_recipes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    order_counter: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "inventory": self.inventory,
            "production_queue": [asdict(order) for order in self.production_queue],
            "pasta_recipes": self.pasta_recipes,
            "custom_recipes": self.custom_recipes,
            "order_counter": self.order_counter
        }


# Initialize the shared factory state
factory_state = FactoryState()

