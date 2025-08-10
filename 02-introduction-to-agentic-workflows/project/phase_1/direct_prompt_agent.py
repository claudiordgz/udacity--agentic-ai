from workflow_agents.base_agents import DirectPromptAgent
import os

openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the Capital of France?"

direct_agent = DirectPromptAgent(openai_api_key, base_url="https://openai.vocareum.com/v1")
response = direct_agent.respond(prompt)



print("--------------------------------")
print(f"Direct Prompt Agent Response: {response}")
print("--------------------------------")
print(f"Used own knowledge? {'Yes' if 'Paris' in response else 'No'}")
print("--------------------------------")
