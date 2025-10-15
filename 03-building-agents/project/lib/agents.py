from typing import TypedDict, List, Optional, Union, TypeVar, Dict
import json

from lib.state_machine import StateMachine, Step, EntryPoint, Termination, Run
from lib.llm import LLM
from lib.messages import AIMessage, UserMessage, SystemMessage, ToolMessage
from lib.tooling import Tool, ToolCall
from lib.memory import ShortTermMemory


# Define the state schema
class AgentState(TypedDict):
    user_query: str  # The current user query being processed
    instructions: str  # System instructions for the agent
    messages: List[dict]  # List of conversation messages
    current_tool_calls: Optional[List[ToolCall]]  # Current pending tool calls
    session_id: str  # Session identifier for memory management
    total_tokens: Optional[int]  # Tokens used by the most recent LLM call
    cumulative_tokens: Optional[int]  # Tokens used by all LLM calls in this run so far
    tool_iterations: int  # Number of tool executions in this run
    seen_tool_calls: List[str]  # Keys of executed tool calls (for dedupe)
    tool_call_cache: Dict[str, str]  # Cache of tool call key -> JSON result
    
class Agent:
    def __init__(self, 
                 model_name: str,
                 instructions: str, 
                 tools: List[Tool] = None,
                 temperature: float = 0.7,
                 include_tool_docs: bool = True,
                 strict_tool_validation: bool = True,
                 max_tool_iterations: int = 2,
                 dedupe_tool_calls: bool = True,
                 cache_tool_results: bool = True,
                 discourage_repeats_instructions: bool = True):
        """
        Initialize an Agent instance
        
        Args:
            model_name: Name/identifier of the LLM model to use
            instructions: System instructions for the agent
            tools: Optional list of tools available to the agent
            temperature: Temperature parameter for LLM (default: 0.7)
        """
        self.tools = tools if tools else []
        if strict_tool_validation and self.tools:
            self._validate_tools(self.tools)
        self.instructions = self._augment_instructions_with_tools(instructions, discourage_repeats_instructions) if include_tool_docs and self.tools else instructions
        self.model_name = model_name
        self.temperature = temperature
        self.memory = ShortTermMemory()
        self.max_tool_iterations = max_tool_iterations
        self.dedupe_tool_calls = dedupe_tool_calls
        self.cache_tool_results = cache_tool_results
                
        # Initialize state machine
        self.workflow = self._create_state_machine()

    def _augment_instructions_with_tools(self, base_instructions: str, discourage_repeats: bool) -> str:
        lines = []
        for t in self.tools:
            sig = str(getattr(t, "signature", ""))
            desc = getattr(t, "description", "") or ""
            lines.append(f"- {t.name}{sig}: {desc}")
        catalog = "\n".join(lines)
        suffix = ("\n\nTools you can use:\n" + catalog) if catalog else ""
        policy = ("\n\nPolicy:\n- Do not call the same tool with identical arguments more than once in a run. If results are insufficient, switch tools or ask a clarifying question.") if discourage_repeats else ""
        return (base_instructions + suffix + policy)

    def _validate_tools(self, tools: List[Tool]):
        """Validate that tools have docstrings (descriptions) and return type annotations.

        Raises:
            ValueError: if any tool is missing a docstring/description or a return type.
        """
        missing: List[str] = []
        for t in tools:
            # Description comes from the function docstring by default
            desc = getattr(t, "description", None)
            type_hints = getattr(t, "type_hints", {}) or {}
            has_return = "return" in type_hints

            if not desc:
                missing.append(f"Tool '{t.name}' is missing a docstring/description")
            if not has_return:
                missing.append(f"Tool '{t.name}' is missing a return type annotation")

        if missing:
            details = "\n - ".join([""] + missing)
            raise ValueError(
                "Invalid tool definitions detected. Please add docstrings and explicit return types." + details
            )

    def _prepare_messages_step(self, state: AgentState) -> AgentState:
        """Step logic: Prepare messages for LLM consumption"""
        prior_messages = state.get("messages", [])
        # Drop any prior system messages to avoid duplicating long tool catalogs
        prior_without_system = [
            m for m in prior_messages
            if getattr(m, "role", None) != "system"
        ]

        messages = [SystemMessage(content=state["instructions"])]
        messages.extend(prior_without_system)
        messages.append(UserMessage(content=state["user_query"]))

        return {
            "messages": messages,
            "session_id": state["session_id"],
            "tool_iterations": state.get("tool_iterations", 0) or 0,
            "seen_tool_calls": state.get("seen_tool_calls", []) or [],
            "tool_call_cache": state.get("tool_call_cache", {}) or {},
        }

    def _llm_step(self, state: AgentState) -> AgentState:
        """Step logic: Process the current state through the LLM"""

        # Initialize LLM
        llm = LLM(
            model=self.model_name,
            temperature=self.temperature,
            tools=self.tools
        )

        response = llm.invoke(state["messages"])
        tool_calls = response.tool_calls if response.tool_calls else None

        # Create AI message with content and tool calls
        ai_message = AIMessage(content=response.content, tool_calls=tool_calls)
        
        # Build updated state and carry over tool tracking fields across cycles
        updated: AgentState = {
            "messages": state["messages"] + [ai_message],
            "current_tool_calls": tool_calls,
            "session_id": state["session_id"],
            "tool_iterations": state.get("tool_iterations", 0) or 0,
            "seen_tool_calls": state.get("seen_tool_calls", []) or [],
            "tool_call_cache": state.get("tool_call_cache", {}) or {},
        }
        # Attach usage if available
        if getattr(llm, "last_usage", None):
            try:
                last_total = llm.last_usage.get("total_tokens")
                updated["total_tokens"] = last_total
                prev_cum = state.get("cumulative_tokens", 0) or 0
                if last_total is not None:
                    updated["cumulative_tokens"] = prev_cum + int(last_total)
            except Exception:
                pass
        return updated

    def _tool_step(self, state: AgentState) -> AgentState:
        """Step logic: Execute any pending tool calls"""
        tool_calls = state["current_tool_calls"] or []
        tool_messages = []
        iterations = state.get("tool_iterations", 0) or 0
        seen_keys = set(state.get("seen_tool_calls", []) or [])
        cache: Dict[str, str] = state.get("tool_call_cache", {}) or {}
        
        for call in tool_calls:
            # Access tool call data correctly
            function_name = call.function.name
            function_args = json.loads(call.function.arguments)
            tool_call_id = call.id
            # Canonicalize args to ensure dedupe works despite spacing/key-order differences
            canonical_args = json.dumps(function_args, sort_keys=True, separators=(",", ":"))
            key = f"{function_name}|{canonical_args}"

            # If over iteration budget, return a bounded response without executing
            if iterations >= self.max_tool_iterations:
                bounded = json.dumps({"status": "no_context", "error": "max tool iterations reached"})
                tool_messages.append(
                    ToolMessage(
                        content=bounded,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                )
                continue

            # Dedupe identical calls in a single run
            if self.dedupe_tool_calls and key in seen_keys:
                if self.cache_tool_results and key in cache:
                    cached_content = cache[key]
                else:
                    cached_content = json.dumps({"status": "no_context", "error": "duplicate tool call with identical arguments"})
                tool_messages.append(
                    ToolMessage(
                        content=cached_content,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                )
                continue
            # Find the matching tool
            tool = next((t for t in self.tools if t.name == function_name), None)
            if tool:
                # Preserve structured results so the model can reason on fields
                result = tool(**function_args)
                result_json = json.dumps(result)
                tool_messages.append(
                    ToolMessage(
                        content=result_json, 
                        tool_call_id=tool_call_id, 
                        name=function_name, 
                    )
                )
                seen_keys.add(key)
                if self.cache_tool_results:
                    cache[key] = result_json
                iterations += 1
        
        # Clear tool calls and add results to messages
        return {
            "messages": state["messages"] + tool_messages,
            "current_tool_calls": None,
            "session_id": state["session_id"],
            "tool_iterations": iterations,
            "seen_tool_calls": list(seen_keys),
            "tool_call_cache": cache,
        }

    def _create_state_machine(self) -> StateMachine[AgentState]:
        """Create the internal state machine for the agent"""
        machine = StateMachine[AgentState](AgentState)
        
        # Create steps
        entry = EntryPoint[AgentState]()
        message_prep = Step[AgentState]("message_prep", self._prepare_messages_step)
        llm_processor = Step[AgentState]("llm_processor", self._llm_step)
        tool_executor = Step[AgentState]("tool_executor", self._tool_step)
        termination = Termination[AgentState]()
        
        machine.add_steps([entry, message_prep, llm_processor, tool_executor, termination])
        
        # Add transitions
        machine.connect(entry, message_prep)
        machine.connect(message_prep, llm_processor)
        
        # Transition based on whether there are tool calls
        def check_tool_calls(state: AgentState) -> Union[Step[AgentState], str]:
            """Transition logic: Check if there are tool calls"""
            if state.get("current_tool_calls"):
                return tool_executor
            return termination
        
        machine.connect(llm_processor, [tool_executor, termination], check_tool_calls)
        machine.connect(tool_executor, llm_processor)  # Go back to llm after tool execution
        
        return machine

    def invoke(self, query: str, session_id: Optional[str] = None) -> Run:
        """
        Run the agent on a query
        
        Args:
            query: The user's query to process
            
        Returns:
            The final run object after processing
        """

        session_id = session_id or "default"
        # Ensure session exists
        self.memory.create_session(session_id)

        # Preload full prior messages for conversational continuity (entire session)
        previous_messages: List[dict] = []
        prior_runs: List[Run[AgentState]] = self.memory.get_all_objects(session_id)
        for run in prior_runs:
            final_state = run.get_final_state()
            if final_state and final_state.get("messages"):
                previous_messages.extend(final_state["messages"])  # append in chronological order

        initial_state: AgentState = {
            "user_query": query,
            "instructions": self.instructions,
            "messages": previous_messages,
            "current_tool_calls": None,
            "session_id": session_id,
            "tool_iterations": 0,
            "seen_tool_calls": [],
            "tool_call_cache": {},
        }

        run_object = self.workflow.run(initial_state)

        # Persist run in memory under this session
        self.memory.add(run_object, session_id)

        return run_object

    def get_session_runs(self, session_id: Optional[str] = None) -> List[Run]:
        """Return all Run objects for a session (default if None)."""
        return self.memory.get_all_objects(session_id)

    def reset_session(self, session_id: Optional[str] = None):
        """Reset memory for a specific session or all sessions."""
        self.memory.reset(session_id)
