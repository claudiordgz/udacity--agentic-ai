"""Configuration for the lesson 7 fraud detection exercise."""

import os

try:
    import dotenv
except ImportError:  # pragma: no cover - fallback when dotenv is absent
    dotenv = None

if dotenv is not None:
    dotenv.load_dotenv(dotenv_path="../../.env")

openai_api_key = os.getenv("OPENAI_API_KEY")

from smolagents import OpenAIServerModel

model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_base="https://openai.vocareum.com/v1",
    api_key=openai_api_key,
)


