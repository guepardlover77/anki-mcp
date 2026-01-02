"""MCP Tools for Anki operations."""

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

__all__ = [
    "register_deck_tools",
    "register_note_tools",
    "register_card_tools",
    "register_review_tools",
    "register_statistics_tools",
    "register_model_tools",
    "register_media_tools",
    "register_sync_tools",
    "register_import_export_tools",
    "register_generation_tools",
]
