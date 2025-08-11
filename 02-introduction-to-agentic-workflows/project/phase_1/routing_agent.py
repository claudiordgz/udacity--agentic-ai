import os
from workflow_agents.base_agents import RoutingAgent, KnowledgeAugmentedPromptAgent

openai_api_key = os.getenv("OPENAI_API_KEY")
base_url = "https://openai.vocareum.com/v1"

# Define three knowledge-augmented agents
persona = "You are a college professor"

knowledge = "You know everything about Texas"
texas_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona, knowledge, base_url=base_url)

knowledge = "You know everything about Europe"
europe_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona, knowledge, base_url=base_url)

persona = "You are a college math professor"
knowledge = (
    "You know everything about math, you take prompts with numbers, extract math formulas, "
    "and show the answer without explanation"
)
math_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona, knowledge, base_url=base_url)

# Define routing table: name, description, and callable func
agents = [
    {
        "name": "Texas Agent",
        "description": "Answers questions about Texas. Does not answer about Europe or mathematics.",
        "func": lambda query: texas_agent.respond(query),
    },
    {
        "name": "Europe Agent",
        "description": "Answers questions about Europe. Does not answer about Texas or mathematics.",
        "func": lambda query: europe_agent.respond(query),
    },
    {
        "name": "Math Agent",
        "description": "When a prompt contains numbers, respond with a math formula and result.",
        "func": lambda query: math_agent.respond(query),
    },
]

# Instantiate the router with routes
routing_agent = RoutingAgent(openai_api_key, agents=agents, base_url=base_url)

# Print the RoutingAgent responses to the following prompts:
#           - "Tell me about the history of Rome, Texas"
#           - "Tell me about the history of Rome, Italy"
#           - "One story takes 2 days, and there are 20 stories" 
print("--------------------------------")
print("Prompts used:")
print(" - Tell me about the history of Rome, Texas")
print(" - Tell me about the history of Rome, Italy")
print(" - One story takes 2 days, and there are 20 stories")
print("--------------------------------")
print("Routing Agent Responses:")
print("--------------------------------")
print(routing_agent.route("Tell me about the history of Rome, Texas"))
print("--------------------------------")
print(routing_agent.route("Tell me about the history of Rome, Italy"))
print("--------------------------------")
print(routing_agent.route("One story takes 2 days, and there are 20 stories"))
print("--------------------------------")
