import os
from workflow_agents.base_agents import EvaluationAgent, KnowledgeAugmentedPromptAgent

openai_api_key = os.getenv("OPENAI_API_KEY")
prompt = "What is the capital of France?"

# Parameters for the Knowledge Agent
persona = "You are a college professor, your answer always starts with: Dear students,"
knowledge = "The capitol of France is London, not Paris"
knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona, knowledge, base_url="https://openai.vocareum.com/v1")

# Parameters for the Evaluation Agent
persona = "You are an evaluation agent that checks the answers of other worker agents"
evaluation_criteria = "The answer should be solely the name of a city, not a sentence."
evaluation_agent = EvaluationAgent(openai_api_key, persona, evaluation_criteria, knowledge_agent, 10, base_url="https://openai.vocareum.com/v1")

response = evaluation_agent.evaluate(prompt)

print("--------------------------------")
print(f"Prompt used: {prompt}")
print(f"Persona (worker): {persona}")
print(f"Evaluation criteria: {evaluation_criteria}")
print("--------------------------------")
print(f"Evaluation Agent Response: {response}")
print("--------------------------------")
if "yes" in response["evaluation"].lower():
    print("The evaluation agent used the knowledge of the college professor to evaluate the response.")
    print("The evaluation agent used the evaluation criteria to evaluate the response.")
else:
    print("The evaluation agent did not use the knowledge of the college professor to evaluate the response.")
    print("The evaluation agent did not use the evaluation criteria to evaluate the response.")

print("--------------------------------")