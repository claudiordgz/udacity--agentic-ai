"""Test fixtures for the lesson 7 exercise."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from core import database_service
from data.fraud_data import seed_demo_records


@pytest.fixture(autouse=True)
def reset_database() -> None:
    """Reset the shared database before each test to ensure isolation."""

    database_service.reset_all()


@pytest.fixture
def demo_data() -> None:
    """Populate the deterministic demo records for tests that expect them."""

    seed_demo_records()

