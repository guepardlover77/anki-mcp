"""Anki MCP Server - Gérez Anki depuis Claude avec génération automatique de flashcards."""

__version__ = "0.1.0"
__author__ = "Anki MCP"

from anki_mcp.server import create_server, mcp

__all__ = ["create_server", "mcp", "__version__"]
