"""MCP Resources for Anki data."""

import json

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import CardType
from anki_mcp.server import get_anki_actions


def register_resources(mcp: FastMCP) -> None:
    """Register Anki resources with the MCP server.

    Resources:
    - anki://decks - List all decks
    - anki://decks/{name} - Get deck details
    - anki://decks/{name}/due - Get due cards for a deck
    - anki://models - List all note types
    - anki://models/{name} - Get model details
    - anki://tags - List all tags
    - anki://stats/today - Today's statistics
    - anki://notes/{id} - Get note by ID
    - anki://cards/{id} - Get card by ID
    """

    @mcp.resource("anki://decks")
    async def get_all_decks() -> str:
        """Get all Anki decks with their statistics."""
        try:
            actions = get_anki_actions()
            decks = await actions.get_deck_names_and_ids()
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

            return json.dumps({"decks": result, "total": len(result)}, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://decks/{name}")
    async def get_deck_details(name: str) -> str:
        """Get details for a specific deck."""
        try:
            actions = get_anki_actions()

            # Verify deck exists
            decks = await actions.get_deck_names_and_ids()
            if name not in decks:
                return json.dumps({"error": f"Deck '{name}' not found"})

            # Get stats
            stats = await actions.get_deck_stats([name])
            deck_stats = stats.get(name)

            # Get config
            config = await actions.get_deck_config(name)

            result = {
                "name": name,
                "id": decks[name],
                "statistics": {
                    "new_count": deck_stats.new_count if deck_stats else 0,
                    "learn_count": deck_stats.learn_count if deck_stats else 0,
                    "review_count": deck_stats.review_count if deck_stats else 0,
                    "total_cards": deck_stats.total_in_deck if deck_stats else 0,
                },
                "config": {
                    "name": config.name,
                    "autoplay": config.autoplay,
                    "is_filtered": config.dyn,
                    "max_answer_time": config.max_taken,
                },
            }

            return json.dumps(result, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://decks/{name}/due")
    async def get_deck_due_cards(name: str) -> str:
        """Get due cards for a specific deck."""
        try:
            actions = get_anki_actions()

            # Find due and new cards
            query = f'deck:"{name}" (is:due OR is:new)'
            card_ids = await actions.find_cards(query)
            cards = await actions.get_cards_info(card_ids[:50]) if card_ids else []  # Limit to 50

            due_cards = []
            for card in cards:
                due_cards.append({
                    "card_id": card.card_id,
                    "is_new": card.type == CardType.NEW,
                    "question_preview": card.question[:100] if card.question else "",
                })

            return json.dumps({
                "deck": name,
                "total_due": len(card_ids),
                "cards_preview": due_cards,
            }, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://models")
    async def get_all_models() -> str:
        """Get all note types (models)."""
        try:
            actions = get_anki_actions()
            models = await actions.get_model_names_and_ids()

            result = []
            for name, model_id in sorted(models.items()):
                fields = await actions.get_model_field_names(name)
                result.append({
                    "name": name,
                    "id": model_id,
                    "fields": fields,
                })

            return json.dumps({"models": result, "total": len(result)}, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://models/{name}")
    async def get_model_details(name: str) -> str:
        """Get details for a specific note type."""
        try:
            actions = get_anki_actions()
            model = await actions.get_model_info(name)

            return json.dumps({
                "name": model.name,
                "id": model.model_id,
                "fields": model.fields,
            }, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://tags")
    async def get_all_tags() -> str:
        """Get all tags in the collection."""
        try:
            actions = get_anki_actions()
            tags = await actions.get_tags()

            return json.dumps({
                "tags": sorted(tags),
                "total": len(tags),
            }, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://stats/today")
    async def get_today_stats() -> str:
        """Get today's review statistics."""
        try:
            actions = get_anki_actions()

            reviews_today = await actions.get_num_cards_reviewed_today()

            # Get counts of due cards
            due_cards = await actions.find_cards("is:due")
            new_cards = await actions.find_cards("is:new")

            return json.dumps({
                "reviews_today": reviews_today,
                "cards_due": len(due_cards),
                "new_cards_available": len(new_cards),
            }, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://notes/{note_id}")
    async def get_note_by_id(note_id: str) -> str:
        """Get a specific note by ID."""
        try:
            actions = get_anki_actions()
            notes = await actions.get_notes_info([int(note_id)])

            if not notes:
                return json.dumps({"error": f"Note {note_id} not found"})

            note = notes[0]
            fields_dict = {name: field.value for name, field in note.fields.items()}

            return json.dumps({
                "note_id": note.note_id,
                "model_name": note.model_name,
                "tags": note.tags,
                "fields": fields_dict,
                "card_ids": note.cards,
            }, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})

    @mcp.resource("anki://cards/{card_id}")
    async def get_card_by_id(card_id: str) -> str:
        """Get a specific card by ID."""
        try:
            actions = get_anki_actions()
            cards = await actions.get_cards_info([int(card_id)])

            if not cards:
                return json.dumps({"error": f"Card {card_id} not found"})

            card = cards[0]
            fields_dict = {name: field.value for name, field in card.fields.items()}

            return json.dumps({
                "card_id": card.card_id,
                "note_id": card.note_id,
                "deck_name": card.deck_name,
                "model_name": card.model_name,
                "question": card.question,
                "answer": card.answer,
                "fields": fields_dict,
                "interval_days": card.interval,
                "ease_factor": card.factor / 1000 if card.factor else None,
                "reviews": card.reps,
                "lapses": card.lapses,
            }, indent=2)
        except AnkiConnectError as e:
            return json.dumps({"error": str(e)})
