# UdaPlay: AI Game Research Agent

UdaPlay is an AI assistant for game research that answers questions using a local vector database (RAG), falls back to web search when needed, keeps conversation history, and persists useful facts in long‑term memory.

## Getting Started

### Dependencies

Python 3.11+

Required packages (already pinned in the repo):
- chromadb, openai, tavily-python, python-dotenv, tiktoken, pdfplumber, sqlalchemy, pydantic

### Environment

Create a `.env` file at repo root:
```
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://openai.vocareum.com/v1
TAVILY_API_KEY=...
```

Optional for SQL tools and embeddings:
```
DATABASE_URL=sqlite:///./app.db
CHROMA_EMBED_MODEL=text-embedding-ada-002
```

### Setup
1) Create venv and install deps
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # or use pyproject/poetry if preferred
```

2) Ensure the notebooks can import `lib`:
- We work under `03-building-agents/project/`. Notebooks reference `lib/*` directly.

### Data Ingestion

The games corpus lives in `project/games/*.json`. Use the notebook `Udaplay_02_starter_project.ipynb` to:
- Initialize Chroma persistent client
- Load JSON corpus via `CorpusLoaderService.load_json_dir("games_market", "./games")`

### Run the Agent (Notebook)

Open `Udaplay_02_starter_project.ipynb` and run cells in order:
- Tools: `retrieve_game`, `evaluate_retrieval`, `game_web_search`
- Agent setup with `include_tool_docs` and strict validation
- Long‑term memory (`store_memory`, `search_memory`)
- Orchestrator demo (optional)
- Agent trace cells to inspect tools, args, and tokens

### Example Queries
- "When were Pokémon Gold and Silver released?"
- "Which was the first 3D platformer Mario game?"
- "Was Mortal Kombat X released for PlayStation 5?"

### Sessions and Memory
The agent remembers prior context within the same `session_id` using short‑term memory. Use a consistent `session_id` across turns:
```python
agent = Agent(model_name="gpt-4o-mini", tools=[...], instructions="...")

# First message
run1 = agent.invoke("Summarize Gran Turismo history", session_id="execs")

# Follow-up uses prior context automatically
run2 = agent.invoke("And what platform did it debut on?", session_id="execs")

# Reset a session if needed
agent.reset_session("execs")
```

## Testing

Use the evaluation utilities in `lib/evaluation.py` (or the demo code in the notebook) to:
- Measure black-box correctness
- Inspect single-step tool selection
- Analyze trajectory metrics (steps, tokens, cost estimate)

## Project Instructions (Deliverables)
- Implement and document the three tools (retrieve, evaluate, web search)
- Build the Agent with memory and run example queries
- Add curated facts to long‑term memory and verify retrieval
- Provide an Agent trace for at least three queries (tools + tokens)

## Built With
- ChromaDB (vector storage)
- OpenAI (chat + embeddings)
- Tavily (web search)
- Pydantic, dotenv, tiktoken

## License
[License](../LICENSE.md)
