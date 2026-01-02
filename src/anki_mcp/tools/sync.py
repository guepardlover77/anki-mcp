"""MCP Tools for Anki sync operations."""

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.server import get_anki_actions, get_anki_client


def register_sync_tools(mcp: FastMCP) -> None:
    """Register sync-related tools with the MCP server.

    Tools:
    - sync_collection: Sync with AnkiWeb
    - check_connection: Check AnkiConnect status
    - get_anki_version: Get Anki version info
    """

    @mcp.tool()
    async def sync_collection() -> dict:
        """Sync the Anki collection with AnkiWeb.

        This triggers a sync with AnkiWeb, the same as clicking
        the sync button in Anki.

        Returns:
            Confirmation of sync initiation.
        """
        try:
            actions = get_anki_actions()
            await actions.sync()

            return {
                "success": True,
                "message": "Sync initiated with AnkiWeb",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def check_connection() -> dict:
        """Check if AnkiConnect is running and accessible.

        Returns:
            Connection status and AnkiConnect version.
        """
        try:
            client = get_anki_client()

            # Check connection
            connected = await client.is_connected()

            if connected:
                # Get version
                version = await client.invoke("version")
                return {
                    "connected": True,
                    "ankiconnect_version": version,
                    "url": client.settings.anki_connect_url,
                }
            else:
                return {
                    "connected": False,
                    "error": "AnkiConnect is not responding",
                    "suggestion": "Make sure Anki is running and AnkiConnect add-on is installed",
                }
        except AnkiConnectError as e:
            return {
                "connected": False,
                "error": str(e),
            }

    @mcp.tool()
    async def get_anki_version() -> dict:
        """Get Anki and AnkiConnect version information.

        Returns:
            Version details for Anki and AnkiConnect.
        """
        try:
            client = get_anki_client()
            actions = get_anki_actions()

            # Get AnkiConnect version
            ac_version = await client.invoke("version")

            # Get profile
            try:
                profiles = await client.invoke("getProfiles")
                current_profile = profiles[0] if profiles else "Unknown"
            except Exception:
                current_profile = "Unknown"

            # Get collection stats as a proxy for checking it's working
            stats = await client.invoke("getCollectionStatsHTML")

            return {
                "ankiconnect_version": ac_version,
                "current_profile": current_profile,
                "connection_url": client.settings.anki_connect_url,
                "status": "operational",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
