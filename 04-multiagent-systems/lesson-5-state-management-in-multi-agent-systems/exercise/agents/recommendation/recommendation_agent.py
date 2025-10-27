"""Recommendation Agent for providing personalized fruit recommendations."""

from smolagents import ToolCallingAgent
import sys
sys.path.append('../..')
from config import model
from agents.recommendation.tools import get_purchase_history, generate_recommendation


class RecommendationAgent(ToolCallingAgent):
    """Agent for providing personalized recommendations using LLM reasoning."""
    
    def __init__(self):
        super().__init__(
            tools=[get_purchase_history, generate_recommendation],
            model=model,
            name="recommendation_agent",
            description="Agent that provides personalized fruit recommendations based on customer purchase history."
        )
