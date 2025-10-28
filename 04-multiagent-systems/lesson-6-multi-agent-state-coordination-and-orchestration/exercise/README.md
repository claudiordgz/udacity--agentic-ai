# Italian Pasta Factory - Multi-Agent State Coordination

**Learning Goal**: Implement multi-agent state coordination with advanced orchestration patterns.

## Project Structure

```
exercise/
├── main.py                              # Main entry point with demo
├── config.py                            # Model configuration
├── data/
│   └── factory_state.py                 # Shared state storage (inventory, recipes, queue)
└── agents/
    ├── orchestrator/
    │   └── orchestrator.py              # PastaFactoryOrchestrator - coordinates agents
    ├── order_processor/
    │   ├── tools.py                     # Order processing tools
    │   └── order_processor_agent.py     # Parses orders, generates IDs
    ├── inventory_manager/
    │   ├── tools.py                     # Inventory management tools
    │   └── inventory_manager_agent.py   # Tracks ingredients
    ├── production_manager/
    │   ├── tools.py                     # Production management tools
    │   └── production_manager_agent.py  # Manages production queue
    └── custom_pasta_designer/
        ├── tools.py                     # Recipe design tools
        └── custom_pasta_designer_agent.py  # Creates custom recipes
```

## Key Concepts

### Multi-Agent State Coordination

The `factory_state` dictionary stores:
1. **Inventory**: Tracks available ingredients (flour, water, eggs, semolina)
2. **Production Queue**: Stores pending pasta orders
3. **Recipes**: Standard and custom pasta recipes
4. **Order Counter**: Tracks order numbering

### Agent Responsibilities

**PastaFactoryOrchestrator**:
- Coordinates all agent interactions
- Manages session and workflow state
- Implements retry logic and error handling

**OrderProcessorAgent**:
- Parses customer requests
- Generates unique order IDs
- Verifies pasta shapes exist

**InventoryManagerAgent**:
- Tracks ingredient availability
- Checks recipe requirements
- Monitors inventory levels

**ProductionManagerAgent**:
- Manages production queue
- Handles order prioritization (normal, rush, emergency)
- Calculates delivery estimates

**CustomPastaDesignerAgent**:
- Creates custom pasta recipes
- Validates ingredient availability
- Stores new recipes in state

### State Management Flow with Conflict Detection

```
Customer Request
    ↓
Orchestrator receives request
    ↓
OrderProcessor parses order & generates ID
    ↓
[STATE COORDINATION]
InventoryManager checks if ingredients are SUFFICIENT via check_ingredients tool
    ↓
[CONFLICT DETECTION]
Is order feasible? 
    ↓
    ├─ NO (INSUFFICIENT) → [CONFLICT RESOLUTION] → Deny order with explanation
    ↓
    └─ YES (SUFFICIENT) → ProductionManager adds to queue with priority
                           ↓
                      All updates written to shared factory_state
```

## Advanced Features

- **State Coordination**: Orchestrator coordinates with specialist agents to check shared state
- **Conflict Detection**: System detects when ingredients are insufficient for an order
- **Conflict Resolution**: Predefined rule denies orders that cannot be fulfilled
- **Priority Handling**: Rush and emergency orders processed first
- **Custom Recipes**: Dynamic recipe creation
- **Error Handling**: Retry logic with exponential backoff
- **Production Scheduling**: Capacity planning and delivery estimation

## Running the System

```bash
python main.py
```

The demo will:
- Process standard pasta orders
- Handle rush orders with priority
- Create custom pasta recipes
- Show state updates across all agents

