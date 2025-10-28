"""Configuration for the lesson 6 exercise."""

import os
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")
openai_api_key = os.getenv("OPENAI_API_KEY")

from smolagents import OpenAIServerModel

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_base="https://openai.vocareum.com/v1",
    api_key=openai_api_key,
)
