"""FastMCP server setup for Anki MCP."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.actions import AnkiActions
from anki_mcp.client.base import AnkiConnectClient
from anki_mcp.config import get_settings


class AnkiContext:
    """Context holding the Anki client and actions."""

    def __init__(self) -> None:
        self._client: AnkiConnectClient | None = None
        self._actions: AnkiActions | None = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure the context is initialized (lazy initialization)."""
        if not self._initialized:
            settings = get_settings()
            self._client = AnkiConnectClient(settings)
            self._actions = AnkiActions(self._client)
            self._initialized = True

    async def initialize(self) -> None:
        """Initialize the Anki client and validate connection."""
        self._ensure_initialized()

        # Validate connection on startup
        if self._client:
            if not await self._client.is_connected():
                # Don't fail hard - just log warning
                # This allows the server to start even if Anki isn't running
                # Tools will provide clear error messages when Anki is needed
                import sys

                print(
                    "WARNING: Cannot connect to AnkiConnect. "
                    "Please ensure Anki is running with AnkiConnect add-on installed.",
                    file=sys.stderr,
                )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> AnkiConnectClient:
        """Get the AnkiConnect client."""
        self._ensure_initialized()
        if self._client is None:
            raise RuntimeError("AnkiContext not initialized")
        return self._client

    @property
    def actions(self) -> AnkiActions:
        """Get the AnkiActions instance."""
        self._ensure_initialized()
        if self._actions is None:
            raise RuntimeError("AnkiContext not initialized")
        return self._actions


# Global context
_context = AnkiContext()


def get_anki_client() -> AnkiConnectClient:
    """Get the AnkiConnect client instance."""
    return _context.client


def get_anki_actions() -> AnkiActions:
    """Get the AnkiActions instance."""
    return _context.actions


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage server lifecycle."""
    await _context.initialize()
    try:
        yield
    finally:
        await _context.cleanup()


# Create the MCP server
mcp = FastMCP(
    name="anki-mcp",
    version="0.1.0",
)


def create_server() -> FastMCP:
    """Create and configure the MCP server with all tools and resources.

    Returns:
        Configured FastMCP server instance.
    """
    # Import and register tools
    from anki_mcp.tools.deck import register_deck_tools
    from anki_mcp.tools.note import register_note_tools
    from anki_mcp.tools.card import register_card_tools
    from anki_mcp.tools.review import register_review_tools
    from anki_mcp.tools.statistics import register_statistics_tools
    from anki_mcp.tools.model import register_model_tools
    from anki_mcp.tools.media import register_media_tools
    from anki_mcp.tools.sync import register_sync_tools
    from anki_mcp.tools.import_export import register_import_export_tools
    from anki_mcp.tools.generation import register_generation_tools
    from anki_mcp.tools.pdf_qcm import register_pdf_qcm_tools
    from anki_mcp.tools.pdf_course import register_pdf_course_tools
    from anki_mcp.resources.base import register_resources
    from anki_mcp.prompts.base import register_prompts

    # Core tools
    register_deck_tools(mcp)
    register_note_tools(mcp)
    register_card_tools(mcp)

    # Review and statistics
    register_review_tools(mcp)
    register_statistics_tools(mcp)

    # Model and media
    register_model_tools(mcp)
    register_media_tools(mcp)

    # Sync and import/export
    register_sync_tools(mcp)
    register_import_export_tools(mcp)

    # Generation (priority)
    register_generation_tools(mcp)
    register_pdf_qcm_tools(mcp)
    register_pdf_course_tools(mcp)

    # Resources
    register_resources(mcp)

    # Prompts
    register_prompts(mcp)

    return mcp
