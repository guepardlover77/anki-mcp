"""MCP Tools for Anki deck operations."""

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.server import get_anki_actions


def register_deck_tools(mcp: FastMCP) -> None:
    """Register deck-related tools with the MCP server.

    Tools:
    - list_decks: List all decks
    - create_deck: Create a new deck
    - delete_deck: Delete a deck
    - rename_deck: Rename a deck
    - get_deck_config: Get deck configuration
    """

    @mcp.tool()
    async def list_decks() -> dict:
        """List all Anki decks with their IDs.

        Returns a dictionary with deck names and their IDs.
        Nested decks are shown with :: separator (e.g., "Parent::Child").
        """
        try:
            actions = get_anki_actions()
            decks = await actions.get_deck_names_and_ids()

            # Get stats for each deck
            deck_names = list(decks.keys())
            stats = await actions.get_deck_stats(deck_names) if deck_names else {}

            result = []
            for name, deck_id in sorted(decks.items()):
                deck_info = {
                    "name": name,
                    "id": deck_id,
                }
                if name in stats:
                    deck_info["new_count"] = stats[name].new_count
                    deck_info["learn_count"] = stats[name].learn_count
                    deck_info["review_count"] = stats[name].review_count
                    deck_info["total_cards"] = stats[name].total_in_deck
                result.append(deck_info)

            return {
                "decks": result,
                "total": len(result),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def create_deck(name: str) -> dict:
        """Create a new Anki deck.

        Args:
            name: The deck name. Use :: for nested decks (e.g., "Languages::French").

        Returns:
            The created deck's ID.
        """
        try:
            actions = get_anki_actions()
            deck_id = await actions.create_deck(name)
            return {
                "success": True,
                "deck_id": deck_id,
                "name": name,
                "message": f"Deck '{name}' created successfully",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def delete_deck(name: str, delete_cards: bool = True) -> dict:
        """Delete an Anki deck.

        Args:
            name: The deck name to delete.
            delete_cards: Whether to also delete cards in the deck (default: True).
                         If False, cards are moved to the Default deck.

        Returns:
            Confirmation of deletion.
        """
        try:
            actions = get_anki_actions()

            # Verify deck exists
            decks = await actions.get_deck_names()
            if name not in decks:
                return {"error": f"Deck '{name}' not found"}

            await actions.delete_deck(name, cards_too=delete_cards)
            return {
                "success": True,
                "message": f"Deck '{name}' deleted successfully",
                "cards_deleted": delete_cards,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def rename_deck(old_name: str, new_name: str) -> dict:
        """Rename an Anki deck.

        Args:
            old_name: Current deck name.
            new_name: New deck name.

        Returns:
            Confirmation of rename.
        """
        try:
            actions = get_anki_actions()

            # Verify deck exists
            decks = await actions.get_deck_names()
            if old_name not in decks:
                return {"error": f"Deck '{old_name}' not found"}

            if new_name in decks:
                return {"error": f"Deck '{new_name}' already exists"}

            await actions.rename_deck(old_name, new_name)
            return {
                "success": True,
                "old_name": old_name,
                "new_name": new_name,
                "message": f"Deck renamed from '{old_name}' to '{new_name}'",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_deck_config(name: str) -> dict:
        """Get configuration for an Anki deck.

        Args:
            name: The deck name.

        Returns:
            Deck configuration including review and new card settings.
        """
        try:
            actions = get_anki_actions()

            # Verify deck exists
            decks = await actions.get_deck_names()
            if name not in decks:
                return {"error": f"Deck '{name}' not found"}

            config = await actions.get_deck_config(name)
            return {
                "name": name,
                "config_id": config.id,
                "config_name": config.name,
                "autoplay": config.autoplay,
                "is_filtered": config.dyn,
                "max_answer_time": config.max_taken,
                "show_timer": config.timer,
                "new_cards": config.new,
                "reviews": config.rev,
                "lapses": config.lapse,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
