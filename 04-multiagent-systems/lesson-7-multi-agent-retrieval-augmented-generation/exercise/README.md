# Lesson 7 – Fraud Detection With Multi-Agent RAG

This exercise implements a multi-agent retrieval-augmented generation (RAG) workflow
for analysing insurance transactions and flagging potential fraud. The solution
follows the same structure as the earlier lessons: agents live in dedicated
packages, the data layer is separate, and the OpenAI server model configuration is
centralised in `config.py`.

## Project Structure

- `config.py` – shared LLM configuration for all agents.
- `data/fraud_data.py` – deterministic seed data, fraud patterns, and helper utilities.
- `core/` – shared domain models (`Claim`, `PatientRecord`, etc.), access control, and the in-memory database/seed generator.
- `tools/` – reusable smolagents tools (claim search, complaint handling, knowledge base lookup) decoupled from the original demo.
- `agents/` – individual agent implementations built on the shared tools:
  - `transaction_data/` – retrieves transaction records.
  - `customer_data/` – enriches transactions with customer metadata.
  - `fraud_pattern/` – pattern analysis combining heuristics and lightweight similarity.
  - `claim_processing/`, `customer_service/`, `medical_review/`, `complaint_resolution/` – copies of the demo agents, now depending on local utilities instead of `demo.py`.
  - `retrieval_coordinator/` – orchestrates data collection across agents.
  - `synthesis/` – produces the final fraud risk report.
  - `fraud_detection/` – exposes a `ToolCallingAgent` entry point for the workflow.
- `demos.py` – LLM-powered demonstration scenarios that exercise the agents through `ToolCallingAgent.run`.
- `evaluator.py` – integration tests that call the demos and assert expected outcomes.
- `workflow.py` – helper function `demonstrate_fraud_detection()` that wires agents together.
- `main.py` – runnable script requested in the exercise brief.

## Running The Demo

```bash
python main.py
```

The script will:

1. Populate the shared database using the local `core.DataGenerator` utilities.
2. Seed deterministic records and fraud patterns for reproducible results.
3. Execute the multi-agent workflow and print a fraud report for each transaction under review.

## Extending

- Add new patterns to `FRAUD_PATTERNS` and call `seed_demo_records()` to make them available.
- Adjust thresholds in `FraudPatternDetector` or `SynthesisAgent` to tune risk scoring.
- Integrate additional retrieval agents by extending `RetrievalCoordinator` with new data sources.


