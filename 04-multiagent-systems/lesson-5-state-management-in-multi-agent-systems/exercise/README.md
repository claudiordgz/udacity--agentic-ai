# Colombian Fruit Market - State Management Exercise

**Learning Goal**: Implement shared persistent state management for a multi-agent system.

## Project Structure

```
exercise/
├── main.py                              # Main entry point demonstrating state management
├── config.py                            # Model configuration
├── data/
│   └── market_state.py                  # Shared state storage (inventory + purchase_history)
└── agents/
    ├── orchestrator/
    │   └── orchestrator.py              # MarketOrchestrator - coordinates agents
    ├── sales/
    │   └── sales_agent.py               # SalesAgent - writes to purchase_history
    └── recommendation/
        └── recommendation_agent.py      # RecommendationAgent - reads from purchase_history
```

## Key Concepts

### Shared Persistent State

The `market_state` dictionary stores two key pieces of information:
1. **Inventory**: Tracks available fruits and quantities
2. **Purchase History**: Stores all customer purchases

### Agent Responsibilities

**MarketOrchestrator**:
- Coordinates interactions between SalesAgent and RecommendationAgent
- Provides a unified interface for customer requests
- Manages shared state references

**SalesAgent**:
- Processes customer purchases
- Updates inventory
- **Writes to purchase_history** (shared state)

**RecommendationAgent**:
- Provides personalized recommendations
- **Reads from purchase_history** (shared state)
- Has no direct knowledge of sales transactions

### State Management Flow

```
Customer Purchase
    ↓
SalesAgent.process_purchase()
    ↓
Updates purchase_history in shared state
    ↓
RecommendationAgent.generate_recommendation()
    ↓
Reads from purchase_history to provide recommendations
```

## How It Works

1. **Shared State**: Both agents receive references to the same `purchase_history` dictionary
2. **Write by SalesAgent**: When a customer makes a purchase, SalesAgent records it in `purchase_history`
3. **Read by RecommendationAgent**: When a customer asks for recommendations, RecommendationAgent reads their purchase history
4. **Decoupled**: The agents don't need to communicate directly - they share state instead

## Running the System

```bash
python main.py
```

The demo will:
- Show initial state (inventory and empty purchase history)
- Demonstrate SalesAgent writing to shared state
- Show how RecommendationAgent reads from that state
- Provide different recommendations for different customers based on their history
- Display final state showing all purchases

## Key Insight

The power of persistent state management is that:
- Agents can be **decoupled** - they don't need to know about each other
- State persists across interactions - information survives agent boundaries
- One agent's actions can influence another agent's decisions without direct communication

