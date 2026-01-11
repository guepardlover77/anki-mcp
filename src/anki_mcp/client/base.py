"""Base HTTP client for AnkiConnect API."""

import asyncio
from typing import Any

import httpx

from anki_mcp.config import Settings, get_settings


class AnkiConnectError(Exception):
    """Exception raised when AnkiConnect returns an error."""

    def __init__(
        self,
        message: str,
        error: str | None = None,
        suggestions: list[str] | None = None,
    ):
        self.message = message
        self.error = error
        self.suggestions = suggestions or []
        super().__init__(message)


class AnkiConnectClient:
    """Async HTTP client for AnkiConnect API.

    AnkiConnect uses a simple JSON-RPC-like protocol:
    - All requests are POST to the same endpoint
    - Request body: {"action": "actionName", "version": 6, "params": {...}}
    - Response: {"result": ..., "error": null} or {"result": null, "error": "..."}
    """

    API_VERSION = 6

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds
    RETRY_BACKOFF = 2.0  # exponential backoff multiplier

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
        """Get or create the HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._settings.anki_connect_url,
                timeout=self._settings.timeout,
                headers={"Content-Type": "application/json"},
                # Connection pooling for better performance and reliability
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=30.0,
                ),
                # Enable HTTP/2 for better performance if available
                http2=True,
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
        """Invoke an AnkiConnect action with automatic retry on transient failures.

        Args:
            action: The AnkiConnect action name.
            **params: Parameters for the action.

        Returns:
            The result from AnkiConnect.

        Raises:
            AnkiConnectError: If AnkiConnect returns an error or connection fails.
        """
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                return await self._do_invoke(action, **params)
            except httpx.ConnectError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF**attempt)
                    await asyncio.sleep(delay)
                    continue
                # Final attempt failed - provide detailed guidance
                raise AnkiConnectError(
                    "Cannot connect to AnkiConnect",
                    error=str(e),
                    suggestions=[
                        "1. Make sure Anki is running",
                        "2. Verify AnkiConnect add-on is installed (Tools > Add-ons, code: 2055492159)",
                        "3. Restart Anki if you just installed AnkiConnect",
                        f"4. Check that AnkiConnect is accessible at {self._settings.anki_connect_url}",
                        "5. Verify no firewall is blocking localhost:8765",
                    ],
                ) from e
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (self.RETRY_BACKOFF**attempt)
                    await asyncio.sleep(delay)
                    continue
                # Timeout after retries
                raise AnkiConnectError(
                    f"AnkiConnect request timed out after {self.MAX_RETRIES} attempts",
                    error=str(e),
                    suggestions=[
                        "1. Anki may be busy with a large operation",
                        "2. Try again in a few moments",
                        "3. Check if Anki is frozen or unresponsive",
                        "4. Consider increasing timeout in settings",
                    ],
                ) from e
            except httpx.HTTPStatusError as e:
                # HTTP errors don't retry - they indicate a protocol issue
                raise AnkiConnectError(
                    f"HTTP error from AnkiConnect: {e.response.status_code}",
                    error=str(e),
                    suggestions=[
                        "1. Check AnkiConnect add-on version is up to date",
                        "2. Verify AnkiConnect is properly configured",
                        "3. Try restarting Anki",
                    ],
                ) from e

        # Should never reach here, but for type safety
        raise AnkiConnectError(
            "Failed to connect after retries",
            error=str(last_error) if last_error else "Unknown error",
        )

    async def _do_invoke(self, action: str, **params: Any) -> Any:
        """Internal method to perform the actual AnkiConnect invocation.

        Args:
            action: The AnkiConnect action name.
            **params: Parameters for the action.

        Returns:
            The result from AnkiConnect.

        Raises:
            httpx exceptions or AnkiConnectError.
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

        response = await client.post("/", json=payload)
        response.raise_for_status()

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
