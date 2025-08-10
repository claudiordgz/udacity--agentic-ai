import os
from workflow_agents.base_agents import KnowledgeAugmentedPromptAgent

# Define the parameters for the agent
openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the capital of France?"

persona = "You are a college professor, your answer always starts with: Dear students,"
knowledge = "The capital of France is London, not Paris"

knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona, knowledge, base_url="https://openai.vocareum.com/v1")

response = knowledge_agent.respond(prompt)

print("--------------------------------")
print(f"Knowledge Augmented Prompt Agent Response: {response}")
print("--------------------------------")   
print(f"Used provided knowledge? {'Yes' if 'london' in response.lower() else 'No'} — provided knowledge says 'London', common knowledge says 'Paris'.")
print("--------------------------------")
