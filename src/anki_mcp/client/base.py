"""Base HTTP client for AnkiConnect API."""

from typing import Any

import httpx

from anki_mcp.config import Settings, get_settings


class AnkiConnectError(Exception):
    """Exception raised when AnkiConnect returns an error."""

    def __init__(self, message: str, error: str | None = None):
        self.message = message
        self.error = error
        super().__init__(message)


class AnkiConnectClient:
    """Async HTTP client for AnkiConnect API.

    AnkiConnect uses a simple JSON-RPC-like protocol:
    - All requests are POST to the same endpoint
    - Request body: {"action": "actionName", "version": 6, "params": {...}}
    - Response: {"result": ..., "error": null} or {"result": null, "error": "..."}
    """

    API_VERSION = 6

    def __init__(self, settings: Settings | None = None):
        """Initialize the client.

        Args:
            settings: Optional settings instance. Uses default if not provided.
        """
        self._settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    @property
    def settings(self) -> Settings:
        """Get the settings instance."""
        return self._settings

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._settings.anki_connect_url,
                timeout=self._settings.timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AnkiConnectClient":
        """Async context manager entry."""
        await self._get_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def invoke(self, action: str, **params: Any) -> Any:
        """Invoke an AnkiConnect action.

        Args:
            action: The AnkiConnect action name.
            **params: Parameters for the action.

        Returns:
            The result from AnkiConnect.

        Raises:
            AnkiConnectError: If AnkiConnect returns an error or connection fails.
        """
        client = await self._get_client()

        payload: dict[str, Any] = {
            "action": action,
            "version": self.API_VERSION,
        }

        if params:
            payload["params"] = params

        # Add API key if configured
        if self._settings.api_key:
            payload["key"] = self._settings.api_key

        try:
            response = await client.post("/", json=payload)
            response.raise_for_status()
        except httpx.ConnectError as e:
            raise AnkiConnectError(
                "Cannot connect to AnkiConnect. Is Anki running with AnkiConnect add-on?",
                error=str(e),
            ) from e
        except httpx.HTTPStatusError as e:
            raise AnkiConnectError(
                f"HTTP error from AnkiConnect: {e.response.status_code}",
                error=str(e),
            ) from e
        except httpx.TimeoutException as e:
            raise AnkiConnectError(
                "AnkiConnect request timed out",
                error=str(e),
            ) from e

        data = response.json()

        # Check for AnkiConnect error
        if data.get("error"):
            raise AnkiConnectError(
                f"AnkiConnect error: {data['error']}",
                error=data["error"],
            )

        return data.get("result")

    async def is_connected(self) -> bool:
        """Check if AnkiConnect is reachable.

        Returns:
            True if connected, False otherwise.
        """
        try:
            version = await self.invoke("version")
            return version is not None
        except AnkiConnectError:
            return False

    async def request_permission(self) -> dict[str, Any]:
        """Request permission from the user to use AnkiConnect.

        Returns:
            Permission result with 'permission' and 'requireApiKey' fields.
        """
        result = await self.invoke("requestPermission")
        return result or {}
