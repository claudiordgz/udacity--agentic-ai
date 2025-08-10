"""Agentic workflow for the Email Router project (Phase 2).

This script wires together the agents implemented in Phase 1 to:
- Plan steps from a high-level workflow prompt
- Route each step to the most suitable role (PM/Program Manager/Dev Engineer)
- Validate each role's output via its EvaluationAgent
- Print the final structured result
"""
# agentic_workflow.py
from workflow_agents.base_agents import ActionPlanningAgent, KnowledgeAugmentedPromptAgent, EvaluationAgent, RoutingAgent
import os

openai_api_key = os.getenv("OPENAI_API_KEY")

# load the product spec
product_spec = open(os.path.join(os.path.dirname(__file__), "Product-Spec-Email-Router.txt"), "r").read()

# Instantiate all the agents

# Action Planning Agent
knowledge_action_planning = (
    "Stories are defined from a product spec by identifying a "
    "persona, an action, and a desired outcome for each story. "
    "Each story represents a specific functionality of the product "
    "described in the specification. \n"
    "Features are defined by grouping related user stories. \n"
    "Tasks are defined for each story and represent the engineering "
    "work required to develop the product. \n"
    "A development Plan for a product contains all these components"
)
# TODO: 4 - Instantiate an action_planning_agent using the 'knowledge_action_planning'
action_planning_agent = ActionPlanningAgent(openai_api_key, knowledge_action_planning, base_url="https://openai.vocareum.com/v1")

# Product Manager - Knowledge Augmented Prompt Agent
persona_product_manager = "You are a Product Manager, you are responsible for defining the user stories for a product."
knowledge_product_manager = (
    "Stories are defined by writing sentences with a persona, an action, and a desired outcome. "
    "The sentences always start with: As a "
    "Write several stories for the product spec below, where the personas are the different users of the product. "
) + product_spec
product_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona_product_manager, knowledge_product_manager, base_url="https://openai.vocareum.com/v1")

# Product Manager - Evaluation Agent
persona_product_manager_eval = "You are an evaluation agent that checks the answers of other worker agents."
evaluation_criteria_product_manager = "The answer should be user stories following this exact structure: " \
    "As a [type of user], I want [an action or feature] so that [benefit/value]."
product_manager_evaluation_agent = EvaluationAgent(openai_api_key, persona_product_manager_eval, evaluation_criteria_product_manager, product_manager_knowledge_agent, max_interactions=10, base_url="https://openai.vocareum.com/v1", enable_scoring=True)

# Program Manager - Knowledge Augmented Prompt Agent
persona_program_manager = "You are a Program Manager, you are responsible for defining the features for a product."
knowledge_program_manager = "Features of a product are defined by organizing similar user stories into cohesive groups."
program_manager_knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona_program_manager, knowledge_program_manager, base_url="https://openai.vocareum.com/v1")

# Program Manager - Evaluation Agent
persona_program_manager_eval = "You are an evaluation agent that checks the answers of other worker agents."

evaluation_criteria_program_manager = """
The answer should be product features that follow the following structure: 
- Feature Name: A clear, concise title that identifies the capability
- Description: A brief explanation of what the feature does and its purpose
- Key Functionality: The specific capabilities or actions the feature provides
- User Benefit: How this feature creates value for the user
"""
program_manager_evaluation_agent = EvaluationAgent(openai_api_key, persona_program_manager_eval, evaluation_criteria_program_manager, program_manager_knowledge_agent, max_interactions=10, base_url="https://openai.vocareum.com/v1", enable_scoring=True)

# Development Engineer - Knowledge Augmented Prompt Agent
persona_dev_engineer = "You are a Development Engineer, you are responsible for defining the development tasks for a product."
knowledge_dev_engineer = "Development tasks are defined by identifying what needs to be built to implement each user story."
development_engineer_knowledge_agent = KnowledgeAugmentedPromptAgent(openai_api_key, persona_dev_engineer, knowledge_dev_engineer, base_url="https://openai.vocareum.com/v1")

# Development Engineer - Evaluation Agent
persona_dev_engineer_eval = "You are an evaluation agent that checks the answers of other worker agents."
evaluation_criteria_dev_engineer = """
The answer should be tasks following this exact structure: 
- Task ID: A unique identifier for tracking purposes
- Task Title: Brief description of the specific development work
- Related User Story: Reference to the parent user story
- Description: Detailed explanation of the technical work required
- Acceptance Criteria: Specific requirements that must be met for completion
- Estimated Effort: Time or complexity estimation
- Dependencies: Any tasks that must be completed first
"""
development_engineer_evaluation_agent = EvaluationAgent(openai_api_key, persona_dev_engineer_eval, evaluation_criteria_dev_engineer, development_engineer_knowledge_agent, max_interactions=10, base_url="https://openai.vocareum.com/v1", enable_scoring=True)

# Support Functions
def product_manager_support_function(query: str) -> str:
    """Run Product Manager flow: respond to the query and validate the output.

    Steps:
    1) Generate a PM response using the Product Manager knowledge agent
    2) Evaluate that response with the Product Manager evaluation agent
    3) Return the final, validated response (fallback to raw response if missing)
    """
    response_from_knowledge = product_manager_knowledge_agent.respond(query)
    evaluation = product_manager_evaluation_agent.evaluate(response_from_knowledge)
    if isinstance(evaluation, dict) and "score" in evaluation:
        print(f"[Product Manager] Evaluation score: {evaluation['score']}")
    return evaluation.get("final_response", response_from_knowledge)

def program_manager_support_function(query: str) -> str:
    """Run Program Manager flow: respond and validate per feature criteria."""
    response_from_knowledge = program_manager_knowledge_agent.respond(query)
    evaluation = program_manager_evaluation_agent.evaluate(response_from_knowledge)
    if isinstance(evaluation, dict) and "score" in evaluation:
        print(f"[Program Manager] Evaluation score: {evaluation['score']}")
    return evaluation.get("final_response", response_from_knowledge)

def development_engineer_support_function(query: str) -> str:
    """Run Development Engineer flow: respond and validate per task criteria."""
    response_from_knowledge = development_engineer_knowledge_agent.respond(query)
    evaluation = development_engineer_evaluation_agent.evaluate(response_from_knowledge)
    if isinstance(evaluation, dict) and "score" in evaluation:
        print(f"[Development Engineer] Evaluation score: {evaluation['score']}")
    return evaluation.get("final_response", response_from_knowledge)

# Routing Agent
routing_agent = RoutingAgent(openai_api_key, [
    {"name": "Product Manager", "description": persona_product_manager, "func": product_manager_support_function},
    {"name": "Program Manager", "description": persona_program_manager, "func": program_manager_support_function},
    {"name": "Development Engineer", "description": persona_dev_engineer, "func": development_engineer_support_function},
], base_url="https://openai.vocareum.com/v1")

# Run the workflow

print("\n*** Workflow execution started ***\n")
# Workflow Prompt
# ****
workflow_prompt = "What would the development tasks for this product be?"
# ****
print(f"Task to complete in this workflow, workflow prompt = {workflow_prompt}")

print("\nDefining workflow steps from the workflow prompt")

# 1) Extract steps
workflow_steps = action_planning_agent.extract_steps_from_prompt(workflow_prompt)
print(f"Extracted {len(workflow_steps)} step(s):")
for s in workflow_steps:
    print(s)

# 2) Initialize results accumulator
completed_steps = []

# 3) Execute steps via router
for step in workflow_steps:
    print(f"\n--- Executing step ---\n{step}")
    try:
        routed_output = routing_agent.route(step)
    except Exception as e:
        routed_output = f"[ERROR] Routing failed for step: {step}. Reason: {e}"
    completed_steps.append(routed_output)
    print("Step result:\n" + str(routed_output))

# 4) Print final output
print("\n*** Workflow execution completed ***\n")
if completed_steps:
    print("Final output:\n" + str(completed_steps[-1]))
else:
    print("No steps were completed.")
