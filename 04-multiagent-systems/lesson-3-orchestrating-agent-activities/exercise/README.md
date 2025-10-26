# Skate Park & Shop System Exercise

## Project Structure

```
exercise/
├── main.py                          # Main entry point (UI mode and tests)
├── ui.py                            # Interactive user interface
├── config.py                        # LLM configuration
├── data/                            # Data layer
│   └── inventory.py                 # Inventory data management
└── agents/                          # Agent implementations
    ├── inventory/
    │   ├── __init__.py
    │   └── tools.py                 # InventoryAgent + tools
    ├── sales/
    │   ├── __init__.py
    │   └── tools.py                 # SalesAgent + tools
    └── orchestrator/
        ├── __init__.py
        └── orchestrator.py          # OrchestratorAgent (routes to other agents)
```

## Instructions

1. **The system is now LLM-powered!**
   - Each agent (`InventoryAgent`, `SalesAgent`, `OrchestratorAgent`) uses LLM reasoning
   - Orchestrator uses LLM to intelligently route requests and use tools
   - LLM decides when to check stock and when to process sales

2. **How it works:**
   - Extract action, item, and quantity from request
   - LLM orchestrates: checks stock using `check_stock(item)` tool
   - LLM handles "inquire" vs "purchase" actions intelligently
   - LLM prevents sales when stock is insufficient

3. **Workflow Pattern**:
   ```
   Request → Check Stock → Conditional Branch:
                              ├─ "inquire" → Return stock info
                              └─ "purchase" → Check stock
                                                ├─ Relevance → Sell
                                                └─ Not in stock → Error
   ```

3. **Run the system:**
   - Interactive UI mode: `python main.py`
   - Automated tests: `python main.py --test`

The UI displays available items from the inventory and lets you:
- Browse current stock levels
- Inquire about specific items
- Purchase items (only if in stock)

## Key Concepts

- **Data Layer**: `data/inventory.py` handles all inventory operations
- **Agent Tools**: Each agent has tools that wrap data layer functions
- **Orchestration**: Coordinating sequential and conditional workflows
- **Error Handling**: Prevent sales when stock is insufficient

