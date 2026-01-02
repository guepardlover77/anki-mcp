"""Tests for configuration module."""

import pytest

from anki_mcp.config import Settings, get_settings


def test_default_settings():
    """Test default settings values."""
    settings = Settings()

    assert settings.host == "localhost"
    assert settings.port == 8765
    assert settings.api_key is None
    assert settings.timeout == 30.0
    assert settings.server_name == "anki-mcp"
    assert settings.debug is False


def test_anki_connect_url():
    """Test AnkiConnect URL property."""
    settings = Settings(host="127.0.0.1", port=9000)

    assert settings.anki_connect_url == "http://127.0.0.1:9000"


def test_get_settings_cached():
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
