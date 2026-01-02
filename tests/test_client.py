"""Tests for AnkiConnect client."""

import pytest
from unittest.mock import AsyncMock, patch

from anki_mcp.client.base import AnkiConnectClient, AnkiConnectError
from anki_mcp.config import Settings


@pytest.fixture
def client():
    """Create a test client."""
    settings = Settings(host="localhost", port=8765, timeout=5.0)
    return AnkiConnectClient(settings)


class TestAnkiConnectClient:
    """Tests for AnkiConnectClient."""

    def test_api_version(self, client: AnkiConnectClient):
        """Test API version is set correctly."""
        assert client.API_VERSION == 6

    def test_settings(self, client: AnkiConnectClient):
        """Test settings are accessible."""
        assert client.settings.host == "localhost"
        assert client.settings.port == 8765

    @pytest.mark.asyncio
    async def test_invoke_builds_correct_payload(self, client: AnkiConnectClient):
        """Test invoke builds correct JSON payload."""
        with patch.object(client, '_get_client') as mock_get_client:
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.json.return_value = {"result": "test", "error": None}
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            result = await client.invoke("testAction", param1="value1")

            # Verify the call
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            payload = call_args.kwargs["json"]

            assert payload["action"] == "testAction"
            assert payload["version"] == 6
            assert payload["params"] == {"param1": "value1"}
            assert result == "test"

    @pytest.mark.asyncio
    async def test_invoke_handles_error(self, client: AnkiConnectClient):
        """Test invoke handles AnkiConnect errors."""
        with patch.object(client, '_get_client') as mock_get_client:
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.json.return_value = {"result": None, "error": "test error"}
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            with pytest.raises(AnkiConnectError) as exc_info:
                await client.invoke("testAction")

            assert "test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close_client(self, client: AnkiConnectClient):
        """Test closing the client."""
        # Should not raise when client is None
        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, client: AnkiConnectClient):
        """Test async context manager."""
        async with client as c:
            assert c is client
