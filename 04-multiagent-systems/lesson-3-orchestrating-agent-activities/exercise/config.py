"""Configuration for LLM agents."""

import os
from dotenv import load_dotenv
from smolagents import OpenAIServerModel

load_dotenv(dotenv_path="../../.env")
openai_api_key = os.getenv("OPENAI_API_KEY")

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_base="https://openai.vocareum.com/v1",
    api_key=openai_api_key,
)

