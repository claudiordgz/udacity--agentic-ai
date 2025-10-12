from typing import TypedDict, List, Optional, Union, TypeVar
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
    
class Agent:
    def __init__(self, 
                 model_name: str,
                 instructions: str, 
                 tools: List[Tool] = None,
                 temperature: float = 0.7):
        """
        Initialize an Agent instance
        
        Args:
            model_name: Name/identifier of the LLM model to use
            instructions: System instructions for the agent
            tools: Optional list of tools available to the agent
            temperature: Temperature parameter for LLM (default: 0.7)
        """
        self.instructions = instructions
        self.tools = tools if tools else []
        self.model_name = model_name
        self.temperature = temperature
        self.memory = ShortTermMemory()
                
        # Initialize state machine
        self.workflow = self._create_state_machine()

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

        return {"messages": messages, "session_id": state["session_id"]}

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
        
        return {
            "messages": state["messages"] + [ai_message],
            "current_tool_calls": tool_calls,
            "session_id": state["session_id"],
        }

    def _tool_step(self, state: AgentState) -> AgentState:
        """Step logic: Execute any pending tool calls"""
        tool_calls = state["current_tool_calls"] or []
        tool_messages = []
        
        for call in tool_calls:
            # Access tool call data correctly
            function_name = call.function.name
            function_args = json.loads(call.function.arguments)
            tool_call_id = call.id
            # Find the matching tool
            tool = next((t for t in self.tools if t.name == function_name), None)
            if tool:
                result = str(tool(**function_args))
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps(result), 
                        tool_call_id=tool_call_id, 
                        name=function_name, 
                    )
                )
        
        # Clear tool calls and add results to messages
        return {
            "messages": state["messages"] + tool_messages,
            "current_tool_calls": None,
            "session_id": state["session_id"],
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
