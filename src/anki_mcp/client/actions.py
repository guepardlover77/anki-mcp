"""High-level API wrappers for AnkiConnect actions."""

from typing import Any

from anki_mcp.client.base import AnkiConnectClient
from anki_mcp.client.models import (
    CardEase,
    CardInfo,
    DeckConfig,
    DeckStats,
    ModelInfo,
    NoteInfo,
    NoteInput,
)


class AnkiActions:
    """High-level wrapper for AnkiConnect actions.

    Groups related actions together for easier use.
    """

    def __init__(self, client: AnkiConnectClient):
        """Initialize with an AnkiConnect client.

        Args:
            client: The AnkiConnect client to use.
        """
        self.client = client

    # ============ Deck Actions ============

    async def get_deck_names(self) -> list[str]:
        """Get all deck names."""
        return await self.client.invoke("deckNames")

    async def get_deck_names_and_ids(self) -> dict[str, int]:
        """Get deck names with their IDs."""
        return await self.client.invoke("deckNamesAndIds")

    async def create_deck(self, name: str) -> int:
        """Create a new deck.

        Args:
            name: The deck name (can include :: for nested decks).

        Returns:
            The ID of the created deck.
        """
        return await self.client.invoke("createDeck", deck=name)

    async def delete_deck(self, name: str, cards_too: bool = True) -> None:
        """Delete a deck.

        Args:
            name: The deck name to delete.
            cards_too: Whether to also delete the cards in the deck.
        """
        await self.client.invoke("deleteDecks", decks=[name], cardsToo=cards_too)

    async def rename_deck(self, old_name: str, new_name: str) -> None:
        """Rename a deck.

        Args:
            old_name: Current deck name.
            new_name: New deck name.
        """
        # Get deck ID first
        decks = await self.get_deck_names_and_ids()
        if old_name not in decks:
            raise ValueError(f"Deck '{old_name}' not found")

        # Use changeDeck action to move cards, then delete old deck
        # Actually, AnkiConnect doesn't have a direct rename, so we use a workaround
        await self.client.invoke(
            "changeDeck",
            cards=await self.find_cards(f'deck:"{old_name}"'),
            deck=new_name,
        )
        # Create the new deck if it doesn't exist (changeDeck creates it)
        # Then delete the old empty deck
        await self.client.invoke("deleteDecks", decks=[old_name], cardsToo=False)

    async def get_deck_config(self, name: str) -> DeckConfig:
        """Get deck configuration.

        Args:
            name: The deck name.

        Returns:
            The deck configuration.
        """
        result = await self.client.invoke("getDeckConfig", deck=name)
        return DeckConfig.model_validate(result)

    async def get_deck_stats(self, deck_names: list[str]) -> dict[str, DeckStats]:
        """Get statistics for multiple decks.

        Args:
            deck_names: List of deck names.

        Returns:
            Dictionary mapping deck names to their stats.
        """
        result = await self.client.invoke("getDeckStats", decks=deck_names)
        stats = {}
        for deck_id, data in result.items():
            stats[data["name"]] = DeckStats(
                deck_id=int(deck_id),
                name=data["name"],
                new_count=data.get("new_count", 0),
                learn_count=data.get("learn_count", 0),
                review_count=data.get("review_count", 0),
                total_in_deck=data.get("total_in_deck", 0),
            )
        return stats

    # ============ Note Actions ============

    async def add_note(self, note: NoteInput) -> int:
        """Add a single note.

        Args:
            note: The note to add.

        Returns:
            The ID of the created note.
        """
        note_dict: dict[str, Any] = {
            "deckName": note.deck_name,
            "modelName": note.model_name,
            "fields": note.fields,
            "tags": note.tags,
        }

        if note.options:
            note_dict["options"] = note.options
        if note.audio:
            note_dict["audio"] = note.audio
        if note.video:
            note_dict["video"] = note.video
        if note.picture:
            note_dict["picture"] = note.picture

        return await self.client.invoke("addNote", note=note_dict)

    async def add_notes(self, notes: list[NoteInput]) -> list[int | None]:
        """Add multiple notes.

        Args:
            notes: List of notes to add.

        Returns:
            List of note IDs (None for failed additions).
        """
        notes_data = []
        for note in notes:
            note_dict: dict[str, Any] = {
                "deckName": note.deck_name,
                "modelName": note.model_name,
                "fields": note.fields,
                "tags": note.tags,
            }
            if note.options:
                note_dict["options"] = note.options
            notes_data.append(note_dict)

        return await self.client.invoke("addNotes", notes=notes_data)

    async def update_note_fields(self, note_id: int, fields: dict[str, str]) -> None:
        """Update note fields.

        Args:
            note_id: The note ID.
            fields: Field name to value mapping.
        """
        await self.client.invoke(
            "updateNoteFields", note={"id": note_id, "fields": fields}
        )

    async def update_note_tags(
        self, note_id: int, tags: list[str]
    ) -> None:
        """Replace all tags on a note.

        Args:
            note_id: The note ID.
            tags: New tags for the note.
        """
        # Get current note info
        notes = await self.get_notes_info([note_id])
        if not notes:
            raise ValueError(f"Note {note_id} not found")

        current_tags = notes[0].tags

        # Remove old tags
        if current_tags:
            await self.client.invoke(
                "removeTags", notes=[note_id], tags=" ".join(current_tags)
            )

        # Add new tags
        if tags:
            await self.client.invoke("addTags", notes=[note_id], tags=" ".join(tags))

    async def delete_notes(self, note_ids: list[int]) -> None:
        """Delete notes.

        Args:
            note_ids: List of note IDs to delete.
        """
        await self.client.invoke("deleteNotes", notes=note_ids)

    async def find_notes(self, query: str) -> list[int]:
        """Find notes matching a query.

        Args:
            query: Anki search query.

        Returns:
            List of matching note IDs.
        """
        return await self.client.invoke("findNotes", query=query)

    async def get_notes_info(self, note_ids: list[int]) -> list[NoteInfo]:
        """Get information about notes.

        Args:
            note_ids: List of note IDs.

        Returns:
            List of note information.
        """
        result = await self.client.invoke("notesInfo", notes=note_ids)
        return [NoteInfo.model_validate(n) for n in result]

    async def add_tags(self, note_ids: list[int], tags: str) -> None:
        """Add tags to notes.

        Args:
            note_ids: List of note IDs.
            tags: Space-separated tags to add.
        """
        await self.client.invoke("addTags", notes=note_ids, tags=tags)

    async def remove_tags(self, note_ids: list[int], tags: str) -> None:
        """Remove tags from notes.

        Args:
            note_ids: List of note IDs.
            tags: Space-separated tags to remove.
        """
        await self.client.invoke("removeTags", notes=note_ids, tags=tags)

    async def get_tags(self) -> list[str]:
        """Get all tags in the collection."""
        return await self.client.invoke("getTags")

    # ============ Card Actions ============

    async def find_cards(self, query: str) -> list[int]:
        """Find cards matching a query.

        Args:
            query: Anki search query.

        Returns:
            List of matching card IDs.
        """
        return await self.client.invoke("findCards", query=query)

    async def get_cards_info(self, card_ids: list[int]) -> list[CardInfo]:
        """Get information about cards.

        Args:
            card_ids: List of card IDs.

        Returns:
            List of card information.
        """
        result = await self.client.invoke("cardsInfo", cards=card_ids)
        return [CardInfo.model_validate(c) for c in result]

    async def suspend_cards(self, card_ids: list[int]) -> bool:
        """Suspend cards.

        Args:
            card_ids: List of card IDs to suspend.

        Returns:
            True if successful.
        """
        return await self.client.invoke("suspend", cards=card_ids)

    async def unsuspend_cards(self, card_ids: list[int]) -> bool:
        """Unsuspend cards.

        Args:
            card_ids: List of card IDs to unsuspend.

        Returns:
            True if successful.
        """
        return await self.client.invoke("unsuspend", cards=card_ids)

    async def are_cards_suspended(self, card_ids: list[int]) -> list[bool]:
        """Check if cards are suspended.

        Args:
            card_ids: List of card IDs to check.

        Returns:
            List of booleans indicating suspension status.
        """
        return await self.client.invoke("areSuspended", cards=card_ids)

    async def get_cards_due(self, deck_name: str | None = None) -> list[int]:
        """Get cards that are due for review.

        Args:
            deck_name: Optional deck to filter by.

        Returns:
            List of due card IDs.
        """
        query = "is:due"
        if deck_name:
            query = f'deck:"{deck_name}" is:due'
        return await self.find_cards(query)

    async def change_deck(self, card_ids: list[int], deck_name: str) -> None:
        """Move cards to a different deck.

        Args:
            card_ids: List of card IDs to move.
            deck_name: Target deck name.
        """
        await self.client.invoke("changeDeck", cards=card_ids, deck=deck_name)

    async def set_ease_factor(self, card_ids: list[int], ease_factor: int) -> bool:
        """Set the ease factor for cards.

        Args:
            card_ids: List of card IDs.
            ease_factor: New ease factor (e.g., 2500 for 250%).

        Returns:
            True if successful.
        """
        return await self.client.invoke(
            "setEaseFactors", cards=card_ids, easeFactors=[ease_factor] * len(card_ids)
        )

    # ============ Review Actions ============

    async def answer_card(self, card_id: int, ease: CardEase) -> bool:
        """Answer a card during review.

        Args:
            card_id: The card ID.
            ease: The answer ease (1-4).

        Returns:
            True if successful.
        """
        return await self.client.invoke(
            "answerCards", answers=[{"cardId": card_id, "ease": ease.value}]
        )

    async def get_reviews_of_cards(self, card_ids: list[int]) -> dict[int, list[Any]]:
        """Get review history for cards.

        Args:
            card_ids: List of card IDs.

        Returns:
            Dictionary mapping card IDs to review lists.
        """
        result = await self.client.invoke("getReviewsOfCards", cards=card_ids)
        return {int(k): v for k, v in result.items()}

    # ============ Model Actions ============

    async def get_model_names(self) -> list[str]:
        """Get all model (note type) names."""
        return await self.client.invoke("modelNames")

    async def get_model_names_and_ids(self) -> dict[str, int]:
        """Get model names with their IDs."""
        return await self.client.invoke("modelNamesAndIds")

    async def get_model_field_names(self, model_name: str) -> list[str]:
        """Get field names for a model.

        Args:
            model_name: The model name.

        Returns:
            List of field names.
        """
        return await self.client.invoke("modelFieldNames", modelName=model_name)

    async def get_model_info(self, model_name: str) -> ModelInfo:
        """Get detailed model information.

        Args:
            model_name: The model name.

        Returns:
            Model information.
        """
        models = await self.client.invoke("modelNamesAndIds")
        model_id = models.get(model_name, 0)

        fields = await self.get_model_field_names(model_name)

        return ModelInfo(
            name=model_name,
            id=model_id,
            flds=fields,
        )

    # ============ Media Actions ============

    async def store_media_file(
        self, filename: str, data: str | None = None, path: str | None = None, url: str | None = None
    ) -> str:
        """Store a media file in Anki.

        Args:
            filename: Target filename in Anki's media folder.
            data: Base64-encoded file data.
            path: Path to file on disk.
            url: URL to download file from.

        Returns:
            The filename stored.
        """
        params: dict[str, str] = {"filename": filename}
        if data:
            params["data"] = data
        elif path:
            params["path"] = path
        elif url:
            params["url"] = url
        else:
            raise ValueError("Must provide data, path, or url")

        return await self.client.invoke("storeMediaFile", **params)

    async def retrieve_media_file(self, filename: str) -> str:
        """Retrieve a media file from Anki.

        Args:
            filename: The filename to retrieve.

        Returns:
            Base64-encoded file data.
        """
        return await self.client.invoke("retrieveMediaFile", filename=filename)

    async def delete_media_file(self, filename: str) -> None:
        """Delete a media file from Anki.

        Args:
            filename: The filename to delete.
        """
        await self.client.invoke("deleteMediaFile", filename=filename)

    async def get_media_files_names(self, pattern: str = "*") -> list[str]:
        """Get media file names matching a pattern.

        Args:
            pattern: Glob pattern to match.

        Returns:
            List of matching filenames.
        """
        return await self.client.invoke("getMediaFilesNames", pattern=pattern)

    # ============ Sync Actions ============

    async def sync(self) -> None:
        """Trigger a sync with AnkiWeb."""
        await self.client.invoke("sync")

    # ============ Utility Actions ============

    async def get_num_cards_reviewed_today(self) -> int:
        """Get the number of cards reviewed today."""
        return await self.client.invoke("getNumCardsReviewedToday")

    async def get_num_cards_reviewed_by_day(self) -> list[list[Any]]:
        """Get cards reviewed by day."""
        return await self.client.invoke("getNumCardsReviewedByDay")

    async def get_collection_stats_html(self) -> str:
        """Get collection statistics as HTML."""
        return await self.client.invoke("getCollectionStatsHTML")

    async def gui_browse(self, query: str) -> list[int]:
        """Open Anki's browser with a query.

        Args:
            query: Search query to show in browser.

        Returns:
            List of card IDs shown.
        """
        return await self.client.invoke("guiBrowse", query=query)

    async def gui_current_card(self) -> CardInfo | None:
        """Get the current card being reviewed in Anki's GUI.

        Returns:
            Current card info or None if not reviewing.
        """
        result = await self.client.invoke("guiCurrentCard")
        if result:
            return CardInfo.model_validate(result)
        return None

    async def gui_show_question(self) -> bool:
        """Show the question side of the current card."""
        return await self.client.invoke("guiShowQuestion")

    async def gui_show_answer(self) -> bool:
        """Show the answer side of the current card."""
        return await self.client.invoke("guiShowAnswer")

    async def gui_answer_card(self, ease: CardEase) -> bool:
        """Answer the current card in Anki's GUI.

        Args:
            ease: The answer ease.

        Returns:
            True if successful.
        """
        return await self.client.invoke("guiAnswerCard", ease=ease.value)

    async def gui_start_review(self) -> bool:
        """Start a review session in Anki's GUI."""
        return await self.client.invoke("guiStartCardTimer")

    async def gui_deck_review(self, deck_name: str) -> bool:
        """Start reviewing a specific deck.

        Args:
            deck_name: The deck to review.

        Returns:
            True if successful.
        """
        return await self.client.invoke("guiDeckReview", name=deck_name)
