import os
from dotenv import load_dotenv
from smolagents import ToolCallingAgent, OpenAIServerModel, tool
from typing import Dict, Any, List, TypedDict, Literal
import json
import random

load_dotenv()

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base="https://openai.vocareum.com/v1",
)

# Type definitions
class PenguinAction(TypedDict, total=False):
    action: Literal["request_food", "find_food"]
    method: Literal["fishing", "foraging"]

class ScientistDecision(TypedDict):
    give_food: int  # 0-5
    give_tool: bool

class PenguinHistory(TypedDict):
    recent_food: int
    has_tool: bool

# Global state for simplicity
DISTRIBUTION_HISTORY = {}
@tool
def check_history(penguin_name: str) -> PenguinHistory:
    """
    Check the recent resource distribution history for a specific penguin.
    
    Args:
        penguin_name: The unique name or identifier of the penguin 
                     whose resource distribution history will be 
                     retrieved and analyzed.
    
    Returns:
        PenguinHistory: A dictionary containing:
            - 'recent_food' (int): Total food received in the last 3 rounds
            - 'has_tool' (bool): Whether the penguin has possessed a tool 
                               in recent history
    """
    history = DISTRIBUTION_HISTORY.get(penguin_name, [])
    recent_food = sum(h["food"] for h in history[-3:]) if history else 0
    has_tool = any(h["has_tool"] for h in history) if history else False
    return {"recent_food": recent_food, "has_tool": has_tool}  # type: PenguinHistory

@tool
def record_distribution(penguin_name: str, food: int, has_tool: bool) -> str:
    """
    Record the distribution of resources to a specific penguin.
    
    Args:
        penguin_name: The unique name or identifier of the penguin 
                     receiving resources.
        food: The number of food units being given to the penguin.
              Must be an integer between 0 and 5.
        has_tool: A flag indicating whether a tool is being distributed.
                  True means a tool is given, False means no tool is given.
    
    Returns:
        str: A confirmation message describing the resource distribution.
    """
    if penguin_name not in DISTRIBUTION_HISTORY:
        DISTRIBUTION_HISTORY[penguin_name] = []
    DISTRIBUTION_HISTORY[penguin_name].append({"food": food, "has_tool": has_tool})
    return f"Recorded: {penguin_name} got {food} food and {'a' if has_tool else 'no'} tool"

@tool
def find_food(penguin_name: str, method: str) -> int:
  """
  Finds food using a specified method.
  
  Args:
      penguin_name: The name of the penguin searching for food.
      method: The method used to find food (fishing or foraging).
  
  Returns:
      The amount of food found as an integer.
  """
  if method == "fishing":
    food_found = random.randint(2, 7)  # More food when fishing
    print(f"{penguin_name} went fishing and found {food_found} food.")
    return food_found
  else:
    food_found = random.randint(0, 3)
    print(f"{penguin_name} foraged and found {food_found} food.")
    return food_found

# The tool is added by the student
# --- EXAMPLE TOOL (Student can change) ---


class ScientistAgent(ToolCallingAgent):
    def __init__(self, initial_food_supply: int = 20, refresh_interval: int = 5) -> None:
        super().__init__(
            tools=[check_history, record_distribution],
            model=model,
            name="scientist",
            description="A scientist responding to penguin actions"
        )
        self.initial_food_supply = initial_food_supply
        self.food_supply = initial_food_supply
        self.tool_available = True
        self.refresh_interval = refresh_interval
        self.turn_counter = 0

    def refresh_resources(self):
        """Periodically refresh the scientist's food supply."""
        self.food_supply = self.initial_food_supply
        self.tool_available = True
        print(f"\n🔄 Scientist Resources Refreshed!")
        print(f"Food Supply Reset to: {self.food_supply}")
        print(f"Tool Availability Reset to: {self.tool_available}")

    def respond_to_action(self, penguin: 'PenguinAgent', penguin_action: PenguinAction) -> None:
        """Respond to a penguin's action."""
        self.turn_counter += 1
        if self.turn_counter % self.refresh_interval == 0:
            self.refresh_resources()

        print(f"\n--- Turn {self.turn_counter}: Scientist Responds to {penguin.name} ---")
        print(f"Penguin Action: {penguin_action}")
        print(f"Penguin State:")
        print(f"  - Food: {penguin.food}")
        print(f"  - Has Tool: {penguin.has_tool}")

        history = check_history(penguin.name)
        print(f"Penguin History:")
        print(f"  - Recent Food: {history['recent_food']}")
        print(f"  - Has Had Tool: {history['has_tool']}")

        print(f"\nScientist Resources:")
        print(f"  - Food Supply: {self.food_supply}")
        print(f"  - Tool Available: {self.tool_available}")

        response = self.run(
            f"""Penguin {penguin.name} took action: {penguin_action}
            Penguin's current state:
            - Food: {penguin.food}
            - Has Tool: {penguin.has_tool}

            Recent History: {history['recent_food']} recent food, {'has' if history['has_tool'] else 'no'} tool.
            Available Scientist Resources: {self.food_supply} food, Tool: {self.tool_available}

            Respond with JSON: {{"give_food": <0-5>, "give_tool": <bool>}}"""
        )

        try:
            # Parse the scientist's decision
            if isinstance(response, dict):
                decision_data = response
            else:
                decision_data = json.loads(response.split("final_answer:")[-1].strip())
            
            # Type the decision
            decision: ScientistDecision = {
                "give_food": min(int(decision_data.get('give_food', 0)), self.food_supply),
                "give_tool": bool(decision_data.get('give_tool', False)) and self.tool_available
            }

            food = decision["give_food"]
            tool = decision["give_tool"]

            print(f"\nScientist's Decision:")
            print(f"  - Food to Give: {food}")
            print(f"  - Tool to Give: {tool}")

            if food > 0:
                self.food_supply -= food
                penguin.food += food
            if tool:
                penguin.has_tool = True
                self.tool_available = False

            record_distribution(penguin.name, food, tool)

            print(f"\nPost-Action State:")
            print(f"Scientist Resources:")
            print(f"  - Remaining Food Supply: {self.food_supply}")
            print(f"  - Tool Available: {self.tool_available}")
            print(f"Penguin {penguin.name}:")
            print(f"  - Food: {penguin.food}")
            print(f"  - Has Tool: {penguin.has_tool}")

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error processing scientist's response: {e}")

class PenguinAgent(ToolCallingAgent):
    def __init__(self, name: str) -> None:
        # Penguins don't use tools - they make decisions that are processed externally
        super().__init__(tools=[], model=model, name=name)
        self.name = name
        self.food = 0
        self.has_tool = False
        self.is_hungry = True  # Penguins start hungry

    def take_action(self) -> PenguinAction:
        """Penguin decides on an action each round."""
        history = check_history(self.name)

        # YOUR CODE HERE
        # ****************************************************
        # Determine if penguin should be hungry based on food level
        # Penguin needs at least 1 food to not be hungry
        self.is_hungry = self.food < 1
        
        if not self.is_hungry:
            print(f"{self.name} is not hungry (has {self.food} food).")
            return {"action": "request_food", "method": "foraging"}  # Just request food but not urgent
        
        prompt = f"""You are Penguin {self.name}. You are HUNGRY and need food.
        
        Your current state:
        - Food: {self.food} (you need at least 1 to not be hungry)
        - Has Tool: {self.has_tool}
        - Is Hungry: {self.is_hungry}
        
        Your recent history:
        - Recent Food Received: {history['recent_food']}
        - Has Had Tool: {history['has_tool']}
        
        Decide on an action:
        1. "request_food" - Request food from the scientist (may get 0-5 food, and possibly a tool)
        2. "find_food" - Search for food yourself using either:
           - "fishing" (finds 2-7 food, more reliable)
           - "foraging" (finds 0-3 food, less reliable)
        
        Respond with JSON: {{"action": "<request_food|find_food>", "method": "<fishing|foraging>"}}"""

        response = self.run(prompt)
        # ****************************************************

        try:
            # Parse JSON response
            if isinstance(response, dict):
                action_data = response
            else:
                action_data = json.loads(response.split("final_answer:")[-1].strip())
            
            # Validate and construct typed dict
            action: PenguinAction = {
                "action": action_data.get("action", "request_food"),
                "method": action_data.get("method", "foraging")
            }
            return action
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error processing {self.name}'s action: {e}")
            return {"action": "request_food"}  # type: ignore

def run_simulation():
    scientist = ScientistAgent(initial_food_supply=20, refresh_interval=5)
    penguins = [PenguinAgent(f"Penguin_{i}") for i in range(4)]

    print("\nStarting Simulation...")
    for round in range(3):
        print(f"\n{'='*50}")
        print(f"ROUND {round + 1}")
        print(f"{'='*50}")

        # Penguins take actions
        penguin_actions = {}
        for penguin in penguins:
            action = penguin.take_action()
            penguin_actions[penguin.name] = action
            print(f"{penguin.name} Action: {action}")

        # Process Penguin Actions
        for penguin in penguins:
          if penguin_actions[penguin.name].get("action") == "request_food":
            pass # handled by scientist
          elif penguin_actions[penguin.name].get("action"):
            if penguin_actions[penguin.name].get("action") == "find_food":
              food_found = find_food(penguin.name, penguin_actions[penguin.name].get("method","foraging")) #Use the finding tool
              penguin.food += food_found

        # Scientist responds to actions
        for penguin in penguins:
            scientist.respond_to_action(penguin, penguin_actions[penguin.name])

    print(f"\nFinal State:")
    print(f"Remaining: {scientist.food_supply} food, {'🔨' if scientist.tool_available else ''}")

    for penguin in penguins:
        history = check_history(penguin.name)
        print(f"{penguin.name} - Total Food: {penguin.food}, Has Tool: {history['has_tool']}")

if __name__ == "__main__":
    run_simulation()