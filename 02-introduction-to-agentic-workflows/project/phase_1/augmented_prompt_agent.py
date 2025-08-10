import os
from workflow_agents.base_agents import AugmentedPromptAgent

openai_api_key = os.getenv("OPENAI_API_KEY")

prompt = "What is the capital of France?"
persona = "You are a college professor; your answers always start with: 'Dear students,'"

augmented_agent = AugmentedPromptAgent(openai_api_key, persona, base_url="https://openai.vocareum.com/v1")

response = augmented_agent.respond(prompt)

used_persona = isinstance(response, str) and response.lstrip().lower().startswith("dear students,")

print("--------------------------------")
print(f"Augmented Prompt Agent Response: {response}")
print("--------------------------------")
if used_persona:
    print("The agent likely used the knowledge of the college professor to answer the prompt.")
    print("The system prompt specifying the persona affected the agent's response by making the agent more formal and academic.")
else:
    print("The response does not start with 'Dear students,'.")
    print("The agent may not have applied the specified persona consistently.")
print("--------------------------------")