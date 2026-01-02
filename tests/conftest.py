"""Pytest configuration and fixtures for Anki MCP tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from anki_mcp.client.base import AnkiConnectClient
from anki_mcp.client.actions import AnkiActions
from anki_mcp.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        host="localhost",
        port=8765,
        timeout=5.0,
        debug=True,
    )


@pytest.fixture
def mock_client(settings: Settings) -> AnkiConnectClient:
    """Create a mock AnkiConnect client."""
    client = AnkiConnectClient(settings)
    client.invoke = AsyncMock()
    return client


@pytest.fixture
def mock_actions(mock_client: AnkiConnectClient) -> AnkiActions:
    """Create AnkiActions with mock client."""
    return AnkiActions(mock_client)
