"""Shared test setup for core.

settings.py calls load_dotenv(), so a developer's real AI_API_KEY ends up in
the environment during test runs. Without this, any test that searches for
something the literal search cannot find would make a real API call --
spending rate limit, slowing the suite down, and failing unpredictably in CI
or on a teammate's machine.

So the AI is off for every test by default. Tests that want it put the key
back themselves, with a mocked _call_model, which is the only way it should
ever be exercised in a test.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def no_live_ai_calls(monkeypatch):
    """Switch the AI off unless a test deliberately turns it on."""
    monkeypatch.delenv("AI_API_KEY", raising=False)
