"""MCP Tools for Anki card operations."""

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import CardQueue, CardType
from anki_mcp.server import get_anki_actions


def register_card_tools(mcp: FastMCP) -> None:
    """Register card-related tools with the MCP server.

    Tools:
    - find_cards: Search for cards
    - get_card_info: Get card details
    - suspend_cards: Suspend cards
    - unsuspend_cards: Unsuspend cards
    - get_due_cards: Get cards due for review
    - move_cards: Move cards to a different deck
    """

    @mcp.tool()
    async def find_cards(
        query: str,
        limit: int | None = None,
    ) -> dict:
        """Search for cards using Anki's search syntax.

        Args:
            query: Anki search query. Examples:
                - "deck:French" - cards in French deck
                - "is:new" - new cards
                - "is:due" - due cards
                - "is:suspended" - suspended cards
                - "is:buried" - buried cards
                - "is:learn" - learning cards
                - "is:review" - review cards
                - "-is:suspended" - not suspended
                - "prop:due=0" - due today
                - "prop:ivl>=21" - interval >= 21 days
            limit: Maximum number of results to return.

        Returns:
            List of matching card IDs.
        """
        try:
            actions = get_anki_actions()
            card_ids = await actions.find_cards(query)

            if limit:
                card_ids = card_ids[:limit]

            return {
                "card_ids": card_ids,
                "count": len(card_ids),
                "query": query,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_card_info(card_ids: list[int]) -> dict:
        """Get detailed information about cards.

        Args:
            card_ids: List of card IDs to retrieve.

        Returns:
            Detailed card information including question, answer, and scheduling info.
        """
        try:
            actions = get_anki_actions()
            cards = await actions.get_cards_info(card_ids)

            # Map type and queue values to readable strings
            type_names = {
                CardType.NEW: "new",
                CardType.LEARNING: "learning",
                CardType.REVIEW: "review",
                CardType.RELEARNING: "relearning",
            }
            queue_names = {
                CardQueue.SUSPENDED: "suspended",
                CardQueue.SIBLING_BURIED: "sibling_buried",
                CardQueue.MANUALLY_BURIED: "manually_buried",
                CardQueue.NEW: "new",
                CardQueue.LEARNING: "learning",
                CardQueue.REVIEW: "review",
                CardQueue.DAY_LEARNING: "day_learning",
                CardQueue.PREVIEW: "preview",
            }

            result = []
            for card in cards:
                fields_dict = {
                    name: field.value for name, field in card.fields.items()
                }
                result.append({
                    "card_id": card.card_id,
                    "note_id": card.note_id,
                    "deck_name": card.deck_name,
                    "model_name": card.model_name,
                    "question": card.question,
                    "answer": card.answer,
                    "fields": fields_dict,
                    "type": type_names.get(card.type, str(card.type)),
                    "queue": queue_names.get(card.queue, str(card.queue)),
                    "due": card.due,
                    "interval_days": card.interval,
                    "ease_factor": card.factor / 1000 if card.factor else None,
                    "reviews": card.reps,
                    "lapses": card.lapses,
                })

            return {
                "cards": result,
                "count": len(result),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def suspend_cards(card_ids: list[int]) -> dict:
        """Suspend cards (exclude from reviews).

        Args:
            card_ids: List of card IDs to suspend.

        Returns:
            Confirmation of suspension.
        """
        try:
            actions = get_anki_actions()
            success = await actions.suspend_cards(card_ids)
            return {
                "success": success,
                "suspended_count": len(card_ids),
                "message": f"Suspended {len(card_ids)} cards",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def unsuspend_cards(card_ids: list[int]) -> dict:
        """Unsuspend cards (include in reviews again).

        Args:
            card_ids: List of card IDs to unsuspend.

        Returns:
            Confirmation of unsuspension.
        """
        try:
            actions = get_anki_actions()
            success = await actions.unsuspend_cards(card_ids)
            return {
                "success": success,
                "unsuspended_count": len(card_ids),
                "message": f"Unsuspended {len(card_ids)} cards",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_due_cards(
        deck_name: str | None = None,
        include_new: bool = True,
        limit: int | None = None,
    ) -> dict:
        """Get cards that are due for review.

        Args:
            deck_name: Optional deck to filter by.
            include_new: Include new cards (default: True).
            limit: Maximum number of results.

        Returns:
            List of due card IDs with basic info.
        """
        try:
            actions = get_anki_actions()

            # Build query
            if include_new:
                query = "(is:due OR is:new)"
            else:
                query = "is:due"

            if deck_name:
                query = f'deck:"{deck_name}" ({query})'

            card_ids = await actions.find_cards(query)

            if limit:
                card_ids = card_ids[:limit]

            # Get basic info for these cards
            cards = await actions.get_cards_info(card_ids) if card_ids else []

            due_cards = []
            new_count = 0
            review_count = 0

            for card in cards:
                is_new = card.type == CardType.NEW
                if is_new:
                    new_count += 1
                else:
                    review_count += 1

                due_cards.append({
                    "card_id": card.card_id,
                    "deck_name": card.deck_name,
                    "is_new": is_new,
                    "due": card.due,
                })

            return {
                "cards": due_cards,
                "total": len(due_cards),
                "new_count": new_count,
                "review_count": review_count,
                "deck_filter": deck_name,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def move_cards(card_ids: list[int], target_deck: str) -> dict:
        """Move cards to a different deck.

        Args:
            card_ids: List of card IDs to move.
            target_deck: Name of the target deck (will be created if it doesn't exist).

        Returns:
            Confirmation of move.
        """
        try:
            actions = get_anki_actions()
            await actions.change_deck(card_ids, target_deck)
            return {
                "success": True,
                "moved_count": len(card_ids),
                "target_deck": target_deck,
                "message": f"Moved {len(card_ids)} cards to '{target_deck}'",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
